"""
Quick Requirements Analysis Node

复制 nodes.py 中 AsyncRequirementsAnalysisNode 的完整实现，
移除多语言支持功能，保持相同的数据处理逻辑和提示词模板。
"""

from typing import Dict, Any
from pocketflow import AsyncNode
from utils.openai_client import get_openai_client

# 导入多语言提示词系统
from agent.prompts import get_prompt, PromptTypes
from agent.prompts.text_manager import get_text_manager
from agent.prompts.prompt_types import CommonPromptType


class QuickRequirementsAnalysisNode(AsyncNode):
    """快速需求分析节点 - 复制 AsyncRequirementsAnalysisNode 的逻辑"""

    def __init__(self):
        super().__init__()
        self.name = "QuickRequirementsAnalysisNode"
        self.description = "快速分析需求，复制原有逻辑但移除多语言支持"

    async def prep_async(self, shared):
        """准备数据进行需求分析"""
        # 提取用户需求（与上游字段名保持一致）
        user_requirements = shared.get("user_requirements", "")

        # 提取项目规划
        short_planning = shared.get("short_planning", "")

        # 获取语言设置
        language = shared.get("language")

        # 使用文本管理器格式化推荐工具信息
        text_manager = get_text_manager()
        tools_info = text_manager.build_tools_content(
            recommended_tools=shared.get("recommended_tools", []),
            language=language
        )

        # 使用文本管理器格式化技术调研结果
        research_summary = text_manager.build_research_content(
            research_findings=shared.get("research_findings", {}),
            language=language
        )

        return {
            "user_requirements": user_requirements,
            "short_planning": short_planning,
            "tools_info": tools_info,
            "research_summary": research_summary,
            "language": language,
        }

    async def exec_async(self, input_data):
        """使用LLM分析需求"""
        # 使用多语言模板系统构建需求分析提示词
        prompt = get_prompt(
            PromptTypes.Agent.QUICK_REQUIREMENTS_ANALYSIS,
            language=input_data.get("language"),
            user_requirements=input_data["user_requirements"],
            short_planning=input_data["short_planning"],
            tools_info=input_data["tools_info"],
            research_summary=input_data["research_summary"]
        )

        # 调用LLM分析需求
        client = get_openai_client()
        response = await client.chat_completion(
            messages=[{"role": "user", "content": prompt}]
        )
        llm_response = response.choices[0].message.content if response.choices else ""

        return llm_response

    async def post_async(self, shared, prep_res, exec_res):
        """将分析的需求存储到共享存储中并生成文件"""
        try:
            # exec_res 是字符串类型的LLM响应，不是字典
            if not exec_res or not exec_res.strip():
                shared["quick_requirements_analysis_error"] = "需求分析结果为空"
                print(f"❌ 快速需求分析失败: 需求分析结果为空")
                return "error"

            # 保存需求分析结果
            requirements = exec_res
            shared["requirements"] = requirements
            # 存储语言为中文（默认）
            shared["language"] = "zh"

            # 使用流式事件发送设计文档
            from agent.streaming import emit_design_document
            await emit_design_document(shared, "quick_requirements_analysis.md", requirements)

            # 更新系统消息
            if "system_messages" not in shared:
                shared["system_messages"] = []

            shared["system_messages"].append({
                "timestamp": __import__('time').time(),
                "stage": "quick_requirements_analysis",
                "status": "completed",
                "message": "快速需求分析完成"
            })

            print("✅ 快速需求分析完成")
            return "default"

        except Exception as e:
            shared["quick_requirements_analysis_post_error"] = str(e)
            print(f"❌ 快速需求分析后处理失败: {str(e)}")
            return "error"


