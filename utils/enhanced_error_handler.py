"""
增强错误处理系统

为GTPlanner提供全面的错误处理、重试机制和错误恢复功能，包括：
- 统一错误分类和处理
- 智能重试机制
- 错误恢复策略
- 错误日志和监控
- 用户友好的错误消息
"""

import asyncio
import time
import logging
import traceback
from typing import Any, Dict, Optional, Callable, Union, List, Type
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import functools

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"           # 低影响，可忽略
    MEDIUM = "medium"     # 中等影响，需要处理
    HIGH = "high"         # 高影响，需要立即处理
    CRITICAL = "critical" # 严重错误，系统可能不可用


class ErrorCategory(Enum):
    """错误类别"""
    NETWORK = "network"           # 网络相关错误
    DATABASE = "database"         # 数据库相关错误
    LLM_API = "llm_api"          # LLM API相关错误
    VALIDATION = "validation"     # 数据验证错误
    PERMISSION = "permission"     # 权限相关错误
    TIMEOUT = "timeout"           # 超时错误
    RESOURCE = "resource"         # 资源相关错误
    CONFIGURATION = "configuration"  # 配置相关错误
    UNKNOWN = "unknown"          # 未知错误


@dataclass
class ErrorContext:
    """错误上下文"""
    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    details: Dict[str, Any]
    stack_trace: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None


