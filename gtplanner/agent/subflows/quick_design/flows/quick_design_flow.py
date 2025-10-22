"""
Quick Design Flow

快速设计文档生成流程，当前版本临时简化移除需求分析步骤：
- 直接使用 QuickDesignOptimizationNode 进行设计优化
- 跳过需求分析环节，直接基于用户输入生成设计文档

流程架构：
1. 设计优化 → 直接基于用户需求和项目规划生成完整设计文档

注意：
- 当前版本临时移除需求分析节点以简化流程
- 需求分析相关代码已注释保留，未来版本可能重新启用
- 这是"软移除"策略，便于后续快速恢复功能
"""

from pocketflow import AsyncFlow
from pocketflow_tracing import trace_flow
# TODO: 临时移除需求分析节点导入，未来版本可能重新启用
# from ..nodes.quick_requirements_analysis_node import QuickRequirementsAnalysisNode
from ..nodes.quick_design_optimization_node import QuickDesignOptimizationNode
from agent.streaming import (
    emit_processing_status,
    emit_error
)


@trace_flow(flow_name="QuickDesignFlow")
class TracedQuickDesignFlow(AsyncFlow):
    """带有tracing的快速设计流程"""

    async def prep_async(self, shared):
        """流程级准备"""
        # 发送流程启动事件
        await emit_processing_status(shared, "🚀 启动快速设计流程...")

        shared["flow_start_time"] = __import__('asyncio').get_event_loop().time()

        return {
            "flow_id": "quick_design_flow",
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

        # 发送流程完成事件
        await emit_processing_status(
            shared,
            f"✅ 快速设计流程完成，耗时: {flow_duration:.2f}秒"
        )

        return exec_result


def create_quick_design_flow():
    """
    创建简化的快速设计流程。

    流程设计：
    1. 设计优化（直接开始，跳过需求分析）

    Returns:
        Flow: 简化的快速设计流程
    """
    # TODO: 临时移除需求分析节点创建，未来版本可能重新启用
    # requirements_analysis = QuickRequirementsAnalysisNode()
    design_optimization = QuickDesignOptimizationNode()

    # TODO: 临时移除需求分析节点连接，未来版本可能重新启用
    # requirements_analysis - "default" >> design_optimization

    # 创建并返回带tracing的AsyncFlow，直接从设计优化开始
    flow = TracedQuickDesignFlow()
    flow.start_node = design_optimization
    return flow


class QuickDesignFlow:
    """
    快速设计流程包装器 - 兼容现有接口
    """

    def __init__(self):
        self.name = "QuickDesignFlow"
        self.description = "快速设计流程"
        self.flow = create_quick_design_flow()

    async def run_async(self, shared: dict) -> str:
        """
        异步运行快速设计流程

        Args:
            shared: pocketflow字典共享变量

        Returns:
            流程执行结果
        """
        try:
            # 发送流程启动事件
            await emit_processing_status(shared, "🚀 启动快速设计文档生成流程...")

            # 验证输入数据
            if not await self._validate_input(shared):
                raise ValueError("输入数据验证失败")

            # 执行pocketflow异步流程
            result = await self.flow.run_async(shared)

            # 发送流程完成事件
            await emit_processing_status(shared, "✅ 快速设计文档生成流程执行完成")

            return result

        except Exception as e:
            # 发送错误事件
            await emit_error(shared, f"❌ 快速设计流程执行失败: {e}")

            # 在共享状态中记录错误
            shared["quick_design_flow_error"] = str(e)
            raise e
    
    async def _validate_input(self, shared: dict) -> bool:
        """验证输入数据"""
        try:
            # 检查必需的输入 - 支持多种输入源
            has_user_requirements = "user_requirements" in shared and shared["user_requirements"]
            has_short_planning = "short_planning" in shared and shared["short_planning"]
            has_user_input = "user_input" in shared and shared["user_input"].get("processed_natural_language")

            if not (has_user_requirements or has_short_planning or has_user_input):
                await emit_error(shared, "❌ 缺少必需输入: 需要 user_requirements、short_planning 或 user_input 中的任意一个")
                return False

            # 如果有用户需求，优先使用；否则使用短期规划结果或用户输入
            if has_user_requirements:
                await emit_processing_status(shared, "✅ 使用用户需求作为快速设计输入")
            elif has_short_planning:
                await emit_processing_status(shared, "✅ 使用短期规划结果作为快速设计输入")
            else:
                await emit_processing_status(shared, "✅ 使用用户输入作为快速设计输入")

            return True

        except Exception as e:
            await emit_error(shared, f"❌ 输入数据验证失败: {str(e)}")
            return False
