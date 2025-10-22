"""
Document Generation Node

第六步：整合所有设计结果，生成完整的Agent设计文档。
基于之前提示词的完整格式，生成高质量的pocketflow Agent设计文档。
"""

import time
import json
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


class DocumentGenerationNode(AsyncNode):
    """文档生成节点 - 生成完整的Agent设计文档"""
    
    def __init__(self):
        super().__init__()
        self.name = "DocumentGenerationNode"
        self.description = "整合所有设计结果生成完整的Agent设计文档"
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：收集所有设计结果"""
        try:
            # 获取所有前面步骤的markdown结果
            analysis_markdown = shared.get("analysis_markdown", "")
            nodes_markdown = shared.get("nodes_markdown", "")
            flow_markdown = shared.get("flow_markdown", "")
            data_structure_markdown = shared.get("data_structure_markdown", "")
            node_design_markdown = shared.get("node_design_markdown", "")

            # 获取项目状态信息
            short_planning = shared.get("short_planning", "")
            user_requirements = shared.get("user_requirements", "")
            research_findings = shared.get("research_findings", {})
            recommended_tools = shared.get("recommended_tools", [])

            # 获取语言设置
            language = shared.get("language")

            # 检查必需的输入
            required_data = {
                "analysis_markdown": analysis_markdown,
                "nodes_markdown": nodes_markdown
            }

            missing_data = [key for key, value in required_data.items() if not value]
            if missing_data:
                return {"error": f"缺少必需的设计数据: {missing_data}"}

            return {
                "analysis_markdown": analysis_markdown,
                "nodes_markdown": nodes_markdown,
                "flow_markdown": flow_markdown,
                "data_structure_markdown": data_structure_markdown,
                "node_design_markdown": node_design_markdown,
                "short_planning": short_planning,
                "user_requirements": user_requirements,
                "research_findings": research_findings,
                "recommended_tools": recommended_tools,
                "language": language,  # 添加语言设置
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {"error": f"Document generation preparation failed: {str(e)}"}
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """异步执行阶段：生成完整的Agent设计文档"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])
            
            # 构建文档生成提示词
            prompt = self._build_document_generation_prompt(prep_result)
            
            # 异步调用LLM生成文档
            agent_design_document = await self._generate_complete_document(prompt, prep_result.get("language"))
            
            return {
                "agent_design_document": agent_design_document,
                "generation_success": True,
                "generation_time": time.time()
            }
            
        except Exception as e:
            return {"error": f"Document generation failed: {str(e)}"}
    
    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：保存文档并生成文件"""
        try:
            if "error" in exec_res:
                shared["document_generation_error"] = exec_res["error"]
                await emit_error(shared, f"❌ 文档生成失败: {exec_res['error']}")
                return "error"
            
            # 保存生成的文档
            agent_design_document = exec_res["agent_design_document"]
            shared["agent_design_document"] = agent_design_document

            # 使用流式事件发送设计文档
            from agent.streaming import emit_design_document
            await emit_design_document(shared, "06_agent_design_complete.md", agent_design_document)
            
            # 更新系统消息
            if "system_messages" not in shared:
                shared["system_messages"] = []
            
            shared["system_messages"].append({
                "timestamp": time.time(),
                "stage": "document_generation",
                "status": "completed",
                "message": "完整Agent设计文档生成完成"
            })
            
            await emit_processing_status(shared, "✅ 完整Agent设计文档生成完成")
            return "documentation_complete"

        except Exception as e:
            shared["document_generation_post_error"] = str(e)
            await emit_error(shared, f"❌ 文档生成后处理失败: {str(e)}")
            return "error"
    
    def _build_document_generation_prompt(self, prep_result: Dict[str, Any]) -> str:
        """构建文档生成提示词，使用多语言模板系统"""
        analysis_markdown = prep_result.get("analysis_markdown", "")
        nodes_markdown = prep_result.get("nodes_markdown", "")
        flow_markdown = prep_result.get("flow_markdown", "")
        data_structure_markdown = prep_result.get("data_structure_markdown", "")
        node_design_markdown = prep_result.get("node_design_markdown", "")
        user_requirements = prep_result.get("user_requirements", "")
        language = prep_result.get("language")

        # 从用户需求中提取项目标题，如果没有则使用默认值
        text_manager = get_text_manager()
        default_project_title = text_manager.get_text(CommonPromptType.DEFAULT_PROJECT_TITLE, language)
        project_title = default_project_title
        if user_requirements and isinstance(user_requirements, str):
            # 简单提取：取第一行或前50个字符作为标题
            first_line = user_requirements.split('\n')[0].strip()
            if first_line:
                project_title = first_line[:50] + ("..." if len(first_line) > 50 else "")

        # 获取其他上下文信息
        short_planning = prep_result.get("short_planning", "")
        research_findings = prep_result.get("research_findings", {})
        recommended_tools = prep_result.get("recommended_tools", [])

        # 使用文本管理器构建推荐工具信息
        tools_info = text_manager.build_tools_content(
            recommended_tools=recommended_tools,
            language=language
        )

        # 使用文本管理器构建研究信息
        research_info = text_manager.build_research_content(
            research_findings=research_findings,
            language=language
        )

        # 使用文本管理器获取占位符文本
        no_requirements_text = text_manager.get_text(CommonPromptType.NO_REQUIREMENTS_PLACEHOLDER, language)
        no_planning_text = text_manager.get_text(CommonPromptType.NO_PLANNING_PLACEHOLDER, language)
        no_tools_text = text_manager.get_text(CommonPromptType.NO_TOOLS_PLACEHOLDER, language)

        # 使用多语言模板系统获取提示词
        prompt = get_prompt(
            PromptTypes.Agent.DOCUMENT_GENERATION,
            language=language,
            project_title=project_title,
            user_requirements=user_requirements if user_requirements else no_requirements_text,
            short_planning=short_planning if short_planning else no_planning_text,
            tools_info=tools_info if tools_info else no_tools_text,
            research_findings=research_info,
            analysis_markdown=analysis_markdown,
            nodes_markdown=nodes_markdown,
            flow_markdown=flow_markdown,
            data_structure_markdown=data_structure_markdown,
            node_design_markdown=node_design_markdown
        )
        
        return prompt
    
    async def _generate_complete_document(self, prompt: str, language: str = None) -> str:
        """调用LLM生成完整文档，使用多语言模板系统"""
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
    