@dataclass
class RetryConfig:
    """重试配置"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_backoff: bool = True
    jitter: bool = True
    retryable_errors: List[Type[Exception]] = None
    
    def __post_init__(self):
        if self.retryable_errors is None:
            self.retryable_errors = [
                ConnectionError,
                TimeoutError,
                asyncio.TimeoutError,
                OSError
            ]


class EnhancedErrorHandler:
    """增强错误处理器"""
    
    def __init__(self):
        self.error_history: List[ErrorContext] = []
        self.error_callbacks: List[Callable[[ErrorContext], None]] = []
        self.retry_configs: Dict[str, RetryConfig] = {}
        
        # 错误分类映射
        self.error_classification: Dict[Type[Exception], ErrorCategory] = {
            ConnectionError: ErrorCategory.NETWORK,
            TimeoutError: ErrorCategory.TIMEOUT,
            asyncio.TimeoutError: ErrorCategory.TIMEOUT,
            OSError: ErrorCategory.NETWORK,
            ValueError: ErrorCategory.VALIDATION,
            TypeError: ErrorCategory.VALIDATION,
            KeyError: ErrorCategory.VALIDATION,
            PermissionError: ErrorCategory.PERMISSION,
            FileNotFoundError: ErrorCategory.RESOURCE,
            MemoryError: ErrorCategory.RESOURCE,
        }
        
        logger.info("增强错误处理系统初始化完成")
    
    def register_error_callback(self, callback: Callable[[ErrorContext], None]):
        """注册错误回调函数"""
        self.error_callbacks.append(callback)
    
    def register_retry_config(self, operation_name: str, config: RetryConfig):
        """注册重试配置"""
        self.retry_configs[operation_name] = config
    
    def _classify_error(self, error: Exception) -> tuple[ErrorCategory, ErrorSeverity]:
        """分类错误"""
        error_type = type(error)
        
        # 获取错误类别
        category = self.error_classification.get(error_type, ErrorCategory.UNKNOWN)
        
        # 根据错误类型确定严重程度
        if error_type in [ConnectionError, TimeoutError, asyncio.TimeoutError]:
            severity = ErrorSeverity.MEDIUM
        elif error_type in [ValueError, TypeError, KeyError]:
            severity = ErrorSeverity.MEDIUM
        elif error_type in [PermissionError, MemoryError]:
            severity = ErrorSeverity.HIGH
        else:
            severity = ErrorSeverity.MEDIUM
        
        return category, severity
    
    def _create_error_context(
        self,
        error: Exception,
        message: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> ErrorContext:
        """创建错误上下文"""
        error_id = f"err_{int(time.time() * 1000)}"
        category, severity = self._classify_error(error)
        
        return ErrorContext(
            error_id=error_id,
            timestamp=datetime.now(),
            severity=severity,
            category=category,
            message=message,
            details=details,
            stack_trace=traceback.format_exc(),
            user_id=user_id,
            session_id=session_id,
            request_id=request_id
        )
    
    def handle_error(
        self,
        error: Exception,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        log_error: bool = True
    ) -> ErrorContext:
        """处理错误"""
        if details is None:
            details = {}
        
        error_context = self._create_error_context(
            error, message, details, user_id, session_id, request_id
        )
        
        # 记录到历史
        self.error_history.append(error_context)
        
        # 限制历史记录大小
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-500:]
        
        # 记录日志
        if log_error:
            self._log_error(error_context)
        
        # 通知回调函数
        for callback in self.error_callbacks:
            try:
                callback(error_context)
            except Exception as e:
                logger.error(f"错误回调函数执行失败: {e}")
        
        return error_context
    
    def _log_error(self, error_context: ErrorContext):
        """记录错误日志"""
        log_level = {
            ErrorSeverity.LOW: logging.DEBUG,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }.get(error_context.severity, logging.ERROR)
        
        logger.log(
            log_level,
            f"错误 {error_context.error_id}: {error_context.message} "
            f"[{error_context.category.value}] [{error_context.severity.value}]"
        )
        
        if error_context.stack_trace:
            logger.debug(f"堆栈跟踪:\n{error_context.stack_trace}")
    
    def get_user_friendly_message(self, error_context: ErrorContext) -> str:
        """获取用户友好的错误消息"""
        messages = {
            ErrorCategory.NETWORK: "网络连接出现问题，请检查网络连接后重试",
            ErrorCategory.DATABASE: "数据存储出现问题，请稍后重试",
            ErrorCategory.LLM_API: "AI服务暂时不可用，请稍后重试",
            ErrorCategory.VALIDATION: "输入数据格式不正确，请检查后重试",
            ErrorCategory.PERMISSION: "权限不足，请联系管理员",
            ErrorCategory.TIMEOUT: "操作超时，请稍后重试",
            ErrorCategory.RESOURCE: "系统资源不足，请稍后重试",
            ErrorCategory.CONFIGURATION: "系统配置错误，请联系技术支持",
            ErrorCategory.UNKNOWN: "发生未知错误，请联系技术支持"
        }
        
        return messages.get(error_context.category, messages[ErrorCategory.UNKNOWN])
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        if not self.error_history:
            return {
                "total_errors": 0,
                "errors_by_category": {},
                "errors_by_severity": {},
                "recent_errors": []
            }
        
        # 按类别统计
        errors_by_category = defaultdict(int)
        errors_by_severity = defaultdict(int)
        
        for error in self.error_history:
            errors_by_category[error.category.value] += 1
            errors_by_severity[error.severity.value] += 1
        
        # 最近错误
        recent_errors = [
            {
                "error_id": error.error_id,
                "timestamp": error.timestamp.isoformat(),
                "category": error.category.value,
                "severity": error.severity.value,
                "message": error.message
            }
            for error in self.error_history[-10:]
        ]
        
        return {
            "total_errors": len(self.error_history),
            "errors_by_category": dict(errors_by_category),
            "errors_by_severity": dict(errors_by_severity),
            "recent_errors": recent_errors
        }


class RetryManager:
    """重试管理器"""
    
    def __init__(self, error_handler: Optional[EnhancedErrorHandler] = None):
        self.error_handler = error_handler or EnhancedErrorHandler()
    
    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """计算延迟时间"""
        if config.exponential_backoff:
            delay = config.base_delay * (2 ** (attempt - 1))
        else:
            delay = config.base_delay
        
        # 限制最大延迟
        delay = min(delay, config.max_delay)
        
        # 添加随机抖动
        if config.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)
        
        return delay
    
    def _is_retryable(self, error: Exception, config: RetryConfig) -> bool:
        """判断错误是否可重试"""
        return any(isinstance(error, error_type) for error_type in config.retryable_errors)
    
    async def retry_async(
        self,
        operation: Callable,
        operation_name: str = "operation",
        config: Optional[RetryConfig] = None,
        *args,
        **kwargs
    ):
        """异步重试"""
        config = config or self.retry_configs.get(operation_name, RetryConfig())
        
        last_error = None
        
        for attempt in range(1, config.max_attempts + 1):
            try:
                if asyncio.iscoroutinefunction(operation):
                    return await operation(*args, **kwargs)
                else:
                    return operation(*args, **kwargs)
                    
            except Exception as error:
                last_error = error
                
                # 检查是否可重试
                if not self._is_retryable(error, config) or attempt == config.max_attempts:
                    # 记录错误
                    self.error_handler.handle_error(
                        error,
                        f"操作 '{operation_name}' 失败",
                        {
                            "operation": operation_name,
                            "attempt": attempt,
                            "max_attempts": config.max_attempts,
                            "retryable": self._is_retryable(error, config)
                        }
                    )
                    raise
                
                # 计算延迟并等待
                delay = self._calculate_delay(attempt, config)
                logger.warning(f"操作 '{operation_name}' 第 {attempt} 次尝试失败，{delay:.2f}秒后重试: {error}")
                
                await asyncio.sleep(delay)
        
        # 如果所有重试都失败，抛出最后一个错误
        raise last_error
    
    def retry_sync(
        self,
        operation: Callable,
        operation_name: str = "operation",
        config: Optional[RetryConfig] = None,
        *args,
        **kwargs
    ):
        """同步重试"""
        config = config or self.retry_configs.get(operation_name, RetryConfig())
        
        last_error = None
        
        for attempt in range(1, config.max_attempts + 1):
            try:
                return operation(*args, **kwargs)
                    
            except Exception as error:
                last_error = error
                
                # 检查是否可重试
                if not self._is_retryable(error, config) or attempt == config.max_attempts:
                    # 记录错误
                    self.error_handler.handle_error(
                        error,
                        f"操作 '{operation_name}' 失败",
                        {
                            "operation": operation_name,
                            "attempt": attempt,
                            "max_attempts": config.max_attempts,
                            "retryable": self._is_retryable(error, config)
                        }
                    )
                    raise
                
                # 计算延迟并等待
                delay = self._calculate_delay(attempt, config)
                logger.warning(f"操作 '{operation_name}' 第 {attempt} 次尝试失败，{delay:.2f}秒后重试: {error}")
                
                time.sleep(delay)
        
        # 如果所有重试都失败，抛出最后一个错误
        raise last_error


# 全局实例
_global_error_handler: Optional[EnhancedErrorHandler] = None
_global_retry_manager: Optional[RetryManager] = None


def get_global_error_handler() -> EnhancedErrorHandler:
    """获取全局错误处理器"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = EnhancedErrorHandler()
    return _global_error_handler


