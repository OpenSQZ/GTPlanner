"""
ReAct Orchestrator Flow

基于Function Calling的ReAct主控制器流程，支持pocketflow_tracing。
负责协调ReAct节点的执行，并管理上下文传递。
"""

from typing import Dict, Any
from pocketflow import AsyncFlow
from pocketflow_tracing import trace_flow

from .react_orchestrator_node import ReActOrchestratorNode


@trace_flow(flow_name="ReActOrchestratorFlow")
class TracedReActOrchestratorFlow(AsyncFlow):
    """带有tracing的ReAct主控制器流程"""

    async def prep_async(self, shared):
        """流程级准备"""
        # 确保使用正确的事件循环来获取时间
        shared["flow_start_time"] = __import__('asyncio').get_event_loop().time()

        return {
            "flow_id": "react_orchestrator",
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

        return exec_result


class ReActOrchestratorFlow:
    """
    ReAct主控制器流程

    基于Function Calling的ReAct主控制器，采用模块化设计，降低代码复杂度。
    支持pocketflow_tracing，并正确处理上下文传递。
    """

    def __init__(self):
        self.name = "ReActOrchestratorFlow"
        self.description = "基于Function Calling的模块化ReAct主控制器流程"

        # 创建节点实例
        react_node = ReActOrchestratorNode()

        # 创建带tracing的异步流程
        self.flow = TracedReActOrchestratorFlow()
        self.flow.start_node = react_node

    async def run_async(self, shared: Dict[str, Any] = None) -> str:
        """
        异步运行ReAct主控制器流程（无状态版本）

        Args:
            shared: 预先创建的shared字典（包含完整上下文）

        Returns:
            流程执行结果
        """
        try:
            if shared is None:
                raise ValueError("shared字典不能为空")

            # 执行异步pocketflow流程（带tracing）
            result = await self.flow.run_async(shared)

            return result

        except Exception as e:
            print(f"❌ 异步ReAct主控制器流程执行失败: {e}")
            raise e






# 向后兼容的别名
ReActOrchestratorRefactored = ReActOrchestratorFlow
