"""
Short Planning Node

基于用户需求生成精炼的短规划文档，用于和用户确认项目核心范围与颗粒度。
"""

import time
import json
from typing import Dict, Any

# 导入LLM工具
from gtplanner.utils.openai_client import get_openai_client

# 导入多语言提示词系统
from gtplanner.agent.prompts import get_prompt, PromptTypes
from gtplanner.agent.prompts.text_manager import get_text, build_dynamic_content
from gtplanner.agent.prompts.prompt_types import CommonPromptType

from pocketflow import AsyncNode
from gtplanner.agent.streaming import (
    emit_processing_status,
    emit_error
)


class ShortPlanningNode(AsyncNode):
    """短规划节点 - 生成精炼的短规划文档"""

    def __init__(self):
        super().__init__()
        self.name = "ShortPlanningNode"
        self.description = "生成精炼的短规划文档，用于和用户确认项目核心范围与颗粒度"

    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取用户需求、历史规划和项目状态"""
        try:
            # 发送处理状态
            await emit_processing_status(shared, "📝 开始生成项目实施规划...")
            
            # 获取用户需求
            user_requirements = shared.get("user_requirements", "")

            # 获取之前的规划（原子化，从参数显式传入）
            previous_planning = shared.get("previous_planning", "")

            # 获取改进点（可选）
            improvement_points = shared.get("improvement_points", [])

            # 获取推荐预制件信息（原子化，从参数显式传入）
            recommended_prefabs = shared.get("recommended_prefabs", "")

            # 获取研究结果（原子化，从参数显式传入）
            research_findings = shared.get("research_findings", "")

            # 获取语言设置
            language = shared.get("language")

            # 至少需要用户需求
            if not user_requirements:
                return {"error": "需要提供用户需求"}

            return {
                "user_requirements": user_requirements,
                "previous_planning": previous_planning,
                "improvement_points": improvement_points,
                "recommended_prefabs": recommended_prefabs,
                "research_findings": research_findings,
                "language": language,
                "generation_timestamp": time.time()
            }

        except Exception as e:
            await emit_error(shared, f"❌ 短规划准备阶段失败: {str(e)}")
            return {"error": f"短规划准备阶段失败: {str(e)}"}

    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行短规划文档生成"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])

            user_requirements = prep_result["user_requirements"]
            previous_planning = prep_result["previous_planning"]
            improvement_points = prep_result["improvement_points"]
            recommended_prefabs = prep_result["recommended_prefabs"]
            research_findings = prep_result["research_findings"]
            language = prep_result["language"]

            # 使用异步LLM生成步骤化规划文档，包含推荐预制件和研究结果
            short_planning = await self._generate_planning_document(
                user_requirements,
                previous_planning,
                improvement_points,
                recommended_prefabs,
                research_findings,
                language
            )

            return {
                "short_planning": short_planning,
                "generation_success": True,
                "used_recommended_prefabs": bool(recommended_prefabs),
                "used_research_findings": bool(research_findings)
            }

        except Exception as e:
            raise e

    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """保存短规划文档结果"""
        if "error" in exec_res:
            shared["planning_error"] = exec_res["error"]
            await emit_error(shared, f"❌ 规划生成失败: {exec_res['error']}")
            return "error"

        # 保存短规划文档到统一的字段名
        short_planning = exec_res["short_planning"]
        shared["short_planning"] = short_planning
        
        # 发送完成状态
        await emit_processing_status(shared, "✅ 项目实施规划已生成")

        return "planning_complete"

    async def _generate_planning_document(self, user_requirements: str,
                                        previous_planning: str = "",
                                        improvement_points: list = None,
                                        recommended_prefabs: str = "",
                                        research_findings: str = "",
                                        language: str = None) -> str:
        """使用异步LLM生成步骤化的规划文档（纯文本），结合推荐预制件和研究结果。"""

        # 构建LLM提示词，包含推荐预制件和研究结果
        prompt = self._build_planning_prompt(
            user_requirements,
            previous_planning,
            improvement_points or [],
            recommended_prefabs,
            research_findings,
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
                             recommended_prefabs: str = "",
                             research_findings: str = "",
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

        # 预制件和研究内容现在作为字符串直接传入（原子化）
        prefabs_content = recommended_prefabs if recommended_prefabs else "无推荐预制件"
        research_content = research_findings if research_findings else "无技术调研结果"

        # 使用新的多语言模板系统获取提示词
        prompt = get_prompt(
            PromptTypes.Agent.SHORT_PLANNING_GENERATION,
            language=language,
            req_content=req_content,
            prefabs_content=prefabs_content,
            research_content=research_content
        )

        return prompt
