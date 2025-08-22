"""
统一错误处理框架 - Unified Error Handling Framework

这个模块是GTPlanner项目的错误处理增强功能，主要解决原有错误处理分散、
用户体验差的问题。

主要功能：
1. 统一的异常层次结构，便于错误分类和处理
2. 装饰器系统，自动进行错误处理和日志记录
3. 中央错误处理器，统一管理所有错误
4. 用户友好的错误消息，提升用户体验

技术原理：
- 异常继承：建立清晰的错误类型层次
- 装饰器模式：自动拦截和处理异常
- 策略模式：不同类型的错误采用不同的处理策略

与GTPlanner的集成作用：
- 标准化错误处理流程
- 提升系统稳定性和可靠性
- 改善用户错误体验
- 便于问题定位和调试
"""

import functools
import logging
import traceback
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional, Type, Union
from functools import wraps

# 错误严重程度枚举
# 用于分类错误的严重程度，帮助决定处理策略
class ErrorSeverity(Enum):
    LOW = "low"           # 低严重程度：不影响核心功能
    MEDIUM = "medium"     # 中等严重程度：部分功能受影响
    HIGH = "high"         # 高严重程度：核心功能受影响
    CRITICAL = "critical" # 严重程度：系统无法正常运行

# 错误类型枚举
# 用于分类不同类型的错误，便于针对性处理
class ErrorType(Enum):
    VALIDATION = "validation"           # 验证错误：输入数据不符合要求
    CONFIGURATION = "configuration"     # 配置错误：系统配置问题
    NETWORK = "network"                 # 网络错误：网络连接问题
    PERMISSION = "permission"           # 权限错误：访问权限不足
    RESOURCE = "resource"               # 资源错误：资源不足或不可用
    SYSTEM = "system"                   # 系统错误：系统内部问题
    EXTERNAL = "external"               # 外部错误：第三方服务问题

