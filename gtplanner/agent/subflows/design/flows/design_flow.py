"""
Design Flow - 统一的设计文档生成流程

单节点流程，直接调用 DesignNode 生成设计文档。
"""

from pocketflow import AsyncFlow
from pocketflow_tracing import trace_flow
from ..nodes.design_node import DesignNode
from ..nodes.prefab_functions_detail_node import PrefabFunctionsDetailNode
from gtplanner.agent.streaming import (
    emit_processing_status,
    emit_error
)


@trace_flow(flow_name="DesignFlow")
class TracedDesignFlow(AsyncFlow):
    """带有 tracing 的设计流程"""

    async def prep_async(self, shared):
        """流程级准备"""
        await emit_processing_status(shared, "🎨 启动设计文档生成流程...")
        
        shared["flow_start_time"] = __import__('asyncio').get_event_loop().time()
        
        return {
            "flow_id": "design_flow",
            "start_time": shared["flow_start_time"]
        }

    async def post_async(self, shared, prep_res, exec_res):
        """流程级后处理"""
        flow_duration = __import__('asyncio').get_event_loop().time() - prep_res["start_time"]

        shared["flow_metadata"] = {
            "flow_id": prep_res["flow_id"],
            "duration": flow_duration,
            "status": "completed"
        }

        # 将预制件函数详情文档添加到 generated_documents
        if "prefab_functions_document" in shared:
            if "generated_documents" not in shared:
                shared["generated_documents"] = []

            # 检查是否已经存在同名文档，避免重复添加
            existing_filenames = [doc.get("filename") for doc in shared["generated_documents"]]
            if "prefabs_info.md" not in existing_filenames:
                shared["generated_documents"].append({
                    "type": "design",
                    "filename": "prefabs_info.md",
                    "content": shared["prefab_functions_document"],
                    "tool_name": "prefab_functions_detail"
                })

        await emit_processing_status(
            shared,
            f"✅ 设计流程完成，耗时: {flow_duration:.2f}秒"
        )

        return exec_res


def create_design_flow():
    """
    创建设计流程

    流程：DesignNode -> PrefabFunctionsDetailNode

    DesignNode: 生成系统设计文档
    PrefabFunctionsDetailNode: 查询推荐预制件的函数详情并生成文档

    Returns:
        Flow: 设计流程
    """
    design_node = DesignNode()
    prefab_functions_detail_node = PrefabFunctionsDetailNode()

    # 将设计节点连接到预制件函数详情查询节点
    # 使用 pocketflow 的链接方式：node.next(next_node, action)
    design_node.next(prefab_functions_detail_node, "default")

    # 创建并返回带 tracing 的 AsyncFlow
    flow = TracedDesignFlow()
    flow.start_node = design_node
    return flow


class DesignFlow:
    """
    设计流程包装器 - 兼容现有接口
    """

    def __init__(self):
        self.name = "DesignFlow"
        self.description = "统一的设计文档生成流程（包含预制件函数详情查询）"
        self.flow = create_design_flow()
    
    async def run_async(self, shared: dict) -> str:
        """
        异步运行设计流程
        
        Args:
            shared: pocketflow 字典共享变量
            
        Returns:
            流程执行结果
        """
        try:
            await emit_processing_status(shared, "🚀 启动设计文档生成...")
            
            # 验证输入数据
            if not await self._validate_input(shared):
                raise ValueError("输入数据验证失败")
            
            # 执行 pocketflow 异步流程
            result = await self.flow.run_async(shared)
            
            await emit_processing_status(shared, "✅ 设计文档生成完成")
            
            return result
            
        except Exception as e:
            await emit_error(shared, f"❌ 设计流程执行失败: {e}")
            shared["design_flow_error"] = str(e)
            raise e
    
    async def _validate_input(self, shared: dict) -> bool:
        """验证输入数据"""
        try:
            # 检查必需的输入：user_requirements
            if not shared.get("user_requirements"):
                await emit_error(shared, "❌ 缺少必需输入: user_requirements")
                return False
            
            await emit_processing_status(shared, "✅ 输入数据验证通过")
            return True
            
        except Exception as e:
            await emit_error(shared, f"❌ 输入数据验证失败: {str(e)}")
            return False

