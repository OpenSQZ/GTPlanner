"""
Document Edit Flow

文档编辑流程，单节点流程，调用 DocumentEditNode 生成编辑提案。
"""

from pocketflow import AsyncFlow
from pocketflow_tracing import trace_flow
from ..nodes.document_edit_node import DocumentEditNode
from gtplanner.agent.streaming import emit_processing_status, emit_error


@trace_flow(flow_name="DocumentEditFlow")
class TracedDocumentEditFlow(AsyncFlow):
    """带有 tracing 的文档编辑流程"""
    
    async def prep_async(self, shared):
        """流程级准备"""
        await emit_processing_status(shared, "🚀 启动文档编辑流程...")
        
        shared["flow_start_time"] = __import__('asyncio').get_event_loop().time()
        
        return {
            "flow_id": "document_edit_flow",
            "start_time": shared["flow_start_time"]
        }
    
    async def post_async(self, shared, prep_result, exec_result):
        """流程级后处理"""
        flow_duration = __import__('asyncio').get_event_loop().time() - prep_result["start_time"]
        
        shared["flow_metadata"] = {
            "flow_id": prep_result["flow_id"],
            "duration": flow_duration,
            "status": "completed"
        }
        
        await emit_processing_status(
            shared,
            f"✅ 文档编辑流程完成，耗时: {flow_duration:.2f}秒"
        )
        
        return exec_result


def create_document_edit_flow():
    """
    创建文档编辑流程
    
    流程：DocumentEditNode（单节点）
    
    Returns:
        Flow: 文档编辑流程
    """
    edit_node = DocumentEditNode()
    
    # 创建并返回带 tracing 的 AsyncFlow
    flow = TracedDocumentEditFlow()
    flow.start_node = edit_node
    return flow


class DocumentEditFlow:
    """
    文档编辑流程包装器 - 兼容现有接口
    """
    
    def __init__(self):
        self.name = "DocumentEditFlow"
        self.description = "文档编辑流程"
        self.flow = create_document_edit_flow()
    
    async def run_async(self, shared: dict) -> str:
        """
        异步运行文档编辑流程（智能 subagent 模式）
        
        Args:
            shared: pocketflow 字典共享变量
                必需字段:
                - document_type: 文档类型 ("design" 或 "database_design")
                - edit_instructions: 自然语言描述的修改需求
                - generated_documents: 已生成的文档列表（从 tool_execution_results 传入）
                
        工作流程:
                1. 读取当前文档内容
                2. 使用 LLM 理解 edit_instructions
                3. LLM 自动生成精确的 search/replace 操作
                4. 验证编辑操作
                5. 通过 SSE 发送 diff 视图给前端
                
        Returns:
            流程执行结果
        """
        try:
            await emit_processing_status(shared, "🚀 启动文档编辑...")
            
            # 验证输入数据
            if not await self._validate_input(shared):
                raise ValueError("输入数据验证失败")
            
            # 执行 pocketflow 异步流程
            result = await self.flow.run_async(shared)
            
            await emit_processing_status(shared, "✅ 文档编辑提案生成完成")
            
            return result
            
        except Exception as e:
            await emit_error(shared, f"❌ 文档编辑流程执行失败: {e}")
            shared["document_edit_flow_error"] = str(e)
            raise e
    
    async def _validate_input(self, shared: dict) -> bool:
        """验证输入数据"""
        try:
            # 检查必需的输入
            if not shared.get("document_type"):
                await emit_error(shared, "❌ 缺少必需输入: document_type")
                return False
            
            if not shared.get("edit_instructions"):
                await emit_error(shared, "❌ 缺少必需输入: edit_instructions")
                return False
            
            await emit_processing_status(shared, "✅ 输入数据验证通过")
            return True
            
        except Exception as e:
            await emit_error(shared, f"❌ 输入数据验证失败: {str(e)}")
            return False

