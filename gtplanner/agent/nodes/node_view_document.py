"""
查看文档节点 (NodeViewDocument)

查看当前会话中已生成的文档内容。
每次调用都会返回最新的文档内容（包括用户确认的编辑）。

功能描述：
- 从 tool_execution_results.designs.generated_documents 读取文档
- 支持按 filename 查看文档（如：design.md, prefabs_info.md, database_design.md）
- 返回最新的文档内容
"""

from typing import Dict, Any
from pocketflow import AsyncNode
from gtplanner.agent.streaming import (
    emit_processing_status,
    emit_error
)


class NodeViewDocument(AsyncNode):
    """查看文档节点"""
    
    def __init__(self, max_retries: int = 2, wait: float = 0.5):
        """
        初始化查看文档节点
        
        Args:
            max_retries: 最大重试次数
            wait: 重试等待时间
        """
        super().__init__(max_retries=max_retries, wait=wait)
        self.name = "NodeViewDocument"
    
    async def prep_async(self, shared) -> Dict[str, Any]:
        """
        准备阶段：验证参数并获取文档文件名

        Args:
            shared: pocketflow 字典共享变量

        Returns:
            准备结果字典
        """
        try:
            # 获取文档文件名
            filename = shared.get("filename")

            if not filename:
                error_msg = "filename is required"
                await emit_error(
                    shared=shared,
                    error_message=error_msg,
                    error_details={"error_code": "MISSING_PARAMETER"}
                )
                return {
                    "success": False,
                    "error": error_msg
                }

            # 发送处理状态
            await emit_processing_status(
                shared=shared,
                message=f"正在查看文档 {filename}..."
            )

            # 将 generated_documents 传递给 exec_async
            return {
                "success": True,
                "filename": filename,
                "generated_documents": shared.get("generated_documents", [])
            }

        except Exception as e:
            error_msg = f"Preparation failed: {str(e)}"
            await emit_error(
                shared=shared,
                error_message=error_msg,
                error_details={"error_code": "PREP_ERROR"}
            )
            return {
                "success": False,
                "error": error_msg
            }
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行阶段：从 generated_documents 中按 filename 获取文档内容

        Args:
            prep_result: 准备阶段的结果（包含 filename 和 generated_documents）

        Returns:
            执行结果字典
        """
        try:
            # 检查准备阶段是否成功
            if not prep_result.get("success"):
                return prep_result

            filename = prep_result["filename"]

            # 从 prep_result 中获取已生成的文档（在 prep 阶段传递过来）
            generated_documents = prep_result.get("generated_documents", [])

            if not generated_documents:
                return {
                    "success": False,
                    "error": "没有找到已生成的文档，请先使用 design 或 database_design 工具生成文档"
                }

            # 按 filename 查找文档
            target_document = None
            for doc in generated_documents:
                if doc.get("filename") == filename:
                    target_document = doc
                    break

            if not target_document:
                # 构建可用文档列表
                available_docs = [doc.get("filename") for doc in generated_documents if doc.get("filename")]
                return {
                    "success": False,
                    "error": f"没有找到文档 '{filename}'",
                    "available_documents": available_docs
                }

            # 返回文档内容
            return {
                "success": True,
                "document_type": target_document.get("type"),
                "filename": target_document.get("filename"),
                "content": target_document.get("content", ""),
                "content_length": len(target_document.get("content", ""))
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Execution failed: {str(e)}"
            }
    
    async def post_async(self, shared, prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        后处理阶段：发送完成状态
        
        Args:
            shared: pocketflow 字典共享变量
            prep_res: 准备阶段的结果
            exec_res: 执行阶段的结果
            
        Returns:
            最终结果字典
        """
        try:
            if exec_res.get("success"):
                # 发送成功状态
                await emit_processing_status(
                    shared=shared,
                    message=f"✅ 已获取 {exec_res.get('filename')} 的最新内容"
                )
            else:
                # 发送错误状态
                await emit_error(
                    shared=shared,
                    error_message=exec_res.get("error", "Unknown error"),
                    error_details={"error_code": "VIEW_DOCUMENT_ERROR"}
                )
            
            return exec_res
            
        except Exception as e:
            error_msg = f"Post-processing failed: {str(e)}"
            await emit_error(
                shared=shared,
                error_message=error_msg,
                error_details={"error_code": "POST_ERROR"}
            )
            return {
                "success": False,
                "error": error_msg
            }

