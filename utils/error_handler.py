"""
统一错误处理系统

提供统一的错误处理、记录和恢复机制，确保系统的稳定性和可维护性。
"""

import asyncio
import functools
import time
import traceback
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable, Union, List
from enum import Enum

from utils.logger_config import get_logger


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"          # 轻微错误，不影响主要功能
    MEDIUM = "medium"    # 中等错误，影响部分功能
    HIGH = "high"        # 严重错误，影响核心功能
    CRITICAL = "critical"  # 致命错误，系统无法继续


@dataclass
class ErrorContext:
    """错误上下文信息"""
    source: str                           # 错误来源
    error_message: str                    # 错误消息
    error_type: str                       # 错误类型
    timestamp: float                      # 错误时间戳
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict)
    traceback_info: Optional[str] = None
    session_id: Optional[str] = None
    user_message: Optional[str] = None    # 用户友好的错误消息


class ErrorRecoveryStrategy(Enum):
    """错误恢复策略"""
    IGNORE = "ignore"        # 忽略错误，继续执行
    RETRY = "retry"          # 重试操作
    FALLBACK = "fallback"    # 使用备用方案
    FAIL_FAST = "fail_fast"  # 快速失败
    GRACEFUL_DEGRADATION = "graceful_degradation"  # 优雅降级


class UnifiedErrorHandler:
    """统一错误处理器"""
    
    def __init__(self):
        self.logger = get_logger("error_handler")
        self.error_history: List[ErrorContext] = []
        self.max_history_size = 1000
        
    def record_error(
        self,
        shared: Dict[str, Any],
        source: str,
        error: Union[str, Exception],
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        session_id: Optional[str] = None,
        user_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ErrorContext:
        """
        记录错误到共享状态和历史记录
        
        Args:
            shared: 共享状态字典
            source: 错误来源
            error: 错误对象或消息
            severity: 错误严重程度
            session_id: 会话ID
            user_message: 用户友好的错误消息
            metadata: 额外的元数据
            
        Returns:
            错误上下文对象
        """
        # 构建错误上下文
        error_context = ErrorContext(
            source=source,
            error_message=str(error),
            error_type=type(error).__name__ if isinstance(error, Exception) else "CustomError",
            timestamp=time.time(),
            severity=severity,
            metadata=metadata or {},
            session_id=session_id,
            user_message=user_message
        )
        
        # 如果是异常对象，记录堆栈信息
        if isinstance(error, Exception):
            error_context.traceback_info = traceback.format_exc()
        
        # 记录到共享状态
        if "errors" not in shared:
            shared["errors"] = []
        
        shared["errors"].append({
            "source": error_context.source,
            "error": error_context.error_message,
            "error_type": error_context.error_type,
            "timestamp": error_context.timestamp,
            "severity": error_context.severity.value,
            "session_id": error_context.session_id,
            "user_message": error_context.user_message,
            "metadata": error_context.metadata
        })
        
        # 记录到历史记录
        self.error_history.append(error_context)
        # 维护历史记录大小限制
        while len(self.error_history) > self.max_history_size:
            self.error_history.pop(0)
        
        # 记录日志
        self._log_error(error_context)
        
        return error_context
    
    def _log_error(self, error_context: ErrorContext) -> None:
        """记录错误日志"""
        log_message = f"[{error_context.source}] {error_context.error_message}"
        
        if error_context.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error_context.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif error_context.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        # 记录详细信息
        if error_context.traceback_info:
            self.logger.debug(f"Traceback: {error_context.traceback_info}")
        
        if error_context.metadata:
            self.logger.debug(f"Metadata: {error_context.metadata}")
    
    def get_error_summary(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取错误摘要
        
        Args:
            session_id: 可选的会话ID过滤
            
        Returns:
            错误摘要信息
        """
        errors = self.error_history
        if session_id:
            errors = [e for e in errors if e.session_id == session_id]
        
        if not errors:
            return {"total_errors": 0, "by_severity": {}, "recent_errors": []}
        
        # 按严重程度统计
        by_severity = {}
        for severity in ErrorSeverity:
            by_severity[severity.value] = len([e for e in errors if e.severity == severity])
        
        # 最近的错误
        recent_errors = sorted(errors, key=lambda x: x.timestamp, reverse=True)[:10]
        
        return {
            "total_errors": len(errors),
            "by_severity": by_severity,
            "recent_errors": [
                {
                    "source": e.source,
                    "error": e.error_message,
                    "severity": e.severity.value,
                    "timestamp": e.timestamp
                }
                for e in recent_errors
            ]
        }


def unified_error_handler(
    source: Optional[str] = None,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    recovery_strategy: ErrorRecoveryStrategy = ErrorRecoveryStrategy.FAIL_FAST,
    user_message: Optional[str] = None,
    fallback_value: Any = None
):
    """
    统一错误处理装饰器
    
    Args:
        source: 错误来源（如果为None，使用函数名）
        severity: 错误严重程度
        recovery_strategy: 错误恢复策略
        user_message: 用户友好的错误消息
        fallback_value: 备用返回值
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            error_source = source or f"{func.__module__}.{func.__name__}"
            
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # 尝试从参数中获取shared字典
                shared = None
                for arg in args:
                    if isinstance(arg, dict):
                        shared = arg
                        break

                if shared is None:
                    # 如果没有找到shared字典，创建一个临时的
                    shared = {}
                
                # 记录错误
                error_handler = get_error_handler()
                error_handler.record_error(
                    shared=shared,
                    source=error_source,
                    error=e,
                    severity=severity,
                    user_message=user_message
                )
                
                # 根据恢复策略处理
                if recovery_strategy == ErrorRecoveryStrategy.IGNORE:
                    return fallback_value
                elif recovery_strategy == ErrorRecoveryStrategy.FALLBACK:
                    return fallback_value
                elif recovery_strategy == ErrorRecoveryStrategy.GRACEFUL_DEGRADATION:
                    return {"success": False, "error": str(e), "fallback": True}
                else:  # FAIL_FAST
                    raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            error_source = source or f"{func.__module__}.{func.__name__}"
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 同步版本的错误处理逻辑
                shared = None
                for arg in args:
                    if isinstance(arg, dict):
                        shared = arg
                        break

                if shared is None:
                    shared = {}
                
                error_handler = get_error_handler()
                error_handler.record_error(
                    shared=shared,
                    source=error_source,
                    error=e,
                    severity=severity,
                    user_message=user_message
                )
                
                if recovery_strategy == ErrorRecoveryStrategy.IGNORE:
                    return fallback_value
                elif recovery_strategy == ErrorRecoveryStrategy.FALLBACK:
                    return fallback_value
                elif recovery_strategy == ErrorRecoveryStrategy.GRACEFUL_DEGRADATION:
                    return {"success": False, "error": str(e), "fallback": True}
                else:
                    raise
        
        # 根据函数类型返回相应的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# 全局错误处理器实例
_global_error_handler: Optional[UnifiedErrorHandler] = None


def get_error_handler() -> UnifiedErrorHandler:
    """获取全局错误处理器实例"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = UnifiedErrorHandler()
    return _global_error_handler


def reset_error_handler() -> None:
    """重置全局错误处理器（主要用于测试）"""
    global _global_error_handler
    _global_error_handler = None