# GTPlanner基础异常类
# 所有GTPlanner相关异常的基类，提供统一的错误处理接口
class GTPlannerError(Exception):
    """
    GTPlanner基础异常类
    
    这是所有GTPlanner相关异常的基类，提供了统一的错误处理接口。
    继承自Python标准Exception类，确保与现有代码的兼容性。
    
    主要特性：
    1. 错误代码：便于错误分类和定位
    2. 严重程度：帮助决定处理策略
    3. 详细信息：提供错误的上下文信息
    4. 时间戳：记录错误发生的时间
    
    与GTPlanner的集成价值：
    - 统一的错误处理标准
    - 便于错误分类和统计
    - 支持错误追踪和调试
    """
    
    def __init__(self, message: str, error_code: str = None, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 details: Optional[Dict[str, Any]] = None):
        """
        初始化异常对象
        
        Args:
            message: 错误消息，描述错误的具体情况
            error_code: 错误代码，便于错误分类和定位
            severity: 错误严重程度，决定处理策略
            details: 错误的详细信息，提供上下文
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.severity = severity
        self.details = details or {}
        self.timestamp = datetime.now()
        self.traceback = traceback.format_exc()
    
    def __str__(self) -> str:
        """返回格式化的错误信息"""
        return f"[{self.error_code}] {self.message}"
    
    def get_full_info(self) -> Dict[str, Any]:
        """获取完整的错误信息，用于日志记录和调试"""
        return {
            'error_code': self.error_code,
            'message': self.message,
            'severity': self.severity.value,
            'timestamp': self.timestamp.isoformat(),
            'details': self.details,
            'traceback': self.traceback
        }

# 语言检测相关异常
# 专门处理语言检测过程中的各种错误
class LanguageDetectionError(GTPlannerError):
    """
    语言检测错误
    
    专门处理语言检测过程中的各种错误，如：
    - 输入文本为空或无效
    - 语言检测算法失败
    - 缓存系统错误
    - 模式匹配失败
    
    与GTPlanner的集成作用：
    - 提升语言检测的可靠性
    - 便于语言检测问题的定位
    - 支持多语言功能的错误处理
    """
    
    def __init__(self, message: str, text: str = None, 
                 detection_method: str = None, **kwargs):
        """
        初始化语言检测错误
        
        Args:
            message: 错误消息
            text: 导致错误的输入文本
            detection_method: 使用的检测方法
            **kwargs: 其他错误参数
        """
        details = kwargs.get('details', {})
        if text:
            details['input_text'] = text[:100] + '...' if len(text) > 100 else text
        if detection_method:
            details['detection_method'] = detection_method
        
        super().__init__(
            message=message,
            error_code="LANGUAGE_DETECTION_ERROR",
            severity=ErrorSeverity.MEDIUM,
            details=details
        )

# LLM通信相关异常
# 处理与语言模型通信过程中的各种错误
class LLMCommunicationError(GTPlannerError):
    """
    LLM通信错误
    
    处理与语言模型通信过程中的各种错误，如：
    - API调用失败
    - 网络连接问题
    - 认证失败
    - 响应解析错误
    
    与GTPlanner的集成作用：
    - 提升LLM调用的可靠性
    - 支持重试和降级策略
    - 便于API问题的定位
    """
    
    def __init__(self, message: str, api_endpoint: str = None, 
                 status_code: int = None, **kwargs):
        """
        初始化LLM通信错误
        
        Args:
            message: 错误消息
            api_endpoint: 调用的API端点
            status_code: HTTP状态码
            **kwargs: 其他错误参数
        """
        details = kwargs.get('details', {})
        if api_endpoint:
            details['api_endpoint'] = api_endpoint
        if status_code:
            details['status_code'] = status_code
        
        super().__init__(
            message=message,
            error_code="LLM_COMMUNICATION_ERROR",
            severity=ErrorSeverity.HIGH,
            details=details
        )

# 配置相关异常
# 处理系统配置过程中的各种错误
class ConfigurationError(GTPlannerError):
    """
    配置错误
    
    处理系统配置过程中的各种错误，如：
    - 配置文件缺失
    - 配置项无效
    - 环境变量未设置
    - 配置格式错误
    
    与GTPlanner的集成作用：
    - 确保系统配置的正确性
    - 支持配置验证和检查
    - 便于配置问题的定位
    """
    
    def __init__(self, message: str, config_file: str = None, 
                 config_key: str = None, **kwargs):
        """
        初始化配置错误
        
        Args:
            message: 错误消息
            config_file: 配置文件路径
            config_key: 配置项键名
            **kwargs: 其他错误参数
        """
        details = kwargs.get('details', {})
        if config_file:
            details['config_file'] = config_file
        if config_key:
            details['config_key'] = config_key
        
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            severity=ErrorSeverity.HIGH,
            details=details
        )

def _handle_errors_decorator(error_type: ErrorType, severity: ErrorSeverity):
    """
    内部装饰器实现
    """
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

# 验证相关异常
# 处理数据验证过程中的各种错误
class ValidationError(GTPlannerError):
    """
    验证错误
    
    处理数据验证过程中的各种错误，如：
    - 输入数据格式错误
    - 数据范围超出限制
    - 必填字段缺失
    - 数据类型不匹配
    
    与GTPlanner的集成作用：
    - 确保输入数据的质量
    - 提升系统的健壮性
    - 支持数据验证和清理
    """
    
    def __init__(self, message: str, field_name: str = None, 
                 value: Any = None, expected_type: str = None, **kwargs):
        """
        初始化验证错误
        
        Args:
            message: 错误消息
            field_name: 验证失败的字段名
            value: 验证失败的值
            expected_type: 期望的数据类型
            **kwargs: 其他错误参数
        """
        details = kwargs.get('details', {})
        if field_name:
            details['field_name'] = field_name
        if value is not None:
            details['value'] = str(value)[:100]  # 限制长度
        if expected_type:
            details['expected_type'] = expected_type
        
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            severity=ErrorSeverity.MEDIUM,
            details=details
        )

# 错误处理装饰器
# 自动拦截和处理函数执行过程中的异常
def handle_errors(error_type: ErrorType = ErrorType.SYSTEM, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM):
    """
    错误处理装饰器工厂函数
    
    返回一个装饰器，自动拦截和处理函数执行过程中的异常，提供：
    1. 自动错误分类和日志记录
    2. 用户友好的错误消息
    3. 错误上下文信息收集
    4. 支持错误恢复和降级
    
    使用方式：
    @handle_errors()  # 使用默认参数
    def risky_function():
        # 函数体
        pass
    
    @handle_errors(error_type=ErrorType.VALIDATION, severity=ErrorSeverity.HIGH)
    def validation_function():
        # 函数体
        pass
    
    与GTPlanner的集成价值：
    - 统一的错误处理标准
    - 自动错误日志记录
    """
    return _handle_errors_decorator(error_type, severity)
    - 提升系统稳定性
    - 便于问题定位和调试
    """
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # 正常执行函数
            return func(*args, **kwargs)
        except GTPlannerError as e:
            # 处理GTPlanner已知错误
            ErrorHandler.handle_error(e, {
                'function': func.__name__,
                'args': str(args)[:200],  # 限制长度
                'kwargs': str(kwargs)[:200]
            })
            raise
        except Exception as e:
            # 处理未知错误，转换为GTPlanner错误
            error = GTPlannerError(
                message=f"Unexpected error in {func.__name__}: {str(e)}",
                error_code="UNEXPECTED_ERROR",
                severity=ErrorSeverity.HIGH,
                details={
                    'original_error': str(e),
                    'function': func.__name__,
                    'args': str(args)[:200],
                    'kwargs': str(kwargs)[:200]
                }
            )
            ErrorHandler.handle_error(error)
            raise error
    
    return wrapper