def get_global_retry_manager() -> RetryManager:
    """获取全局重试管理器"""
    global _global_retry_manager
    if _global_retry_manager is None:
        _global_retry_manager = RetryManager()
    return _global_retry_manager


# 装饰器
def handle_errors(
    message: str = "操作失败",
    log_error: bool = True,
    error_handler: Optional[EnhancedErrorHandler] = None
):
    """错误处理装饰器"""
    def decorator(func: Callable):
        handler = error_handler or get_global_error_handler()
        
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as error:
                    handler.handle_error(error, message, log_error=log_error)
                    raise
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as error:
                    handler.handle_error(error, message, log_error=log_error)
                    raise
            return sync_wrapper
    return decorator


def retry_on_failure(
    operation_name: str = "operation",
    config: Optional[RetryConfig] = None,
    retry_manager: Optional[RetryManager] = None
):
    """重试装饰器"""
    def decorator(func: Callable):
        manager = retry_manager or get_global_retry_manager()
        
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await manager.retry_async(func, operation_name, config, *args, **kwargs)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                return manager.retry_sync(func, operation_name, config, *args, **kwargs)
            return sync_wrapper
    return decorator


# 便捷函数
def handle_error(
    error: Exception,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None
) -> ErrorContext:
    """处理错误的便捷函数"""
    handler = get_global_error_handler()
    return handler.handle_error(error, message, details, user_id, session_id, request_id)


def get_error_statistics() -> Dict[str, Any]:
    """获取错误统计信息的便捷函数"""
    handler = get_global_error_handler()
    return handler.get_error_statistics()
