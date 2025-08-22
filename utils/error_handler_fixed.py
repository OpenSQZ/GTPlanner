#!/usr/bin/env python3
"""
GTPlanner 统一错误处理框架 - 修复版本
提供统一的异常处理、错误分类和恢复机制
"""

import logging
from enum import Enum
from typing import Dict, Any, Optional, Callable
from functools import wraps
from dataclasses import dataclass
from datetime import datetime

# 错误严重程度枚举
class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# 错误类型枚举
class ErrorType(Enum):
    LANGUAGE_DETECTION = "language_detection"
    LLM_COMMUNICATION = "llm_communication"
    CONFIGURATION = "configuration"
    VALIDATION = "validation"
    PERFORMANCE = "performance"
    SYSTEM = "system"

# 错误上下文数据类
@dataclass
class ErrorContext:
    function_name: str
    timestamp: datetime
    error_type: ErrorType
    severity: ErrorSeverity
    additional_data: Dict[str, Any]

# GTPlanner基础异常类
class GTPlannerError(Exception):
    """GTPlanner基础异常类"""
    
    def __init__(self, message: str, error_code: str = None, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.severity = severity
        self.details = details or {}
        self.timestamp = datetime.now()

# 语言检测相关错误
class LanguageDetectionError(GTPlannerError):
    """语言检测相关错误"""
    
    def __init__(self, message: str, text: str = "", **kwargs):
        super().__init__(message, **kwargs)
        self.text = text
        self.details.update({"text_length": len(text), "text_preview": text[:50]})

# LLM通信相关错误
class LLMCommunicationError(GTPlannerError):
    """LLM通信相关错误"""
    
    def __init__(self, message: str, endpoint: str = "", status_code: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.endpoint = endpoint
        self.status_code = status_code
        self.details.update({
            "endpoint": endpoint,
            "status_code": status_code
        })

# 配置相关错误
class ConfigurationError(GTPlannerError):
    """配置相关错误"""
    
    def __init__(self, message: str, config_key: str = "", **kwargs):
        super().__init__(message, **kwargs)
        self.config_key = config_key
        self.details.update({"config_key": config_key})

# 验证相关错误
class ValidationError(GTPlannerError):
    """验证相关错误"""
    
    def __init__(self, message: str, field_name: str = "", value: Any = None, **kwargs):
        super().__init__(message, **kwargs)
        self.field_name = field_name
        self.value = value
        self.details.update({
            "field_name": field_name,
            "value": str(value),
            "value_type": type(value).__name__
        })

# 统一错误处理器
class ErrorHandler:
    """统一错误处理器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
        self.error_counts = {}
        self.recovery_strategies = self._setup_recovery_strategies()
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger("GTPlanner.ErrorHandler")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _setup_recovery_strategies(self) -> Dict[ErrorType, Callable]:
        """设置错误恢复策略"""
        return {
            ErrorType.LANGUAGE_DETECTION: self._recover_language_detection,
            ErrorType.LLM_COMMUNICATION: self._recover_llm_communication,
            ErrorType.CONFIGURATION: self._recover_configuration,
            ErrorType.VALIDATION: self._recover_validation,
        }
    
    def handle_error(self, error: Exception, context: ErrorContext) -> Any:
        """处理错误"""
        # 记录错误
        self._log_error(error, context)
        
        # 更新错误统计
        self._update_error_stats(error, context)
        
        # 尝试恢复
        if context.error_type in self.recovery_strategies:
            try:
                return self.recovery_strategies[context.error_type](error, context)
            except Exception as recovery_error:
                self.logger.error(f"恢复策略失败: {recovery_error}")
        
        # 如果无法恢复，重新抛出错误
        raise error
    
    def _log_error(self, error: Exception, context: ErrorContext):
        """记录错误信息"""
        error_info = {
            "function": context.function_name,
            "type": context.error_type.value,
            "severity": context.severity.value,
            "message": str(error),
            "timestamp": context.timestamp.isoformat(),
            "additional_data": context.additional_data
        }
        
        if context.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self.logger.error(f"严重错误: {error_info}")
        elif context.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"中等错误: {error_info}")
        else:
            self.logger.info(f"轻微错误: {error_info}")
    
    def _update_error_stats(self, error: Exception, context: ErrorContext):
        """更新错误统计"""
        error_key = f"{context.error_type.value}_{type(error).__name__}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
    
    def _recover_language_detection(self, error: Exception, context: ErrorContext) -> str:
        """语言检测错误恢复"""
        self.logger.info("使用默认语言恢复语言检测错误")
        return "en"  # 返回默认语言
    
    def _recover_llm_communication(self, error: Exception, context: ErrorContext) -> str:
        """LLM通信错误恢复"""
        self.logger.info("使用缓存或默认响应恢复LLM通信错误")
        return "默认响应：由于网络问题，请稍后重试"
    
    def _recover_configuration(self, error: Exception, context: ErrorContext) -> Any:
        """配置错误恢复"""
        self.logger.info("使用默认配置恢复配置错误")
        return {"default": True}
    
    def _recover_validation(self, error: Exception, context: ErrorContext) -> bool:
        """验证错误恢复"""
        self.logger.info("跳过验证错误，继续执行")
        return True
    
    def get_error_stats(self) -> Dict[str, int]:
        """获取错误统计"""
        return self.error_counts.copy()

# 错误处理装饰器
def handle_errors(error_type: ErrorType = ErrorType.SYSTEM, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM):
    """错误处理装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = ErrorHandler()
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = ErrorContext(
                    function_name=func.__name__,
                    timestamp=datetime.now(),
                    error_type=error_type,
                    severity=severity,
                    additional_data={
                        "args": str(args),
                        "kwargs": str(kwargs)
                    }
                )
                return error_handler.handle_error(e, context)
        return wrapper
    return decorator

# 日志记录并继续执行装饰器
def log_and_continue(func: Callable) -> Callable:
    """日志记录并继续执行装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger = logging.getLogger("GTPlanner.LogAndContinue")
            logger.warning(f"函数 {func.__name__} 执行失败: {e}")
            return None
    return wrapper

# 安全执行函数
def safe_execute(func: Callable, default_value: Any = None, *args, **kwargs) -> Any:
    """安全执行函数"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger = logging.getLogger("GTPlanner.SafeExecute")
        logger.warning(f"安全执行失败: {e}")
        return default_value
