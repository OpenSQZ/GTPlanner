"""
Database Design Node - MySQL 数据库表结构设计节点

这是一个单节点架构，接受显式参数，生成 MySQL 数据库表结构设计文档。
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
    emit_database_design
)

# 导入多语言提示词系统
from gtplanner.agent.prompts import get_prompt, PromptTypes
from gtplanner.agent.prompts.text_manager import get_text_manager


class DatabaseDesignNode(AsyncNode):
    """数据库表结构设计节点 - 单节点架构，生成 MySQL 数据库设计文档"""
    
    def __init__(self):
        super().__init__()
        self.name = "DatabaseDesignNode"
        self.description = "生成 MySQL 数据库表结构设计文档"
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：收集所有输入数据"""
        try:
            # 发送开始事件
            await emit_processing_status(shared, "🗄️  准备生成数据库表结构设计...")
            
            # 必需参数：用户需求
            user_requirements = shared.get("user_requirements", "")
            if not user_requirements:
                return {"error": "user_requirements is required"}
            
            # ⭐ 重要参数：系统设计文档（必须在 design 之后调用）
            system_design = shared.get("system_design", "")
            if not system_design:
                print("⚠️ [DatabaseDesign] 警告: 未找到 system_design，数据库设计可能不够精确")
            
            # 可选参数：项目规划（如果之前调用了 short_planning）
            project_planning = shared.get("short_planning", "")
            
            # 可选参数：推荐预制件（如果之前调用了 prefab_recommend 或 search_prefabs）
            recommended_prefabs = shared.get("recommended_prefabs", [])
            
            # 获取语言设置
            language = shared.get("language")
            
            # 使用文本管理器格式化可选信息
            text_manager = get_text_manager()
            
            prefabs_info = text_manager.build_tools_content(
                recommended_prefabs=recommended_prefabs,
                language=language
            ) if recommended_prefabs else ""
            
            # 发送准备完成事件
            await emit_processing_status(shared, "🤖 正在调用 AI 生成数据库表结构设计...")
            
            return {
                "user_requirements": user_requirements,
                "system_design": system_design,
                "project_planning": project_planning,
                "prefabs_info": prefabs_info,
                "language": language,
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {"error": f"Database design preparation failed: {str(e)}"}
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行阶段：调用 LLM 生成数据库表结构设计"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])
            
            # 注意：exec 阶段不能访问 shared，所以这里无法发送事件
            # 进度事件应在 prep 和 post 阶段发送
            
            # 构建 prompt
            prompt = get_prompt(
                PromptTypes.Agent.DATABASE_DESIGN,
                language=prep_result.get("language"),
                user_requirements=prep_result["user_requirements"],
                system_design=prep_result.get("system_design", ""),
                project_planning=prep_result["project_planning"],
                prefabs_info=prep_result["prefabs_info"]
            )
            
            # 调用 LLM 生成数据库设计文档
            client = get_openai_client()
            response = await client.chat_completion(
                messages=[{"role": "user", "content": prompt}]
            )
            
            database_design = response.choices[0].message.content if response.choices else ""
            
            if not database_design or not database_design.strip():
                raise ValueError("LLM returned empty database design document")
            
            return {
                "database_design": database_design,
                "generation_success": True,
                "generation_time": time.time()
            }
            
        except Exception as e:
            return {"error": f"Database design generation failed: {str(e)}"}
    
    async def post_async(self, shared: Dict[str, Any], prep_result: Dict[str, Any], exec_result: Dict[str, Any]) -> str:
        """后处理阶段：保存数据库设计文档并发送事件"""
        try:
            if "error" in exec_result:
                error_msg = exec_result["error"]
                shared["database_design_error"] = error_msg
                await emit_error(shared, f"❌ 数据库设计文档生成失败: {error_msg}")
                print(f"❌ 数据库设计文档生成失败: {error_msg}")
                return "error"
            
            # 发送生成完成事件
            await emit_processing_status(shared, "📄 数据库设计文档生成完成，正在保存...")
            
            database_design = exec_result["database_design"]
            
            # 保存到 shared
            shared["database_design"] = database_design
            
            # 发送数据库设计文档事件到前端
            await emit_database_design(shared, "database_design.md", database_design)
            
            # 更新系统消息
            if "system_messages" not in shared:
                shared["system_messages"] = []
            
            shared["system_messages"].append({
                "timestamp": time.time(),
                "stage": "database_design",
                "status": "completed",
                "message": "数据库表结构设计完成"
            })
            
            # 发送最终完成事件
            await emit_processing_status(shared, "✅ 数据库设计文档已生成并保存")
            print("✅ 数据库表结构设计生成完成")
            
            return "default"
            
        except Exception as e:
            error_msg = str(e)
            shared["database_design_post_error"] = error_msg
            await emit_error(shared, f"❌ 数据库设计文档保存失败: {error_msg}")
            print(f"❌ 数据库设计文档保存失败: {error_msg}")
            return "error"

