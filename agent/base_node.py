"""
Agent节点基类

提供统一的节点接口和错误处理机制，确保所有节点的一致性和可维护性。
"""

import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
from pocketflow import AsyncNode

from utils.error_handler import (
    get_error_handler, 
    ErrorSeverity, 
    unified_error_handler,
    ErrorRecoveryStrategy
)
from agent.streaming import emit_error, emit_processing_status


class BaseAgentNode(AsyncNode, ABC):
    """
    Agent节点基类
    
    提供统一的错误处理、日志记录和状态管理功能。
    所有Agent节点都应该继承此基类。
    """
    
    def __init__(self, node_name: Optional[str] = None):
        """
        初始化节点
        
        Args:
            node_name: 节点名称，如果为None则使用类名
        """
        super().__init__()
        self.name = node_name or self.__class__.__name__
        self.error_handler = get_error_handler()
        
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备阶段 - 带统一错误处理
        
        Args:
            shared: 共享状态字典
            
        Returns:
            准备结果字典
        """
        try:
            # 记录开始时间
            start_time = time.time()
            
            # 发送处理状态事件
            await self._emit_processing_start(shared)
            
            # 调用子类实现的准备逻辑
            result = await self._prep_impl(shared)
            
            # 添加通用元数据
            result.update({
                "node_name": self.name,
                "prep_start_time": start_time,
                "prep_duration": time.time() - start_time,
                "timestamp": time.time()
            })
            
            return result
            
        except Exception as e:
            # 统一错误处理
            error_context = self.error_handler.record_error(
                shared=shared,
                source=f"{self.name}.prep",
                error=e,
                severity=ErrorSeverity.HIGH,
                user_message=f"{self.name}节点准备阶段失败"
            )
            
            # 发送错误事件
            await emit_error(shared, str(e))
            
            return {
                "error": str(e),
                "error_type": type(e).__name__,
                "error_context": error_context,
                "node_name": self.name,
                "timestamp": time.time()
            }
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行阶段 - 带统一错误处理
        
        Args:
            prep_res: 准备阶段结果
            
        Returns:
            执行结果字典
        """
        if "error" in prep_res:
            return prep_res  # 传递准备阶段的错误
        
        try:
            # 记录开始时间
            start_time = time.time()
            
            # 调用子类实现的执行逻辑
            result = await self._exec_impl(prep_res)
            
            # 添加通用元数据
            if isinstance(result, dict):
                result.update({
                    "node_name": self.name,
                    "exec_start_time": start_time,
                    "exec_duration": time.time() - start_time,
                    "timestamp": time.time()
                })
            
            return result
            
        except Exception as e:
            # 使用自定义异常处理
            from utils.custom_exceptions import map_standard_exception, ProcessingError

            # 映射为自定义异常
            if not isinstance(e, ProcessingError):
                custom_exc = map_standard_exception(e)
                if hasattr(custom_exc, 'details'):
                    custom_exc.details.update({
                        "node_name": self.name,
                        "failed_stage": "execution"
                    })
            else:
                custom_exc = e

            error_dict = custom_exc.to_dict()
            error_dict.update({
                "node_name": self.name,
                "failed_stage": "execution",
                "timestamp": time.time()
            })

            return error_dict
    
    async def post_async(
        self,
        shared: Dict[str, Any],
        prep_res: Dict[str, Any],
        exec_res: Dict[str, Any]
    ) -> str:
        """
        后处理阶段 - 带统一错误处理
        
        Args:
            shared: 共享状态字典
            prep_res: 准备阶段结果
            exec_res: 执行阶段结果
            
        Returns:
            下一步动作
        """
        try:
            # 检查执行阶段是否有错误
            if "error" in exec_res:
                # 记录执行阶段的错误
                self.error_handler.record_error(
                    shared=shared,
                    source=f"{self.name}.exec",
                    error=exec_res["error"],
                    severity=ErrorSeverity.HIGH,
                    user_message=exec_res.get("error", "执行失败")
                )
                
                # 发送错误事件
                await emit_error(shared, exec_res["error"])
                
                return "error"
            
            # 调用子类实现的后处理逻辑
            next_action = await self._post_impl(shared, prep_res, exec_res)
            
            # 发送处理完成事件
            await self._emit_processing_complete(shared, next_action)
            
            return next_action
            
        except Exception as e:
            # 统一错误处理
            self.error_handler.record_error(
                shared=shared,
                source=f"{self.name}.post",
                error=e,
                severity=ErrorSeverity.HIGH,
                user_message=f"{self.name}节点后处理失败"
            )
            
            # 发送错误事件
            await emit_error(shared, str(e))
            
            return "error"
    
    @abstractmethod
    async def _prep_impl(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """
        子类需要实现的准备逻辑
        
        Args:
            shared: 共享状态字典
            
        Returns:
            准备结果字典
        """
        pass
    
    @abstractmethod
    async def _exec_impl(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        子类需要实现的执行逻辑
        
        Args:
            prep_res: 准备阶段结果
            
        Returns:
            执行结果字典
        """
        pass
    
    @abstractmethod
    async def _post_impl(
        self,
        shared: Dict[str, Any],
        prep_res: Dict[str, Any],
        exec_res: Dict[str, Any]
    ) -> str:
        """
        子类需要实现的后处理逻辑
        
        Args:
            shared: 共享状态字典
            prep_res: 准备阶段结果
            exec_res: 执行阶段结果
            
        Returns:
            下一步动作
        """
        pass
    
    async def _emit_processing_start(self, shared: Dict[str, Any]) -> None:
        """发送处理开始事件"""
        try:
            await emit_processing_status(shared, f"🚀 {self.name}节点开始处理...")
        except Exception:
            # 忽略流式事件发送错误，不影响主要逻辑
            pass
    
    async def _emit_processing_complete(self, shared: Dict[str, Any], next_action: str) -> None:
        """发送处理完成事件"""
        try:
            await emit_processing_status(shared, f"✅ {self.name}节点处理完成，下一步: {next_action}")
        except Exception:
            # 忽略流式事件发送错误，不影响主要逻辑
            pass
    
    def get_node_stats(self) -> Dict[str, Any]:
        """
        获取节点统计信息
        
        Returns:
            节点统计信息
        """
        return {
            "node_name": self.name,
            "node_type": self.__class__.__name__,
            "error_count": len([e for e in self.error_handler.error_history if e.source.startswith(self.name)])
        }


class SimpleAgentNode(BaseAgentNode):
    """
    简单Agent节点
    
    为简单的同步操作提供便捷的基类。
    """
    
    def __init__(self, node_name: Optional[str] = None):
        super().__init__(node_name)
    
    async def _prep_impl(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """默认的准备实现 - 子类可以重写"""
        return {"ready": True}
    
    async def _exec_impl(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """默认的执行实现 - 子类必须重写"""
        raise NotImplementedError("子类必须实现 _exec_impl 方法")
    
    async def _post_impl(
        self,
        shared: Dict[str, Any],
        prep_res: Dict[str, Any],
        exec_res: Dict[str, Any]
    ) -> str:
        """默认的后处理实现 - 子类可以重写"""
        return "success"


# 便捷的错误处理装饰器，专门用于节点方法
def node_error_handler(
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    user_message: Optional[str] = None
):
    """
    节点方法错误处理装饰器
    
    Args:
        severity: 错误严重程度
        user_message: 用户友好的错误消息
    """
    return unified_error_handler(
        severity=severity,
        recovery_strategy=ErrorRecoveryStrategy.GRACEFUL_DEGRADATION,
        user_message=user_message,
        fallback_value={"success": False, "error": "操作失败", "fallback": True}
    )