# 安全执行装饰器
# 记录错误但继续执行，不中断程序流程
def log_and_continue(func: Callable) -> Callable:
    """
    安全执行装饰器
    
    记录错误但继续执行，不中断程序流程。适用于：
    1. 非关键功能的错误处理
    2. 需要降级策略的场景
    3. 错误统计和监控
    
    使用方式：
    @log_and_continue
    def non_critical_function():
        # 函数体
        pass
    
    与GTPlanner的集成价值：
    - 提升系统容错能力
    - 支持功能降级
    - 便于错误统计和分析
    """
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # 记录错误但不抛出
            ErrorHandler.log_error(e, {
                'function': func.__name__,
                'args': str(args)[:200],
                'kwargs': str(kwargs)[:200],
                'handling': 'continue_execution'
            })
            # 返回默认值或None
            return None
    
    return wrapper

# 安全执行函数
# 执行可能出错的代码块，提供错误处理
def safe_execute(func: Callable, *args, default_value: Any = None, 
                 error_context: Dict[str, Any] = None, **kwargs) -> Any:
    """
    安全执行函数
    
    执行可能出错的代码块，提供统一的错误处理接口。
    
    Args:
        func: 要执行的函数
        *args: 函数参数
        default_value: 出错时的默认返回值
        error_context: 错误上下文信息
        **kwargs: 函数关键字参数
        
    Returns:
        函数执行结果或默认值
        
    与GTPlanner的集成价值：
    - 统一的错误处理接口
    - 支持错误恢复策略
    - 便于错误统计和分析
    """
    
    try:
        return func(*args, **kwargs)
    except Exception as e:
        context = error_context or {}
        context.update({
            'function': func.__name__,
            'args': str(args)[:200],
            'kwargs': str(kwargs)[:200]
        })
        
        ErrorHandler.log_error(e, context)
        return default_value

