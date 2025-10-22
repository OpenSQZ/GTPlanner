"""
Short Planning Flow

协调 ShortPlanningNode，实现从用户需求到步骤化流程的生成。

流程架构：
ShortPlanningNode (直接处理用户需求)
"""

from pocketflow import AsyncFlow
from pocketflow_tracing import trace_flow
from ..nodes.short_planning_node import ShortPlanningNode
from agent.streaming import (
    emit_processing_status,
    emit_error
)


@trace_flow(flow_name="ShortPlanningFlow")
class TracedShortPlanningFlow(AsyncFlow):
    """带有tracing的短规划流程"""

    async def prep_async(self, shared):
        """流程级准备"""
        # 确保使用正确的事件循环来获取时间
        shared["flow_start_time"] = __import__('asyncio').get_event_loop().time()

        return {
            "flow_id": "short_planning",
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


class ShortPlanningFlow:
    """
    短规划流程

    流程架构：
    ShortPlanningNode (直接处理用户需求生成步骤化流程)
    """

    def __init__(self):
        self.name = "ShortPlanningFlow"
        self.description = "将用户需求直接转换为步骤化的实现流程"

        # 创建节点实例
        short_planner_node = ShortPlanningNode()

        # 简化流程：只有一个节点，直接处理用户需求
        # 错误处理：节点返回"error"会结束流程

        # 创建带tracing的异步流程
        self.flow = TracedShortPlanningFlow()
        self.flow.start_node = short_planner_node

    async def run_async(self, shared: dict) -> str:
        """
        异步运行短规划流程

        Args:
            shared: pocketflow字典共享变量

        Returns:
            流程执行结果
        """
        try:

            # 验证输入数据
            if not self._validate_input(shared):
                raise ValueError("输入数据验证失败：'user_requirements' 缺失或为空。")

            # 执行异步pocketflow流程（带tracing）
            result = await self.flow.run_async(shared)

            return result

        except Exception as e:
            # 发送错误事件
            await emit_error(shared, f"❌ 异步短规划流程执行失败: {e}")
            # 在共享状态中记录错误
            shared["short_planning_flow_error"] = str(e)
            raise e

    def run(self, shared: dict) -> str:
        """
        同步运行短规划流程（兼容性）
        """
        import asyncio
        return asyncio.run(self.run_async(shared))

    def _validate_input(self, shared: dict) -> bool:
        """验证输入数据"""

        # 检查必需的用户需求
        user_requirements = shared.get("user_requirements")
        if not user_requirements:
            # 注意：这是一个同步方法，无法使用 await，所以我们只能记录错误
            # 在实际使用中，这个错误会在异步方法中被处理
            return False
        
        # previous_planning 和 improvement_points 是可选的，无需强制检查

        return True