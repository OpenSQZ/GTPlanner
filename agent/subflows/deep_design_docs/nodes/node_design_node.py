"""
Node Design Node

第五步：基于数据结构设计，详细设计每个Node的prep/exec/post三阶段逻辑。
专注于每个Node的具体实现细节和职责分离。
"""

import time
import json
import asyncio
from typing import Dict, Any
from pocketflow import AsyncNode

# 导入LLM调用工具
from utils.openai_client import get_openai_client
from agent.streaming import (
    emit_processing_status,
    emit_error
)

# 导入多语言提示词系统
from agent.prompts import get_prompt, PromptTypes
from agent.prompts.text_manager import get_text_manager
from agent.prompts.prompt_types import CommonPromptType


class NodeDesignNode(AsyncNode):
    """Node设计节点 - 详细设计每个Node的实现"""
    
    def __init__(self):
        super().__init__()
        self.name = "NodeDesignNode"
        self.description = "详细设计每个Node的prep/exec/post三阶段实现"
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取Flow设计结果"""
        try:
            # 获取markdown格式的设计结果
            analysis_markdown = shared.get("analysis_markdown", "")
            nodes_markdown = shared.get("nodes_markdown", "")
            flow_markdown = shared.get("flow_markdown", "")
            data_structure_json = shared.get("data_structure_json", "")

            # 获取项目状态信息
            short_planning = shared.get("short_planning", "")
            user_requirements = shared.get("user_requirements", "")
            research_findings = shared.get("research_findings", {})
            recommended_tools = shared.get("recommended_tools", [])

            # 获取语言设置
            language = shared.get("language")

            # 检查必需的输入
            if not analysis_markdown:
                return {"error": "缺少Agent分析结果"}

            if not nodes_markdown:
                return {"error": "缺少Node识别结果"}

            return {
                "analysis_markdown": analysis_markdown,
                "nodes_markdown": nodes_markdown,
                "flow_markdown": flow_markdown,
                "data_structure_json": data_structure_json,
                "short_planning": short_planning,
                "user_requirements": user_requirements,
                "research_findings": research_findings,
                "recommended_tools": recommended_tools,
                "language": language,  # 添加语言设置
                "streaming_session": shared.get("streaming_session"),
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {"error": f"Node design preparation failed: {str(e)}"}
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """异步执行阶段：设计每个Node的详细实现"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])
            
            # 构建上下文数据
            context_data = {
                "analysis_markdown": prep_result.get("analysis_markdown", ""),
                "nodes_markdown": prep_result.get("nodes_markdown", ""),
                "flow_markdown": prep_result.get("flow_markdown", ""),
                "data_structure_json": prep_result.get("data_structure_json", "")
            }


            # 发送处理状态事件
            streaming_session = prep_result.get("streaming_session")
            if streaming_session:
                from agent.streaming import emit_processing_status_from_prep
                await emit_processing_status_from_prep(prep_result, "🔧 设计Node")

            # 构建Node设计提示词
            prompt = self._build_node_design_prompt(context_data)

            # 异步调用LLM设计Node，直接输出markdown
            node_design_markdown = await self._design_single_node(prompt, context_data.get("language"))

            return {
                "node_design_markdown": node_design_markdown,
                "design_success": True
            }
            
        except Exception as e:
            return {"error": f"Node design failed: {str(e)}"}
    
    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：保存Node设计"""
        try:
            if "error" in exec_res:
                shared["node_design_error"] = exec_res["error"]
                await emit_error(shared, f"❌ Node设计失败: {exec_res['error']}")
                return "error"
            
            # 保存Node设计markdown
            node_design_markdown = exec_res["node_design_markdown"]
            shared["node_design_markdown"] = node_design_markdown

            # 更新系统消息
            if "system_messages" not in shared:
                shared["system_messages"] = []

            shared["system_messages"].append({
                "timestamp": time.time(),
                "stage": "node_design",
                "status": "completed",
                "message": "Node设计完成"
            })

            # 使用流式事件发送设计文档
            from agent.streaming import emit_design_document
            await emit_design_document(shared, "05_node_design.md", node_design_markdown)

            await emit_processing_status(shared, "✅ Node设计完成")

            return "nodes_designed"

        except Exception as e:
            shared["node_design_post_error"] = str(e)
            await emit_error(shared, f"❌ Node设计后处理失败: {str(e)}")
            return "error"
    
    def _build_node_design_prompt(self, context_data: Dict[str, Any], node_info: Dict[str, Any] = None) -> str:
        """构建Node设计提示词，使用多语言模板系统"""

        # 构建推荐工具信息
        recommended_tools = context_data.get("recommended_tools", [])
        tools_info = ""
        if recommended_tools:
            tools_list = []
            for tool in recommended_tools:
                # 添加 None 检查，防止 tool 为 None
                if tool and isinstance(tool, dict):
                    tool_name = tool.get("name", tool.get("id", "未知工具"))
                    tool_type = tool.get("type", "")
                    tool_summary = tool.get("summary", tool.get("description", ""))
                    tools_list.append(f"- {tool_name} ({tool_type}): {tool_summary}")
            tools_info = "\n".join(tools_list)

        # 构建技术调研信息
        research_findings = context_data.get("research_findings", {})
        research_info = ""
        if research_findings and isinstance(research_findings, dict):
            # 使用正确的字段名
            if research_findings.get("summary"):
                research_info += f"**调研摘要：**\n{research_findings['summary']}\n\n"

            # 从关键词结果中提取关键信息
            keyword_results = research_findings.get("keyword_results", [])
            if keyword_results:
                successful_results = [r for r in keyword_results if r.get("success", False)]
                if successful_results:
                    research_info += "**关键发现：**\n"
                    for result in successful_results[:3]:  # 只显示前3个结果
                        keyword = result.get("keyword", "")
                        result_data = result.get("result", {})
                        if result_data and result_data.get("summary"):
                            research_info += f"- {keyword}: {result_data['summary'][:100]}...\n"
                    research_info += "\n"

        # 如果提供了特定的node_info，使用它；否则使用通用的nodes_markdown
        node_info_text = ""
        if node_info:
            node_info_text = f"**当前设计的Node：**\n{node_info}\n\n"

        # 获取语言设置
        language = context_data.get("language")

        # 使用文本管理器获取占位符文本
        text_manager = get_text_manager()
        no_requirements_text = text_manager.get_text(CommonPromptType.NO_REQUIREMENTS_PLACEHOLDER, language)
        no_planning_text = text_manager.get_text(CommonPromptType.NO_PLANNING_PLACEHOLDER, language)
        no_research_text = text_manager.get_text(CommonPromptType.NO_RESEARCH_PLACEHOLDER, language)
        no_tools_text = text_manager.get_text(CommonPromptType.NO_TOOLS_PLACEHOLDER, language)

        # 使用新的多语言模板系统获取提示词
        prompt = get_prompt(
            PromptTypes.Agent.NODE_DESIGN,
            language=language,
            node_info_text=node_info_text,
            nodes_markdown=context_data.get("nodes_markdown"),
            analysis_markdown=context_data.get("analysis_markdown", ""),
            flow_markdown=context_data.get("flow_markdown", ""),
            data_structure_json=context_data.get("data_structure_json", ""),
            user_requirements=context_data.get("user_requirements", no_requirements_text),
            short_planning=context_data.get("short_planning", no_planning_text),
            research_info=research_info if research_info else no_research_text,
            tools_info=tools_info if tools_info else no_tools_text
        )

        return prompt
    
    async def _design_single_node(self, prompt: str, language: str = None) -> str:
        """调用LLM设计单个Node，使用多语言模板系统"""
        try:
            # 直接使用已经包含完整提示词的prompt
            client = get_openai_client()
            response = await client.chat_completion(
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.choices[0].message.content if response.choices else ""
            return result
        except Exception as e:
            raise Exception(f"LLM调用失败: {str(e)}")

    async def _design_single_node_detailed(self, prep_result: Dict[str, Any], node_info: Dict[str, Any]) -> Dict[str, Any]:
        """为单个Node执行详细设计（供批处理聚合器调用）"""
        try:
            # 构建设计提示词
            prompt = self._build_node_design_prompt(prep_result, node_info)

            # 调用LLM设计
            design_result = await self._design_single_node(prompt, prep_result.get("language"))

            # 解析设计结果
            parsed_result = self._parse_node_design(design_result, node_info)

            return parsed_result

        except Exception as e:
            # 简化错误处理，移除详细的 print 语句
            raise Exception(f"单个Node设计失败: {str(e)}")

    def _parse_node_design(self, node_design: str, original_node_info: Dict[str, Any]) -> Dict[str, Any]:
        """解析Node设计结果"""
        try:
            # 尝试解析JSON
            if isinstance(node_design, str):
                parsed_data = json.loads(node_design)
            else:
                parsed_data = node_design

            # 处理LLM可能返回列表的情况
            if isinstance(parsed_data, list):
                if len(parsed_data) == 0:
                    raise Exception("LLM返回空列表")
                # 取第一个元素
                parsed_node = parsed_data[0]
            elif isinstance(parsed_data, dict):
                parsed_node = parsed_data
            else:
                raise Exception(f"LLM返回了不支持的数据类型: {type(parsed_data)}")

            # 验证必需字段
            if not isinstance(parsed_node, dict):
                raise Exception(f"解析后的Node数据不是字典类型: {type(parsed_node)}")

            if "node_name" not in parsed_node:
                parsed_node["node_name"] = original_node_info.get("node_name", "UnknownNode")
            
            if "node_type" not in parsed_node:
                parsed_node["node_type"] = original_node_info.get("node_type", "Node")
            
            if "design_details" not in parsed_node:
                raise Exception("缺少design_details字段")
            
            # 验证design_details结构
            design_details = parsed_node["design_details"]
            if not isinstance(design_details, dict):
                raise Exception(f"design_details不是字典类型: {type(design_details)}")

            required_stages = ["prep_stage", "exec_stage", "post_stage"]

            for stage in required_stages:
                if stage not in design_details:
                    # 简化日志，移除 print 语句
                    design_details[stage] = {
                        "description": f"默认{stage}描述",
                        "steps": []
                    }
            
            return parsed_node
            
        except json.JSONDecodeError as e:
            raise Exception(f"Node设计JSON解析失败: {e}")
        except Exception as e:
            raise Exception(f"Node设计解析失败: {e}")
