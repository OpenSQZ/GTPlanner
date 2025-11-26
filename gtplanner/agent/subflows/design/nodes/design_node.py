"""
Design Node - 统一的设计文档生成节点

这是一个单节点架构，接受显式参数，生成高层次的系统设计文档。
不依赖 shared 中的其他工具输出，所有信息通过参数显式传入。
"""

import time
from typing import Dict, Any
from pocketflow import AsyncNode

# 导入 OpenAI 客户端
from gtplanner.utils.openai_client import get_openai_client
from gtplanner.agent.streaming import (
    emit_processing_status,
    emit_error,
    emit_design_document
)

# 导入多语言提示词系统
from gtplanner.agent.prompts import get_prompt, PromptTypes
from gtplanner.agent.prompts.text_manager import get_text_manager


class DesignNode(AsyncNode):
    """设计文档生成节点 - 单节点架构，生成完整的设计文档"""

    def __init__(self):
        super().__init__()
        self.name = "DesignNode"
        self.description = "生成高层次的系统设计文档（design.md）"

    def _build_prefabs_info(self, recommended_prefabs: list, language: str = None) -> str:
        """
        构建预制件信息文本（包含函数列表）

        Args:
            recommended_prefabs: 推荐预制件列表
            language: 语言设置

        Returns:
            格式化的预制件信息文本
        """
        if not recommended_prefabs:
            return ""

        prefabs_lines = []
        for prefab in recommended_prefabs:
            # 基本信息
            prefab_name = prefab.get("name", prefab.get("id", "Unknown"))
            prefab_type = prefab.get("type", "")
            prefab_desc = prefab.get("summary", prefab.get("description", ""))

            # 格式化基本信息
            if prefab_type:
                prefabs_lines.append(f"- {prefab_name} ({prefab_type}): {prefab_desc}")
            else:
                prefabs_lines.append(f"- {prefab_name}: {prefab_desc}")

            # 🔑 添加函数列表
            functions = prefab.get("functions", [])
            if functions:
                # 添加函数列表标题
                func_title = "  提供的函数:" if language == "zh" else "  Provided Functions:"
                prefabs_lines.append(func_title)

                # 添加每个函数
                for func in functions:
                    func_name = func.get("name", "unknown")
                    func_desc = func.get("description", "")
                    if func_desc:
                        prefabs_lines.append(f"    - {func_name}: {func_desc}")
                    else:
                        prefabs_lines.append(f"    - {func_name}")

        return "\n".join(prefabs_lines)

    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：收集所有输入数据"""
        try:
            # 发送开始事件
            await emit_processing_status(shared, "📝 准备生成设计文档...")
            
            # 必需参数：用户需求
            user_requirements = shared.get("user_requirements", "")
            if not user_requirements:
                return {"error": "user_requirements is required"}
            
            # 可选参数：项目规划（如果之前调用了 short_planning）
            project_planning = shared.get("short_planning", "")
            
            # 可选参数：推荐预制件（如果之前调用了 prefab_recommend 或 search_prefabs）
            recommended_prefabs = shared.get("recommended_prefabs", [])
            
            # 可选参数：技术调研结果（如果之前调用了 research）
            research_findings = shared.get("research_findings", {})
            
            # 获取语言设置
            language = shared.get("language")

            # 使用本地方法构建预制件信息（包含函数列表）
            prefabs_info = self._build_prefabs_info(recommended_prefabs, language) if recommended_prefabs else ""

            # 使用文本管理器格式化研究结果
            text_manager = get_text_manager()
            research_summary = text_manager.build_research_content(
                research_findings=research_findings,
                language=language
            ) if research_findings else ""
            
            # 发送准备完成事件
            await emit_processing_status(shared, "🤖 正在调用 AI 生成设计文档...")
            
            return {
                "user_requirements": user_requirements,
                "project_planning": project_planning,
                "prefabs_info": prefabs_info,
                "research_summary": research_summary,
                "language": language,
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {"error": f"Design preparation failed: {str(e)}"}
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行阶段：调用 LLM 生成设计文档"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])
            
            # 注意：exec 阶段不能访问 shared，所以这里无法发送事件
            # 进度事件应在 prep 和 post 阶段发送
            
            # 构建 prompt
            prompt = get_prompt(
                PromptTypes.Agent.DESIGN,
                language=prep_result.get("language"),
                user_requirements=prep_result["user_requirements"],
                project_planning=prep_result["project_planning"],
                prefabs_info=prep_result["prefabs_info"],
                research_summary=prep_result["research_summary"]
            )
            
            # 调用 LLM 生成设计文档
            client = get_openai_client()
            response = await client.chat_completion(
                messages=[{"role": "user", "content": prompt}]
            )
            
            design_document = response.choices[0].message.content if response.choices else ""
            
            if not design_document or not design_document.strip():
                raise ValueError("LLM returned empty design document")
            
            return {
                "design_document": design_document,
                "generation_success": True,
                "generation_time": time.time()
            }
            
        except Exception as e:
            return {"error": f"Design generation failed: {str(e)}"}
    
    async def post_async(self, shared: Dict[str, Any], prep_result: Dict[str, Any], exec_result: Dict[str, Any]) -> str:
        """后处理阶段：保存设计文档并发送事件"""
        try:
            if "error" in exec_result:
                error_msg = exec_result["error"]
                shared["design_error"] = error_msg
                await emit_error(shared, f"❌ 设计文档生成失败: {error_msg}")
                print(f"❌ 设计文档生成失败: {error_msg}")
                return "error"
            
            # 发送生成完成事件
            await emit_processing_status(shared, "📄 设计文档生成完成，正在保存...")
            
            design_document = exec_result["design_document"]
            
            # 保存到 shared（与旧版本兼容）
            shared["agent_design_document"] = design_document
            shared["documentation"] = design_document
            
            # ⭐ 重要：保存为 system_design，供后续 database_design 节点使用
            shared["system_design"] = design_document
            
            # 发送设计文档事件到前端
            await emit_design_document(shared, "design.md", design_document)

            # 更新系统消息
            if "system_messages" not in shared:
                shared["system_messages"] = []
            
            shared["system_messages"].append({
                "timestamp": time.time(),
                "stage": "design",
                "status": "completed",
                "message": "设计文档生成完成"
            })
            
            # 发送最终完成事件
            await emit_processing_status(shared, "✅ 设计文档已生成并保存")
            print("✅ 设计文档生成完成")
            
            return "default"
            
        except Exception as e:
            error_msg = str(e)
            shared["design_post_error"] = error_msg
            await emit_error(shared, f"❌ 设计文档保存失败: {error_msg}")
            print(f"❌ 设计文档保存失败: {error_msg}")
            return "error"

