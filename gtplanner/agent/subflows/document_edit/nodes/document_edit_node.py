"""
Document Edit Node

文档编辑节点（智能 subagent 模式），负责：
1. 从 shared 中获取要编辑的文档内容
2. 使用 LLM 理解自然语言的修改需求
3. LLM 自动生成精确的 search/replace 操作
4. 验证编辑操作的有效性
5. 生成编辑提案并通过 SSE 发送给前端
"""

import uuid
import json
from typing import Dict, Any
from pocketflow import AsyncNode
from gtplanner.agent.streaming import emit_document_edit_proposal, emit_processing_status, emit_error
from gtplanner.utils.openai_client import get_openai_client
from gtplanner.agent.prompts import get_prompt, PromptTypes


class DocumentEditNode(AsyncNode):
    """文档编辑节点（智能 subagent）"""
    
    def __init__(self):
        super().__init__()
        self.name = "DocumentEditNode"
        self.description = "智能分析文档并生成编辑提案"
        self.openai_client = get_openai_client()
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备执行环境"""
        await emit_processing_status(shared, "📝 开始分析文档...")
        
        # 验证必需参数
        document_type = shared.get("document_type")
        edit_instructions = shared.get("edit_instructions")
        
        if not document_type:
            return {"error": "Missing required parameter: document_type"}
        
        if not edit_instructions:
            return {"error": "Missing required parameter: edit_instructions"}
        
        # 从 shared 中获取文档内容
        document_content = None
        document_filename = None
        
        # 尝试从 generated_documents 中获取最新的文档（按 timestamp 排序）
        generated_documents = shared.get("generated_documents", [])
        
        # 筛选出匹配类型的文档，并按 timestamp 降序排序（最新的在前）
        matching_docs = [
            doc for doc in generated_documents 
            if doc.get("type") == document_type
        ]
        
        if matching_docs:
            # 按 timestamp 降序排序，获取最新的文档
            matching_docs.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
            latest_doc = matching_docs[0]
            document_content = latest_doc.get("content")
            document_filename = latest_doc.get("filename")
        
        if not document_content:
            return {
                "error": f"No {document_type} document found in current session. Please generate a document first."
            }
        
        return {
            "success": True,
            "document_type": document_type,
            "document_content": document_content,
            "document_filename": document_filename,
            "edit_instructions": edit_instructions,
            "streaming_session": shared.get("streaming_session"),
            "language": shared.get("language", "zh")
        }
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行文档编辑提案生成 - 使用 LLM 生成 search/replace 操作"""
        if "error" in prep_result:
            return prep_result
        
        document_content = prep_result["document_content"]
        edit_instructions = prep_result["edit_instructions"]
        response_content = ""  # 初始化，供错误处理使用
        
        await emit_processing_status(
            {"streaming_session": prep_result.get("streaming_session")},
            "🤖 使用 AI 分析修改需求并生成编辑操作..."
        )
        
        try:
            # 获取语言配置
            language = prep_result.get("language", "zh")
            
            # 使用提示词模板系统构建 prompt
            prompt_template = get_prompt(
                PromptTypes.Agent.DOCUMENT_EDIT,
                language=language
            )
            
            # 填充模板
            prompt = prompt_template.format(
                document_content=document_content,
                edit_instructions=edit_instructions
            )
            
            # 调用 LLM
            response = await self.openai_client.chat_completion(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # 低温度以获得更精确的输出
            )
            
            # 解析 LLM 响应
            response_content = response.choices[0].message.content
            
            # 清理响应内容（处理可能的 markdown 代码块包裹）
            cleaned_content = response_content.strip()
            if cleaned_content.startswith("```json"):
                cleaned_content = cleaned_content[7:]
            elif cleaned_content.startswith("```"):
                cleaned_content = cleaned_content[3:]
            if cleaned_content.endswith("```"):
                cleaned_content = cleaned_content[:-3]
            cleaned_content = cleaned_content.strip()
            
            # 解析 JSON
            result = json.loads(cleaned_content)
            
            # 记录成功解析
            print(f"✅ LLM 响应解析成功: {json.dumps(result, ensure_ascii=False, indent=2)[:300]}...")
            
            edits = result.get("edits", [])
            summary = result.get("summary", "文档修改")
            
            if not edits:
                await emit_error(
                    {"streaming_session": prep_result.get("streaming_session")},
                    "❌ LLM 未生成任何编辑操作"
                )
                return {
                    "success": False,
                    "error": "LLM did not generate any edits"
                }
            
            await emit_processing_status(
                {"streaming_session": prep_result.get("streaming_session")},
                f"✅ 已生成 {len(edits)} 个编辑操作，正在验证..."
            )
            
            # 验证每个编辑操作的 search 字符串是否能精确匹配
            validation_errors = []
            for i, edit in enumerate(edits):
                search_text = edit.get("search", "")
                if search_text not in document_content:
                    validation_errors.append(
                        f"Edit #{i+1}: Cannot find search text in document. "
                        f"Search text: '{search_text[:50]}...'"
                    )
            
            if validation_errors:
                return {
                    "success": False,
                    "error": "Edit validation failed",
                    "validation_errors": validation_errors
                }
            
            # 生成预览内容（应用所有编辑）
            preview_content = document_content
            for edit in edits:
                search_text = edit.get("search", "")
                replace_text = edit.get("replace", "")
                # 只替换第一次出现的地方（保证精确性）
                preview_content = preview_content.replace(search_text, replace_text, 1)
            
            # 生成提案ID
            proposal_id = f"edit_{uuid.uuid4().hex[:8]}"
            
            return {
                "success": True,
                "proposal_id": proposal_id,
                "document_type": prep_result["document_type"],
                "document_filename": prep_result["document_filename"],
                "edits": edits,
                "summary": summary,
                "preview_content": preview_content
            }
            
        except json.JSONDecodeError as e:
            # 记录详细的解析错误信息，方便调试
            error_msg = f"Failed to parse LLM response as JSON: {str(e)}"
            await emit_error(
                {"streaming_session": prep_result.get("streaming_session")},
                f"❌ {error_msg}\n\n原始响应（前500字符）:\n{response_content[:500]}"
            )
            return {
                "success": False,
                "error": error_msg,
                "raw_response": response_content[:500]  # 保存原始响应供调试
            }
        except Exception as e:
            error_msg = f"LLM call failed: {str(e)}"
            await emit_error(
                {"streaming_session": prep_result.get("streaming_session")},
                f"❌ {error_msg}"
            )
            return {
                "success": False,
                "error": error_msg
            }
    
    async def post_async(
        self,
        shared: Dict[str, Any],
        prep_result: Dict[str, Any],
        exec_result: Dict[str, Any]
    ) -> str:
        """后处理：发送编辑提案到前端"""
        print(f"🚀 [DocumentEditNode.post_async] 开始执行")
        print(f"🔍 [DocumentEditNode.post_async] exec_result.success: {exec_result.get('success')}")
        print(f"🔍 [DocumentEditNode.post_async] streaming_session 存在: {shared.get('streaming_session') is not None}")
        
        if not exec_result.get("success"):
            error_msg = exec_result.get("error", "Unknown error")
            validation_errors = exec_result.get("validation_errors", [])
            
            error_details = error_msg
            if validation_errors:
                error_details += "\n\nValidation errors:\n" + "\n".join(validation_errors)
            
            await emit_error(shared, error_details)
            shared["document_edit_error"] = error_details
            return "edit_failed"
        
        # 发送编辑提案到前端
        proposal_id = exec_result["proposal_id"]
        document_type = exec_result["document_type"]
        document_filename = exec_result["document_filename"]
        edits = exec_result["edits"]
        summary = exec_result["summary"]
        preview_content = exec_result.get("preview_content")
        
        await emit_document_edit_proposal(
            shared,
            proposal_id=proposal_id,
            document_type=document_type,
            document_filename=document_filename,
            edits=edits,
            summary=summary,
            preview_content=preview_content
        )
        
        await emit_processing_status(
            shared,
            f"✅ 文档编辑提案已生成（ID: {proposal_id}），等待用户确认"
        )
        
        # 保存提案信息到 shared（用于后续的 tool_execution_results_updates）
        if "pending_document_edits" not in shared:
            shared["pending_document_edits"] = {}
        
        shared["pending_document_edits"][proposal_id] = {
            "document_type": document_type,
            "document_filename": document_filename,
            "edits": edits,
            "summary": summary,
            "status": "pending",
            "created_at": uuid.uuid4().hex  # 使用简单的时间戳替代
        }
        
        # 保存提案ID供工具返回使用
        shared["edit_proposal_id"] = proposal_id
        
        return "edit_proposal_generated"
