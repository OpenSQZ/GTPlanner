"""
Short Planning Node

基于用户需求生成精炼的短规划文档，用于和用户确认项目核心范围与颗粒度。
"""

import time
import json
from typing import Dict, Any

# 导入LLM工具
from utils.openai_client import get_openai_client

# 导入多语言提示词系统
from agent.prompts import get_prompt, PromptTypes
from agent.prompts.text_manager import get_text, build_dynamic_content
from agent.prompts.prompt_types import CommonPromptType

from pocketflow import AsyncNode


class ShortPlanningNode(AsyncNode):
    """短规划节点 - 生成精炼的短规划文档"""

    def __init__(self):
        super().__init__()
        self.name = "ShortPlanningNode"
        self.description = "生成精炼的短规划文档，用于和用户确认项目核心范围与颗粒度"

    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取用户需求、历史规划和项目状态"""
        try:
            # 获取用户需求
            user_requirements = shared.get("user_requirements", "")

            # 获取上一版本的规划（优先从项目状态获取）
            previous_planning = ""
            if "short_planning" in shared:
                # 从之前的规划文档获取
                previous_planning_data = shared["short_planning"]
                if isinstance(previous_planning_data, dict):
                    previous_planning = previous_planning_data.get("content", "")
                elif isinstance(previous_planning_data, str):
                    previous_planning = previous_planning_data


            # 获取改进点（可选）
            improvement_points = shared.get("improvement_points", [])

            # 获取推荐工具信息（用于增强规划）
            recommended_tools = shared.get("recommended_tools", [])

            # 获取研究结果（如果有）
            research_findings = shared.get("research_findings", {})

            # 获取语言设置
            language = shared.get("language")

            # 如果没有明确的用户需求，但有推荐工具，可以基于工具进行规划
            if not user_requirements and recommended_tools:
                # 使用多语言文本片段
                from agent.prompts.text_manager import get_text_manager
                text_manager = get_text_manager()
                user_requirements = text_manager.get_text(
                    CommonPromptType.TOOL_BASED_PLANNING_PLACEHOLDER,
                    language
                )

            # 至少需要用户需求或改进点之一
            if not user_requirements and not improvement_points and not previous_planning:
                return {"error": "需要提供用户需求、改进点或已有规划之一"}

            return {
                "user_requirements": user_requirements,
                "previous_planning": previous_planning,
                "improvement_points": improvement_points,
                "recommended_tools": recommended_tools,
                "research_findings": research_findings,
                "language": language,  # 添加语言设置
                "generation_timestamp": time.time()
            }

        except Exception as e:
            return {"error": f"短规划准备阶段失败: {str(e)}"}

    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行短规划文档生成"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])

            user_requirements = prep_result["user_requirements"]
            previous_planning = prep_result["previous_planning"]
            improvement_points = prep_result["improvement_points"]
            recommended_tools = prep_result["recommended_tools"]
            research_findings = prep_result["research_findings"]
            language = prep_result["language"]  # 从prep_result获取语言设置

            # 使用异步LLM生成步骤化规划文档，包含推荐工具和研究结果
            short_planning = await self._generate_planning_document(
                user_requirements,
                previous_planning,
                improvement_points,
                recommended_tools,
                research_findings,
                language  # 传递语言设置
            )

            return {
                "short_planning": short_planning,
                "generation_success": True,
                "used_recommended_tools": len(recommended_tools) > 0,
                "used_research_findings": bool(research_findings)
            }

        except Exception as e:
            raise e

    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """保存短规划文档结果"""
        if "error" in exec_res:
            shared["planning_error"] = exec_res["error"]
            return "error"

        # 保存短规划文档到统一的字段名
        shared["short_planning"] = exec_res["short_planning"]

        return "planning_complete"

    async def _generate_planning_document(self, user_requirements: str,
                                        previous_planning: str = "",
                                        improvement_points: list = None,
                                        recommended_tools: list = None,
                                        research_findings: dict = None,
                                        language: str = None) -> str:
        """使用异步LLM生成步骤化的规划文档（纯文本），结合推荐工具和研究结果。"""

        # 构建LLM提示词，包含推荐工具和研究结果
        prompt = self._build_planning_prompt(
            user_requirements,
            previous_planning,
            improvement_points or [],
            recommended_tools or [],
            research_findings or {},
            language
        )

        # 调用异步LLM，不再要求JSON格式
        client = get_openai_client()
        response = await client.chat_completion(
            messages=[{"role": "user", "content": prompt}]
        )
        result_str = response.choices[0].message.content if response.choices else ""

        # 直接返回纯文本结果
        return result_str.strip()

    def _build_planning_prompt(self, user_requirements: str,
                             previous_planning: str = "",
                             improvement_points: list = None,
                             recommended_tools: list = None,
                             research_findings: dict = None,
                             language: str = None) -> str:
        """
        构建生成步骤化流程的LLM提示词，使用多语言模板系统。
        """
        # 使用新的文本管理器构建动态内容
        req_content = build_dynamic_content(
            user_requirements=user_requirements,
            previous_planning=previous_planning,
            improvement_points=improvement_points,
            language=language
        )

        # 使用文本管理器构建工具和研究内容
        from agent.prompts.text_manager import get_text_manager
        text_manager = get_text_manager()

        tools_content = text_manager.build_tools_content(
            recommended_tools=recommended_tools,
            language=language
        )

        research_content = text_manager.build_research_content(
            research_findings=research_findings,
            language=language
        )

        # 使用新的多语言模板系统获取提示词
        prompt = get_prompt(
            PromptTypes.Agent.SHORT_PLANNING_GENERATION,
            language=language,
            req_content=req_content,
            tools_content=tools_content,
            research_content=research_content
        )

        return prompt
