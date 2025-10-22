"""
工具推荐节点 (Node_Tool_Recommend)

基于查询文本从向量数据库检索最相关的工具，并返回推荐列表。
基于架构文档中定义的输入输出规格实现。

功能描述：
- 接收用户查询文本
- 调用向量服务进行相似度检索
- 返回最相关的工具列表
- 支持结果过滤和排序
- 可选的大模型重排序
"""

import time
import requests
import asyncio
import json
from typing import Dict, List, Any, Optional
from pocketflow import AsyncNode
from utils.openai_client import OpenAIClient
from utils.config_manager import get_vector_service_config
from agent.streaming import (
    emit_processing_status,
    emit_error
)

# 导入多语言提示词系统
from agent.prompts import get_prompt, PromptTypes


class NodeToolRecommend(AsyncNode):
    """工具推荐节点"""
    
    def __init__(self, max_retries: int = 3, wait: float = 2.0):
        """
        初始化工具推荐节点

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

        # 从配置文件读取索引相关参数
        self.index_name = vector_config.get("tools_index_name", "tools_index")
        self.vector_field = vector_config.get("vector_field", "combined_text")

        # 推荐配置
        self.default_top_k = 5
        self.min_score_threshold = 0.1  # 最小相似度阈值
        self.use_llm_filter = True  # 是否使用大模型筛选
        self.llm_candidate_count = 10  # 传给大模型的候选工具数量

        # 初始化OpenAI客户端
        self.openai_client = OpenAIClient()

        # 检查向量服务可用性
        try:
            response = requests.get(f"{self.vector_service_url}/health", timeout=5)
            self.vector_service_available = response.status_code == 200
        except Exception:
            self.vector_service_available = False
            print("⚠️ 向量服务不可用")

    async def prep_async(self, shared) -> Dict[str, Any]:
        """
        准备阶段：从共享变量获取查询参数

        Args:
            shared: pocketflow字典共享变量

        Returns:
            准备结果字典
        """
        try:
            # 从共享变量获取查询参数
            query = shared.get("query", "")
            top_k = shared.get("top_k", self.default_top_k)
            index_name = shared.get("index_name", self.index_name)
            tool_types = shared.get("tool_types", [])  # 可选的工具类型过滤
            min_score = shared.get("min_score", self.min_score_threshold)
            use_llm_filter = shared.get("use_llm_filter", self.use_llm_filter)  # 是否使用大模型筛选
            language = shared.get("language")  # 获取语言设置

            # 如果没有提供查询，尝试从其他字段提取
            if not query:
                query = self._extract_query_from_shared_state(shared)

            # 验证输入
            if not query or not query.strip():
                return {
                    "error": "No query provided for tool recommendation",
                    "query": "",
                    "top_k": top_k,
                    "index_name": index_name
                }

            # 预处理查询文本
            processed_query = self._preprocess_query(query.strip())

            return {
                "query": processed_query,
                "original_query": query,
                "top_k": top_k,
                "index_name": index_name,
                "tool_types": tool_types,
                "min_score": min_score,
                "use_llm_filter": use_llm_filter,
                "language": language,  # 添加语言设置
                "streaming_session": shared.get("streaming_session")
            }

        except Exception as e:
            return {
                "error": f"Tool recommendation preparation failed: {str(e)}",
                "query": "",
                "top_k": self.default_top_k,
                "index_name": self.index_name
            }

    async def exec_async(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行阶段：调用向量服务进行工具检索

        Args:
            prep_res: 准备阶段的结果

        Returns:
            执行结果字典
        """
        if "error" in prep_res:
            raise ValueError(prep_res["error"])

        query = prep_res["query"]
        top_k = prep_res["top_k"]
        index_name = prep_res["index_name"]
        tool_types = prep_res["tool_types"]
        min_score = prep_res["min_score"]
        use_llm_filter = prep_res["use_llm_filter"]
        language = prep_res["language"]

        if not query:
            raise ValueError("Empty query for tool recommendation")

        if not self.vector_service_available:
            raise RuntimeError("Vector service is not available")

        try:
            start_time = time.time()

            # 调用向量服务进行检索（获取更多候选）
            search_top_k = max(top_k, self.llm_candidate_count) if use_llm_filter else top_k
            # 从 prep_res 中获取 streaming_session 用于事件发送
            shared_for_events = {"streaming_session": prep_res.get("streaming_session")}
            search_results = await self._search_tools(query, index_name, search_top_k, shared_for_events)

            # 过滤和处理结果
            filtered_results = self._filter_results(
                search_results,
                tool_types=tool_types,
                min_score=min_score
            )

            # 后处理结果
            processed_results = self._process_results(filtered_results)

            # 使用大模型筛选（如果启用）
            if use_llm_filter and len(processed_results) > 1:
                try:
                    llm_selected_results = await self._llm_filter_tools(query, processed_results, top_k, language, shared_for_events)
                    processed_results = llm_selected_results
                    await emit_processing_status(shared_for_events, f"✅ 大模型筛选完成，返回 {len(processed_results)} 个工具")
                except Exception as e:
                    await emit_error(shared_for_events, f"⚠️ 大模型筛选失败，使用原始排序: {str(e)}")
                    processed_results = processed_results[:top_k]
            else:
                processed_results = processed_results[:top_k]

            search_time = time.time() - start_time

            return {
                "recommended_tools": processed_results,
                "total_found": len(processed_results),
                "search_time": round(search_time * 1000),  # 转换为毫秒
                "query_used": query,
                "original_query": prep_res["original_query"],
                "search_metadata": {
                    "index_name": index_name,
                    "top_k": top_k,
                    "min_score": min_score,
                    "tool_types_filter": tool_types
                }
            }

        except Exception as e:
            raise RuntimeError(f"Tool recommendation execution failed: {str(e)}")

    async def post_async(self, shared, prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """
        后处理阶段：将推荐结果存储到共享状态

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
                    shared.record_error(Exception(exec_res["error"]), "NodeToolRecommend.exec")
                return "error"

            recommended_tools = exec_res["recommended_tools"]
            total_found = exec_res["total_found"]

            # 检查是否是子流程的共享变量（字典类型）
            if isinstance(shared, dict):
                # 子流程模式：保存推荐结果到共享变量
                shared["recommended_tools"] = recommended_tools
                shared["tool_recommendation_result"] = {
                    "tools": recommended_tools,
                    "total_found": total_found,
                    "query": exec_res["query_used"],
                    "search_time": exec_res["search_time"]
                }
                return "success"

            # 主流程模式：保存到研究发现或相应的状态
            if not hasattr(shared, 'tool_recommendations'):
                shared.tool_recommendations = []

            # 转换推荐结果为标准格式
            for tool in recommended_tools:
                recommendation = {
                    "tool_id": tool["id"],
                    "tool_type": tool["type"],
                    "tool_name": tool.get("summary", ""),
                    "description": tool.get("description", ""),
                    "relevance_score": tool.get("score", 0.0),
                    "examples": tool.get("examples", ""),
                    "metadata": {
                        "category": tool.get("category", ""),
                        "file_path": tool.get("file_path", ""),
                        "requirement": tool.get("requirement", ""),
                        "base_url": tool.get("base_url", ""),
                        "endpoints": tool.get("endpoints", "")
                    },
                    "search_metadata": {
                        "query": exec_res["query_used"],
                        "search_time": exec_res["search_time"]
                    }
                }
                shared.tool_recommendations.append(recommendation)

            # 添加系统消息记录推荐结果
            shared.add_system_message(
                f"工具推荐完成，找到 {total_found} 个相关工具",
                agent_source="NodeToolRecommend",
                query=exec_res["query_used"],
                tools_count=total_found,
                search_time_ms=exec_res["search_time"]
            )

            return "success"

        except Exception as e:
            if hasattr(shared, 'record_error'):
                shared.record_error(e, "NodeToolRecommend.post")
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
            "error": f"Tool recommendation execution failed: {str(exc)}",
            "recommended_tools": [],
            "total_found": 0,
            "query_used": prep_res.get("query", ""),
            "original_query": prep_res.get("original_query", "")
        }

    def _extract_query_from_shared_state(self, shared) -> str:
        """从共享状态中提取查询文本"""
        query_candidates = []

        # 检查是否是子流程的共享变量（字典类型）
        if isinstance(shared, dict):
            # 子流程模式：直接从字典中获取
            if "user_query" in shared:
                query_candidates.append(shared["user_query"])
            if "search_query" in shared:
                query_candidates.append(shared["search_query"])
            if "task_description" in shared:
                query_candidates.append(shared["task_description"])
        else:
            # 主流程模式：从共享状态对象中提取
            if hasattr(shared, 'user_intent') and hasattr(shared.user_intent, 'original_query'):
                query_candidates.append(shared.user_intent.original_query)

            # 支持新的字段名
            if hasattr(shared, 'user_requirements') and shared.user_requirements:
                query_candidates.append(shared.user_requirements)
            if hasattr(shared, 'short_planning') and shared.short_planning:
                query_candidates.append(shared.short_planning)

        # 返回第一个非空的查询
        for candidate in query_candidates:
            if candidate and candidate.strip():
                return candidate.strip()

        return ""

    def _preprocess_query(self, query: str) -> str:
        """预处理查询文本"""
        # 基础清理
        processed = query.strip()

        # 可以添加更多预处理逻辑，如：
        # - 关键词提取
        # - 同义词扩展
        # - 停用词过滤

        return processed

    async def _search_tools(self, query: str, index_name: str, top_k: int, shared: Dict[str, Any]) -> Dict[str, Any]:
        """调用向量服务进行工具检索"""
        try:
            # 构建搜索请求
            search_request = {
                "query": query,
                "vector_field": self.vector_field,
                "index": index_name,
                "top_k": top_k
            }

            # 调用向量服务
            response = requests.post(
                f"{self.vector_service_url}/search",
                json=search_request,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                result = response.json()
                await emit_processing_status(shared, f"✅ 检索到 {result.get('total', 0)} 个相关工具")
                return result
            else:
                error_msg = f"向量服务返回错误: {response.status_code}, {response.text}"
                await emit_error(shared, f"❌ {error_msg}")
                raise RuntimeError(error_msg)

        except requests.exceptions.RequestException as e:
            error_msg = f"调用向量服务失败: {str(e)}"
            print(f"❌ {error_msg}")
            raise RuntimeError(error_msg)

    def _filter_results(self, search_results: Dict[str, Any],
                       tool_types: List[str] = None,
                       min_score: float = 0.0) -> List[Dict[str, Any]]:
        """过滤搜索结果"""
        if "results" not in search_results:
            return []

        filtered = []
        for result in search_results["results"]:
            # 检查相似度阈值
            score = result.get("score", 0.0)
            if score < min_score:
                continue

            # 检查工具类型过滤
            document = result.get("document", {})
            if tool_types and document.get("type") not in tool_types:
                continue

            # 添加分数到文档中
            document["score"] = score
            filtered.append(document)

        return filtered

    def _process_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """后处理搜索结果"""
        processed = []

        for result in results:
            # 确保必要字段存在
            processed_result = {
                "id": result.get("id", ""),
                "type": result.get("type", ""),
                "summary": result.get("summary", ""),
                "description": result.get("description", ""),
                "examples": result.get("examples", ""),
                "score": result.get("score", 0.0),
                "category": result.get("category", ""),
                "file_path": result.get("file_path", ""),
                "created_at": result.get("created_at", ""),
                "updated_at": result.get("updated_at", "")
            }

            # 添加类型特定字段
            if result.get("type") == "PYTHON_PACKAGE":
                processed_result["requirement"] = result.get("requirement", "")
            elif result.get("type") == "APIS":
                processed_result["base_url"] = result.get("base_url", "")
                processed_result["endpoints"] = result.get("endpoints", "")

            processed.append(processed_result)

        # 按相似度分数排序
        processed.sort(key=lambda x: x["score"], reverse=True)

        return processed



    async def _llm_filter_tools(self, query: str, tools: List[Dict[str, Any]], top_k: int, language: str, shared: Dict[str, Any]) -> List[Dict[str, Any]]:
        """使用大模型筛选最合适的工具"""
        if not tools:
            return []

        # 构建提示词
        prompt = self._build_filter_prompt(query, tools, top_k, language)

        try:
            # 调用大模型
            messages = [{"role": "user", "content": prompt}]
            response = await self.openai_client.chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=2000
            )

            # 解析JSON响应
            response_content = response.choices[0].message.content
            try:
                # 清理响应内容，移除可能的markdown代码块标记
                cleaned_content = response_content.strip()
                if cleaned_content.startswith("```json"):
                    cleaned_content = cleaned_content[7:]  # 移除 ```json
                if cleaned_content.startswith("```"):
                    cleaned_content = cleaned_content[3:]   # 移除 ```
                if cleaned_content.endswith("```"):
                    cleaned_content = cleaned_content[:-3]  # 移除结尾的 ```
                cleaned_content = cleaned_content.strip()

                response_json = json.loads(cleaned_content)
            except json.JSONDecodeError as e:
                await emit_error(shared, f"❌ 大模型返回的不是有效JSON: {response_content[:500]}... 错误: {str(e)}")
                return []  # JSON解析失败时返回空列表

            # 解析大模型响应
            selected_tools = await self._parse_llm_filter_response(response_json, tools, shared)

            return selected_tools

        except Exception as e:
            await emit_error(shared, f"❌ 大模型调用失败: {str(e)}")
            return []  # 大模型调用失败时返回空列表

    def _build_filter_prompt(self, query: str, tools: List[Dict[str, Any]], top_k: int, language: str) -> str:
        """构建大模型筛选的提示词，使用多语言模板系统"""
        # 构建工具信息列表
        tools_info = []
        for i, tool in enumerate(tools):
            tool_info = {
                "index": i,
                "id": tool["id"],
                "type": tool["type"],
                "summary": tool["summary"],
                "description": tool["description"][:500] + "..." if len(tool["description"]) > 500 else tool["description"]
            }
            tools_info.append(tool_info)

        # 使用新的多语言模板系统获取提示词
        prompt = get_prompt(
            PromptTypes.Agent.TOOL_RECOMMENDATION,
            language=language,
            query=query,
            tools_info=json.dumps(tools_info, ensure_ascii=False, indent=2),
            top_k=top_k,
            tools_count=len(tools)-1
        )

        return prompt

    async def _parse_llm_filter_response(self, response: Dict[str, Any], original_tools: List[Dict[str, Any]], shared: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析大模型筛选响应"""
        try:
            if "selected_tools" not in response:
                await emit_error(shared, "⚠️ 大模型响应格式错误：缺少selected_tools字段")
                return []  # 格式错误时也返回空列表，避免推荐不相关工具

            selected_tools = response["selected_tools"]
            if not isinstance(selected_tools, list):
                await emit_error(shared, "⚠️ 大模型响应格式错误：selected_tools不是列表")
                return []  # 格式错误时也返回空列表，避免推荐不相关工具

            # 如果大模型没有选择任何工具，尊重LLM的判断，返回空列表
            if not selected_tools:
                await emit_processing_status(shared, "✅ 大模型分析后认为没有合适的工具")
                return []  # 返回空列表，尊重LLM的专业判断

            filtered_tools = []
            used_indices = set()

            for item in selected_tools:
                if not isinstance(item, dict) or "index" not in item:
                    continue

                index = item["index"]
                if not isinstance(index, int) or index < 0 or index >= len(original_tools):
                    continue

                if index in used_indices:
                    continue

                used_indices.add(index)
                tool = original_tools[index].copy()
                tool["llm_reason"] = item.get("reason", "")
                tool["llm_selected"] = True  # 标记为大模型选中
                filtered_tools.append(tool)

            # 注意：这里不补充未选中的工具，只返回大模型筛选出的工具
            await emit_processing_status(shared, f"✅ 大模型筛选解析成功，筛选出 {len(filtered_tools)} 个工具")
            if "analysis" in response:
                await emit_processing_status(shared, f"📝 大模型分析: {response['analysis']}")

            return filtered_tools

        except Exception as e:
            await emit_error(shared, f"❌ 解析大模型响应失败: {str(e)}")
            return []  # 解析失败时返回空列表，避免推荐不相关工具
        
if __name__ == '__main__':
    from node_tool_index import NodeToolIndex
    init_node = NodeToolIndex()
    recommend_node = NodeToolRecommend()
    shared_with_init = {
        "tools_dir":"/home/tang/pyprojects/OpenSQZ-GTPlanner/GTPlanner/tools",
        "index_name":"",
        "force_reindex":True
    }
    prep_init_result = init_node.prep(shared_with_init)
    exec_init_result = init_node.exec(prep_init_result)
    # print(exec_init_result)  # 注释掉测试代码中的 print
    time.sleep(1) #现在需要休眠1秒，等待索引刷新。之后会修复这个问题
    shared_with_llm = {
        "query": "我想解析视频字幕",
        "top_k": 10,
        "index_name": exec_init_result.get("index_name", recommend_node.index_name),  # 使用配置的索引名称
        "use_llm_filter": True
    }
    prep_result = recommend_node.prep(shared=shared_with_llm)
    exec_result = recommend_node.exec(prep_result)
    # print("---------")  # 注释掉测试代码中的 print
    # print(exec_result)   # 注释掉测试代码中的 print

