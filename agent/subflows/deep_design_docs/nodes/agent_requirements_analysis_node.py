"""
Agent Requirements Analysis Node

第一步：分析需求，明确要设计的Agent类型和核心功能。
专注于理解用户需求，确定Agent的定位和主要职责。
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


class AgentRequirementsAnalysisNode(AsyncNode):
    """Agent需求分析节点 - 理解和分析Agent设计需求"""
    
    def __init__(self):
        super().__init__()
        self.name = "AgentRequirementsAnalysisNode"
        self.description = "分析Agent设计需求，明确Agent类型和核心功能"
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：收集需求信息"""
        try:
            # 获取用户需求（必需）
            user_requirements = shared.get("user_requirements", "")

            # 获取短期规划结果（必需）
            short_planning = shared.get("short_planning", "")

            # 获取研究结果（可选）
            research_findings = shared.get("research_findings", {})

            # 获取推荐工具（可选）
            recommended_tools = shared.get("recommended_tools", [])

            # 获取语言设置
            language = shared.get("language")

            # 检查必需的输入
            if not user_requirements:
                return {"error": "缺少用户需求，无法进行架构分析"}
            if not short_planning:
                return {"error": "缺少短期规划结果，无法进行架构分析"}

            return {
                "user_requirements": user_requirements,  # 添加用户需求
                "short_planning": short_planning,
                "research_findings": research_findings,
                "recommended_tools": recommended_tools,
                "language": language,  # 添加语言设置
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {"error": f"Agent requirements analysis preparation failed: {str(e)}"}
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """异步执行阶段：分析Agent需求"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])
            
            # 构建分析提示词
            prompt = self._build_analysis_prompt(prep_result)

            # 异步调用LLM分析需求，直接输出markdown
            analysis_markdown = await self._analyze_agent_requirements_async(prompt, prep_result.get("language"))

            return {
                "analysis_markdown": analysis_markdown,
                "analysis_success": True
            }
            
        except Exception as e:
            return {"error": f"Agent requirements analysis failed: {str(e)}"}
    
    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：保存分析结果"""
        try:
            if "error" in exec_res:
                shared["agent_analysis_error"] = exec_res["error"]
                print(f"❌ Agent需求分析失败: {exec_res['error']}")
                return "error"
            
            # 保存markdown内容
            analysis_markdown = exec_res["analysis_markdown"]
            shared["analysis_markdown"] = analysis_markdown

            # 更新系统消息
            if "system_messages" not in shared:
                shared["system_messages"] = []

            shared["system_messages"].append({
                "timestamp": time.time(),
                "stage": "agent_requirements_analysis",
                "status": "completed",
                "message": "Agent需求分析完成"
            })

            # 使用流式事件发送设计文档
            from agent.streaming import emit_design_document
            await emit_design_document(shared, "01_agent_analysis.md", analysis_markdown)

            await emit_processing_status(shared, "✅ Agent需求分析完成")

            return "analysis_complete"

        except Exception as e:
            shared["agent_analysis_post_error"] = str(e)
            await emit_error(shared, f"❌ Agent需求分析后处理失败: {str(e)}")
            return "error"
    
    def _build_analysis_prompt(self, prep_result: Dict[str, Any]) -> str:
        """构建需求分析提示词，使用多语言模板系统"""
        user_requirements = prep_result.get("user_requirements", "")
        short_planning = prep_result["short_planning"]
        research_findings = prep_result.get("research_findings", {})
        recommended_tools = prep_result.get("recommended_tools", [])
        language = prep_result.get("language")

        # 使用文本管理器构建工具和研究内容
        text_manager = get_text_manager()

        tools_info = text_manager.build_tools_content(
            recommended_tools=recommended_tools,
            language=language
        )

        research_summary = text_manager.build_research_content(
            research_findings=research_findings,
            language=language
        )

        # 使用新的多语言模板系统获取提示词
        prompt = get_prompt(
            PromptTypes.Agent.DEEP_REQUIREMENTS_ANALYSIS,
            language=language,
            user_requirements=user_requirements,
            short_planning=short_planning,
            tools_info=tools_info,
            research_summary=research_summary
        )

        return prompt
    
    async def _analyze_agent_requirements_async(self, prompt: str, language: str = None) -> str:
        """异步调用LLM分析Agent需求，使用多语言模板系统"""
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


