"""
Flow Design Node

第三步：基于已识别的Node列表，设计pocketflow的Flow架构。
专注于设计Node之间的连接、Action驱动的转换逻辑。
"""

import time
from typing import Dict, Any
from pocketflow import AsyncNode

# 导入OpenAI客户端
from utils.openai_client import get_openai_client
from agent.streaming import (
    emit_processing_status,
    emit_error
)

# 导入多语言提示词系统
from agent.prompts import get_prompt, PromptTypes
from agent.prompts.text_manager import get_text_manager
from agent.prompts.prompt_types import CommonPromptType
import asyncio


class FlowDesignNode(AsyncNode):
    """Flow设计节点 - 设计pocketflow的Flow架构"""
    
    def __init__(self):
        super().__init__()
        self.name = "FlowDesignNode"
        self.description = "设计pocketflow的Flow架构和Node连接逻辑"
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取已识别的Node列表"""
        try:
            # 获取markdown格式的设计结果
            analysis_markdown = shared.get("analysis_markdown", "")
            nodes_markdown = shared.get("nodes_markdown", "")

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
                "short_planning": short_planning,
                "user_requirements": user_requirements,
                "research_findings": research_findings,
                "recommended_tools": recommended_tools,
                "language": language,  # 添加语言设置
                "timestamp": time.time()
            }

        except Exception as e:
            return {"error": f"Flow design preparation failed: {str(e)}"}
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """异步执行阶段：设计Flow架构"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])
            
            # 构建Flow设计提示词
            prompt = self._build_flow_design_prompt(prep_result)

            # 异步调用LLM设计Flow，直接输出markdown
            flow_markdown = await self._design_flow_architecture(prompt, prep_result.get("language"))

            return {
                "flow_markdown": flow_markdown,
                "design_success": True
            }
            
        except Exception as e:
            return {"error": f"Flow design failed: {str(e)}"}
    
    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：保存Flow设计"""
        try:
            if "error" in exec_res:
                shared["flow_design_error"] = exec_res["error"]
                await emit_error(shared, f"❌ Flow设计失败: {exec_res['error']}")
                return "error"
            
            # 保存Flow设计markdown
            flow_markdown = exec_res["flow_markdown"]
            shared["flow_markdown"] = flow_markdown

            # 更新系统消息
            if "system_messages" not in shared:
                shared["system_messages"] = []

            shared["system_messages"].append({
                "timestamp": time.time(),
                "stage": "flow_design",
                "status": "completed",
                "message": "Flow设计完成"
            })

            # 使用流式事件发送设计文档
            from agent.streaming import emit_design_document
            await emit_design_document(shared, "03_flow_design.md", flow_markdown)

            await emit_processing_status(shared, "✅ Flow设计完成")

            return "flow_designed"

        except Exception as e:
            shared["flow_design_post_error"] = str(e)
            await emit_error(shared, f"❌ Flow设计后处理失败: {str(e)}")
            return "error"
    
    def _build_flow_design_prompt(self, prep_result: Dict[str, Any]) -> str:
        """构建Flow设计提示词，使用多语言模板系统"""
        analysis_markdown = prep_result.get("analysis_markdown", "")
        nodes_markdown = prep_result.get("nodes_markdown", "")
        short_planning = prep_result.get("short_planning", "")
        user_requirements = prep_result.get("user_requirements", "")
        research_findings = prep_result.get("research_findings", {})
        recommended_tools = prep_result.get("recommended_tools", [])
        language = prep_result.get("language")

        # 构建推荐工具信息
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

        # 使用文本管理器获取占位符文本
        text_manager = get_text_manager()
        no_requirements_text = text_manager.get_text(CommonPromptType.NO_REQUIREMENTS_PLACEHOLDER, language)
        no_planning_text = text_manager.get_text(CommonPromptType.NO_PLANNING_PLACEHOLDER, language)
        no_research_text = text_manager.get_text(CommonPromptType.NO_RESEARCH_PLACEHOLDER, language)
        no_tools_text = text_manager.get_text(CommonPromptType.NO_TOOLS_PLACEHOLDER, language)

        # 使用新的多语言模板系统获取提示词
        prompt = get_prompt(
            PromptTypes.Agent.FLOW_DESIGN,
            language=language,
            analysis_markdown=analysis_markdown,
            nodes_markdown=nodes_markdown,
            user_requirements=user_requirements if user_requirements else no_requirements_text,
            short_planning=short_planning if short_planning else no_planning_text,
            research_info=research_info if research_info else no_research_text,
            tools_info=tools_info if tools_info else no_tools_text
        )

        return prompt
    
    async def _design_flow_architecture(self, prompt: str, language: str = None) -> str:
        """调用LLM设计Flow架构，使用多语言模板系统"""
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
    

