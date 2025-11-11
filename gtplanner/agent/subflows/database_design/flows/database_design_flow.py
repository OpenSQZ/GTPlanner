"""
Database Design Flow - MySQL 数据库表结构设计流程

单节点流程，直接调用 DatabaseDesignNode 生成数据库设计文档。
"""

from pocketflow import AsyncFlow
from pocketflow_tracing import trace_flow
from ..nodes.database_design_node import DatabaseDesignNode
from gtplanner.agent.streaming import (
    emit_processing_status,
    emit_error
)


@trace_flow(flow_name="DatabaseDesignFlow")
class TracedDatabaseDesignFlow(AsyncFlow):
    """带有 tracing 的数据库设计流程"""

    async def prep_async(self, shared):
        """流程级准备"""
        await emit_processing_status(shared, "🗄️  启动数据库表结构设计流程...")
        
        shared["flow_start_time"] = __import__('asyncio').get_event_loop().time()
        
        return {
            "flow_id": "database_design_flow",
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
            f"✅ 数据库设计流程完成，耗时: {flow_duration:.2f}秒"
        )
        
        return exec_result


def create_database_design_flow():
    """
    创建简化的数据库设计流程
    
    流程：DatabaseDesignNode（单节点）
    
    Returns:
        Flow: 数据库设计流程
    """
    database_design_node = DatabaseDesignNode()
    
    # 创建并返回带 tracing 的 AsyncFlow
    flow = TracedDatabaseDesignFlow()
    flow.start_node = database_design_node
    return flow


class DatabaseDesignFlow:
    """
    数据库设计流程包装器 - 兼容现有接口
    """
    
    def __init__(self):
        self.name = "DatabaseDesignFlow"
        self.description = "MySQL 数据库表结构设计流程"
        self.flow = create_database_design_flow()
    
    async def run_async(self, shared: dict) -> str:
        """
        异步运行数据库设计流程
        
        Args:
            shared: pocketflow 字典共享变量
            
        Returns:
            流程执行结果
        """
        try:
            await emit_processing_status(shared, "🚀 启动数据库表结构设计...")
            
            # 验证输入数据
            if not await self._validate_input(shared):
                raise ValueError("输入数据验证失败")
            
            # 执行 pocketflow 异步流程
            result = await self.flow.run_async(shared)
            
            await emit_processing_status(shared, "✅ 数据库设计文档生成完成")
            
            return result
            
        except Exception as e:
            await emit_error(shared, f"❌ 数据库设计流程执行失败: {e}")
            shared["database_design_flow_error"] = str(e)
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

