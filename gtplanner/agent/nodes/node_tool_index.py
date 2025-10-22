"""
工具索引节点 (Node_Tool_Index)

负责扫描工具描述文件并建立向量索引，支持不同类型的工具。
基于架构文档中定义的输入输出规格实现。

功能描述：
- 扫描tools目录下的所有工具描述文件
- 解析YAML格式的工具描述
- 构建统一的文档结构
- 调用向量服务进行批量索引
- 支持多种工具类型的扩展
"""

import os
import glob
import yaml
import requests
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pocketflow import AsyncNode
from utils.config_manager import get_vector_service_config
from agent.streaming import (
    emit_processing_status,
    emit_error
)


class NodeToolIndex(AsyncNode):
    """工具索引节点"""
    
    def __init__(self, max_retries: int = 3, wait: float = 2.0):
        """
        初始化工具索引节点

        Args:
            max_retries: 最大重试次数
            wait: 重试等待时间
        """
        super().__init__(max_retries=max_retries, wait=wait)

        # 从配置文件加载向量服务配置
        vector_config = get_vector_service_config()
        self.vector_service_url = vector_config.get("base_url")
        self.timeout = vector_config.get("timeout", 30)

        # 检查向量服务URL是否配置
        if not self.vector_service_url:
            raise ValueError("向量服务URL未配置，请设置VECTOR_SERVICE_BASE_URL环境变量")

        # 从配置文件读取索引相关参数（保留你同事的改进）
        self.index_name = vector_config.get("tools_index_name", "tools_index")
        self.vector_field = vector_config.get("vector_field", "combined_text")
        
        # 工具目录配置
        self.tools_dir = "tools"
        self.supported_types = ["PYTHON_PACKAGE", "APIS"]
        
        # 检查向量服务可用性
        try:
            response = requests.get(f"{self.vector_service_url}/health", timeout=5)
            self.vector_service_available = response.status_code == 200
        except Exception:
            self.vector_service_available = False
            # 注意：初始化阶段无法发送流式事件
    
    async def prep_async(self, shared) -> Dict[str, Any]:
        """
        准备阶段：扫描和解析工具描述文件

        Args:
            shared: pocketflow字典共享变量

        Returns:
            准备结果字典
        """
        try:
            # 从共享变量获取配置
            tools_dir = shared.get("tools_dir", self.tools_dir)
            index_name = shared.get("index_name", self.index_name)
            force_reindex = shared.get("force_reindex", False)
            
            # 扫描工具文件
            tool_files = await self._scan_tool_files(tools_dir, shared)

            if not tool_files:
                return {
                    "error": f"No tool files found in {tools_dir}",
                    "tool_files": [],
                    "tools_count": 0
                }

            # 解析工具文件
            parsed_tools = []
            failed_files = []

            for file_path in tool_files:
                try:
                    tool_data = await self._parse_tool_file(file_path, shared)
                    if tool_data:
                        parsed_tools.append(tool_data)
                except Exception as e:
                    failed_files.append({"file": file_path, "error": str(e)})
                    # 错误已在 _parse_tool_file 中发送事件
            
            if not parsed_tools:
                return {
                    "error": "No valid tool files parsed",
                    "tool_files": tool_files,
                    "parsed_tools": [],
                    "failed_files": failed_files,
                    "tools_count": 0
                }
            
            return {
                "tool_files": tool_files,
                "parsed_tools": parsed_tools,
                "failed_files": failed_files,
                "tools_count": len(parsed_tools),
                "index_name": index_name,
                "force_reindex": force_reindex,
                "streaming_session": shared.get("streaming_session")
            }
            
        except Exception as e:
            return {
                "error": f"Tool indexing preparation failed: {str(e)}",
                "tool_files": [],
                "parsed_tools": [],
                "tools_count": 0
            }
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行阶段：调用向量服务进行工具索引

        Args:
            prep_res: 准备阶段的结果

        Returns:
            执行结果字典
        """
        if "error" in prep_res:
            raise ValueError(prep_res["error"])

        parsed_tools = prep_res["parsed_tools"]
        index_name = prep_res["index_name"]
        force_reindex = prep_res.get("force_reindex", False)

        if not parsed_tools:
            raise ValueError("No tools to index")

        if not self.vector_service_available:
            raise RuntimeError("Vector service is not available")

        try:
            start_time = time.time()

            # 每次启动都清除现有索引数据，确保使用最新的工具信息
            shared_for_events = {"streaming_session": prep_res.get("streaming_session")}
            await self._clear_index(index_name, shared_for_events)

            # 构建文档列表
            documents = []
            for tool in parsed_tools:
                doc = self._build_document(tool)
                documents.append(doc)

            # 调用向量服务进行批量索引，使用固定的索引名
            index_result = await self._index_documents(documents, index_name, shared_for_events)

            index_time = time.time() - start_time

            return {
                "indexed_count": index_result.get("count", len(documents)),
                "index_name": index_result.get("index", index_name),  # 返回实际使用的索引名
                "index_time": round(index_time * 1000),  # 转换为毫秒
                "documents": documents,
                "failed_tools": prep_res.get("failed_files", []),
                "total_processed": prep_res["tools_count"],
                "force_reindex": force_reindex
            }

        except Exception as e:
            raise RuntimeError(f"Tool indexing execution failed: {str(e)}")
    
    async def post_async(self, shared, prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """
        后处理阶段：更新共享状态

        Args:
            shared: 共享状态对象
            prep_res: 准备阶段结果
            exec_res: 执行阶段结果

        Returns:
            下一步动作
        """
        try:
            if "error" in exec_res:
                if hasattr(shared, 'record_error'):
                    shared.record_error(Exception(exec_res["error"]), "NodeToolIndex.exec")
                return "error"

            indexed_count = exec_res["indexed_count"]
            index_name = exec_res["index_name"]

            # 检查是否是子流程的共享变量（字典类型）
            if isinstance(shared, dict):
                # 子流程模式：保存索引结果到共享变量
                shared["tool_index_result"] = {
                    "indexed_count": indexed_count,
                    "index_name": index_name,
                    "index_time": exec_res["index_time"],
                    "total_processed": exec_res["total_processed"]
                }
                return "success"

            # 主流程模式：更新系统状态
            if not hasattr(shared, 'system_status'):
                shared.system_status = {}
            
            shared.system_status.update({
                "tool_index_name": index_name,
                "tool_index_count": indexed_count,
                "last_index_time": datetime.now().isoformat(),
                "index_duration_ms": exec_res["index_time"]
            })

            # 添加系统消息记录索引结果
            shared.add_system_message(
                f"工具索引完成，成功索引 {indexed_count} 个工具到 {index_name}",
                agent_source="NodeToolIndex",
                indexed_count=indexed_count,
                total_processed=exec_res["total_processed"],
                index_time_ms=exec_res["index_time"]
            )

            return "success"

        except Exception as e:
            if hasattr(shared, 'record_error'):
                shared.record_error(e, "NodeToolIndex.post")
            return "error"
    
    def exec_fallback(self, prep_res: Dict[str, Any], exc: Exception) -> Dict[str, Any]:
        """
        执行失败时的降级处理
        
        Args:
            prep_res: 准备阶段结果
            exc: 异常对象
            
        Returns:
            错误信息
        """
        return {
            "error": f"Tool indexing execution failed: {str(exc)}",
            "indexed_count": 0,
            "total_processed": prep_res.get("tools_count", 0)
        }
    
    async def _scan_tool_files(self, tools_dir: str, shared: Dict[str, Any]) -> List[str]:
        """扫描工具描述文件"""
        if not os.path.exists(tools_dir):
            # 发送错误事件
            await emit_error(shared, f"⚠️ 工具目录不存在: {tools_dir}")
            return []

        # 扫描所有子目录下的yml文件
        pattern = os.path.join(tools_dir, "**", "*.yml")
        tool_files = glob.glob(pattern, recursive=True)

        # 发送发现文件的状态事件
        await emit_processing_status(shared, f"📁 发现 {len(tool_files)} 个工具描述文件")
        return tool_files
    
    async def _parse_tool_file(self, file_path: str, shared: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """解析单个工具描述文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data or not isinstance(data, dict):
                return None
            
            # 验证必需字段
            required_fields = ['id', 'type', 'summary']
            for field in required_fields:
                if field not in data:
                    # 发送警告事件
                    await emit_error(shared, f"⚠️ 工具文件缺少必需字段 {field}: {file_path}")
                    return None
            
            # 添加文件路径信息
            data['file_path'] = file_path
            data['file_name'] = os.path.basename(file_path)
            
            return data
            
        except Exception as e:
            # 发送错误事件
            await emit_error(shared, f"❌ 解析工具文件失败: {file_path}, 错误: {e}")
            return None

    def _build_document(self, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """构建用于索引的文档结构"""
        # 基础字段
        doc = {
            "id": tool_data["id"],
            "type": tool_data["type"],
            "summary": tool_data.get("summary", ""),
            "description": tool_data.get("description", ""),
            "file_path": tool_data.get("file_path", ""),
            "file_name": tool_data.get("file_name", ""),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        # 处理示例
        examples_text = ""
        if "examples" in tool_data and isinstance(tool_data["examples"], list):
            examples_list = []
            for example in tool_data["examples"]:
                if isinstance(example, dict):
                    title = example.get("title", "")
                    content = example.get("content", "")
                    examples_list.append(f"{title}: {content}")
                else:
                    examples_list.append(str(example))
            examples_text = "\n".join(examples_list)

        doc["examples"] = examples_text

        # 处理不同类型工具的特殊字段
        if tool_data["type"] == "PYTHON_PACKAGE":
            doc["requirement"] = tool_data.get("requirement", "")
            doc["category"] = "python_package"
        elif tool_data["type"] == "APIS":
            doc["base_url"] = tool_data.get("base_url", "")
            doc["category"] = "api"

            # 处理endpoints
            endpoints_text = ""
            if "endpoints" in tool_data and isinstance(tool_data["endpoints"], list):
                endpoints_list = []
                for endpoint in tool_data["endpoints"]:
                    if isinstance(endpoint, dict):
                        method = endpoint.get("method", "")
                        path = endpoint.get("path", "")
                        summary = endpoint.get("summary", "")
                        endpoints_list.append(f"{method} {path}: {summary}")
                endpoints_text = "\n".join(endpoints_list)

            doc["endpoints"] = endpoints_text
        else:
            doc["category"] = "other"

        # 构建用于向量检索的组合文本
        combined_parts = [
            doc["summary"],
            doc["description"],
            examples_text
        ]

        # 添加类型特定的文本
        if tool_data["type"] == "PYTHON_PACKAGE":
            combined_parts.append(doc.get("requirement", ""))
        elif tool_data["type"] == "APIS":
            combined_parts.append(doc.get("endpoints", ""))

        # 过滤空字符串并组合
        combined_text = " ".join([part.strip() for part in combined_parts if part.strip()])
        doc[self.vector_field] = combined_text

        return doc

    async def _clear_index(self, index_name: str, shared: Dict[str, Any]) -> None:
        """清除指定索引的所有数据"""
        try:
            await emit_processing_status(shared, f"🗑️ 清除索引数据: {index_name}")

            # 调用向量服务清除索引
            response = requests.delete(
                f"{self.vector_service_url}/index/{index_name}/clear",
                timeout=self.timeout,
                headers={"accept": "application/json"}
            )

            if response.status_code == 200:
                await emit_processing_status(shared, f"✅ 成功清除索引 {index_name} 的数据")
            else:
                # 如果索引不存在，通常返回404，这是正常的
                if response.status_code == 404:
                    await emit_processing_status(shared, f"ℹ️ 索引 {index_name} 不存在或已为空")
                else:
                    error_msg = f"清除索引失败: {response.status_code}, {response.text}"
                    await emit_error(shared, f"⚠️ {error_msg}")
                    # 不抛出异常，因为清除失败不应该阻止后续的索引操作

        except requests.exceptions.RequestException as e:
            error_msg = f"调用清除索引API失败: {str(e)}"
            await emit_error(shared, f"⚠️ {error_msg}")
            # 不抛出异常，因为清除失败不应该阻止后续的索引操作

    async def _index_documents(self, documents: List[Dict[str, Any]], index_name: str, shared: Dict[str, Any]) -> Dict[str, Any]:
        """调用向量服务进行文档索引"""
        try:
            # 先尝试使用指定的索引名
            request_data = {
                "documents": documents,
                "vector_field": self.vector_field,
                "index": index_name
            }

            await emit_processing_status(shared, f"📝 尝试使用索引 {index_name} 进行索引...")

            response = requests.post(
                f"{self.vector_service_url}/documents",
                json=request_data,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                result = response.json()
                await emit_processing_status(shared, f"✅ 成功索引 {result.get('count', 0)} 个工具到索引 {index_name}")
                result["index"] = index_name
                return result
            elif response.status_code == 404 and "不存在" in response.text:
                # 索引不存在，让服务自动创建一个新索引
                await emit_processing_status(shared, f"📝 索引 {index_name} 不存在，让服务自动创建新索引...")

                # 不指定索引名，让服务自动创建
                auto_request_data = {
                    "documents": documents,
                    "vector_field": self.vector_field
                    # 不指定 index
                }

                response = requests.post(
                    f"{self.vector_service_url}/documents",
                    json=auto_request_data,
                    timeout=self.timeout,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    result = response.json()
                    actual_index_name = result.get("index")
                    await emit_processing_status(shared, f"✅ 成功创建新索引 {actual_index_name}，索引了 {result.get('count', 0)} 个工具")

                    # 返回实际创建的索引名，这将成为新的固定索引名
                    return result
                else:
                    error_msg = f"自动创建索引失败: {response.status_code}, {response.text}"
                    await emit_error(shared, f"❌ {error_msg}")
                    raise RuntimeError(error_msg)
            else:
                error_msg = f"向量服务返回错误: {response.status_code}, {response.text}"
                await emit_error(shared, f"❌ {error_msg}")
                raise RuntimeError(error_msg)

        except requests.exceptions.RequestException as e:
            error_msg = f"调用向量服务失败: {str(e)}"
            await emit_error(shared, f"❌ {error_msg}")
            raise RuntimeError(error_msg)