# 中央错误处理器
# 统一管理所有错误的处理逻辑
class ErrorHandler:
    """
    中央错误处理器
    
    统一管理所有错误的处理逻辑，提供：
    1. 错误分类和路由
    2. 错误日志记录
    3. 用户通知
    4. 错误恢复建议
    
    与GTPlanner的集成价值：
    - 统一的错误处理中心
    - 便于错误监控和分析
    - 支持错误处理策略配置
    """
    
    # 错误处理策略配置
    _error_strategies = {
        ErrorSeverity.LOW: {
            'log_level': logging.INFO,
            'notify_user': False,
            'retry': False
        },
        ErrorSeverity.MEDIUM: {
            'log_level': logging.WARNING,
            'notify_user': True,
            'retry': True
        },
        ErrorSeverity.HIGH: {
            'log_level': logging.ERROR,
            'notify_user': True,
            'retry': True,
            'max_retries': 3
        },
        ErrorSeverity.CRITICAL: {
            'log_level': logging.CRITICAL,
            'notify_user': True,
            'retry': False,
            'escalate': True
        }
    }
    
    @classmethod
    def handle_error(cls, error: Exception, context: Dict[str, Any] = None):
        """
        处理错误
        
        根据错误的严重程度采用不同的处理策略。
        
        Args:
            error: 要处理的错误
            context: 错误上下文信息
        """
        context = context or {}
        
        if isinstance(error, GTPlannerError):
            # 处理GTPlanner已知错误
            cls._handle_gtplanner_error(error, context)
        else:
            # 处理未知错误
            cls._handle_unknown_error(error, context)
    
    @classmethod
    def log_error(cls, error: Exception, context: Dict[str, Any] = None):
        """
        记录错误日志
        
        记录错误信息但不中断程序执行。
        
        Args:
            error: 要记录的错误
            context: 错误上下文信息
        """
        context = context or {}
        
        # 获取日志记录器
        logger = logging.getLogger('gtplanner.error_handler')
        
        # 记录错误信息
        if isinstance(error, GTPlannerError):
            error_info = error.get_full_info()
            logger.warning(f"GTPlanner error: {error_info}", extra=context)
        else:
            logger.warning(f"Unknown error: {str(error)}", extra=context)
    
    @classmethod
    def _handle_gtplanner_error(cls, error: GTPlannerError, context: Dict[str, Any]):
        """
        处理GTPlanner已知错误
        
        Args:
            error: GTPlanner错误对象
            context: 错误上下文信息
        """
        # 获取错误处理策略
        strategy = cls._error_strategies.get(error.severity, {})
        
        # 记录错误日志
        logger = logging.getLogger('gtplanner.error_handler')
        log_level = strategy.get('log_level', logging.ERROR)
        
        error_info = error.get_full_info()
        error_info.update(context)
        
        logger.log(log_level, f"GTPlanner error: {error_info}")
        
        # 用户通知
        if strategy.get('notify_user', False):
            cls._notify_user(error, context)
        
        # 错误恢复建议
        if error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            cls._suggest_recovery(error, context)
    
    @classmethod
    def _handle_unknown_error(cls, error: Exception, context: Dict[str, Any]):
        """
        处理未知错误
        
        Args:
            error: 未知错误对象
            context: 错误上下文信息
        """
        logger = logging.getLogger('gtplanner.error_handler')
        
        # 记录错误信息
        error_info = {
            'error_type': type(error).__name__,
            'message': str(error),
            'traceback': traceback.format_exc(),
            'context': context
        }
        
        logger.error(f"Unknown error: {error_info}")
        
        # 对于未知错误，采用保守策略
        cls._notify_user(error, context)
    
    @classmethod
    def _notify_user(cls, error: Exception, context: Dict[str, Any]):
        """
        通知用户错误信息
        
        Args:
            error: 错误对象
            context: 错误上下文信息
        """
        # 这里可以实现用户通知逻辑，如：
        # - 控制台输出
        # - 日志文件
        # - 邮件通知
        # - 系统通知
        
        if isinstance(error, GTPlannerError):
            print(f"⚠️  {error.message}")
            if error.details:
                print(f"   详细信息: {error.details}")
        else:
            print(f"❌ 发生未知错误: {str(error)}")
    
    @classmethod
    def _suggest_recovery(cls, error: GTPlannerError, context: Dict[str, Any]):
        """
        提供错误恢复建议
        
        Args:
            error: 错误对象
            context: 错误上下文信息
        """
        # 根据错误类型提供恢复建议
        if isinstance(error, ConfigurationError):
            print("💡 建议检查配置文件和环境变量设置")
        elif isinstance(error, LLMCommunicationError):
            print("💡 建议检查网络连接和API密钥设置")
        elif isinstance(error, LanguageDetectionError):
            print("💡 建议检查输入文本格式")
        elif isinstance(error, ValidationError):
            print("💡 建议检查输入数据格式和内容")
        else:
            print("💡 建议查看日志文件获取详细错误信息")
    
    @classmethod
    def get_error_statistics(cls) -> Dict[str, Any]:
        """
        获取错误统计信息
        
        用于监控和分析系统错误情况。
        
        Returns:
            包含错误统计信息的字典
        """
        # 这里可以实现错误统计逻辑
        # 如错误类型分布、频率统计等
        return {
            'total_errors': 0,
            'error_types': {},
            'severity_distribution': {},
            'recent_errors': []
        }
    
    @classmethod
    def clear_error_logs(cls):
        """
        清理错误日志
        
        用于测试或维护，清理所有错误日志。
        """
        # 这里可以实现日志清理逻辑
        pass
