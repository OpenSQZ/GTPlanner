"""
自定义异常类型体系

定义GTPlanner项目的异常类型层次结构，提供具体的错误代码和用户友好的消息。
"""

import asyncio
from typing import Dict, Any, Optional
from enum import Enum


class ErrorCode(Enum):
    """错误代码枚举"""
    
    # 通用错误 (1000-1099)
    UNKNOWN_ERROR = 1000
    INVALID_INPUT = 1001
    MISSING_REQUIRED_FIELD = 1002
    INVALID_CONFIGURATION = 1003
    
    # API相关错误 (1100-1199)
    API_CONNECTION_ERROR = 1100
    API_TIMEOUT_ERROR = 1101
    API_RATE_LIMIT_ERROR = 1102
    API_AUTHENTICATION_ERROR = 1103
    API_INVALID_RESPONSE = 1104
    API_QUOTA_EXCEEDED = 1105
    
    # 配置错误 (1200-1299)
    CONFIG_FILE_NOT_FOUND = 1200
    CONFIG_PARSE_ERROR = 1201
    CONFIG_VALIDATION_ERROR = 1202
    CONFIG_MISSING_REQUIRED = 1203
    
    # 验证错误 (1300-1399)
    VALIDATION_FAILED = 1300
    SCHEMA_VALIDATION_ERROR = 1301
    DATA_TYPE_ERROR = 1302
    VALUE_OUT_OF_RANGE = 1303
    
    # 处理错误 (1400-1499)
    PROCESSING_FAILED = 1400
    NODE_EXECUTION_ERROR = 1401
    FLOW_EXECUTION_ERROR = 1402
    TIMEOUT_ERROR = 1403
    
    # 存储错误 (1500-1599)
    STORAGE_ERROR = 1500
    FILE_NOT_FOUND = 1501
    FILE_PERMISSION_ERROR = 1502
    DATABASE_ERROR = 1503
    
    # 网络错误 (1600-1699)
    NETWORK_ERROR = 1600
    CONNECTION_TIMEOUT = 1601
    DNS_RESOLUTION_ERROR = 1602
    SSL_ERROR = 1603


class GTPlannerException(Exception):
    """GTPlanner基础异常类"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        suggestions: Optional[list] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.user_message = user_message or self._generate_user_message()
        self.suggestions = suggestions or []
    
    def _generate_user_message(self) -> str:
        """生成用户友好的错误消息"""
        user_messages = {
            ErrorCode.UNKNOWN_ERROR: "发生了未知错误，请稍后重试",
            ErrorCode.INVALID_INPUT: "输入数据格式不正确",
            ErrorCode.MISSING_REQUIRED_FIELD: "缺少必需的字段",
            ErrorCode.INVALID_CONFIGURATION: "配置文件有误",
            ErrorCode.API_CONNECTION_ERROR: "无法连接到API服务",
            ErrorCode.API_TIMEOUT_ERROR: "API请求超时",
            ErrorCode.API_RATE_LIMIT_ERROR: "API请求频率过高，请稍后重试",
            ErrorCode.API_AUTHENTICATION_ERROR: "API认证失败，请检查密钥",
            ErrorCode.CONFIG_FILE_NOT_FOUND: "配置文件未找到",
            ErrorCode.PROCESSING_FAILED: "处理请求时发生错误",
            ErrorCode.NETWORK_ERROR: "网络连接出现问题"
        }
        return user_messages.get(self.error_code, "发生了错误")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_code": self.error_code.value,
            "error_name": self.error_code.name,
            "message": self.message,
            "user_message": self.user_message,
            "details": self.details,
            "suggestions": self.suggestions
        }
    
    def __str__(self) -> str:
        return f"[{self.error_code.name}] {self.message}"


class APIError(GTPlannerException):
    """API相关错误"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.API_CONNECTION_ERROR,
        status_code: Optional[int] = None,
        response_data: Optional[Dict] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if status_code:
            details['status_code'] = status_code
        if response_data:
            details['response_data'] = response_data
        
        super().__init__(message, error_code, details, **kwargs)
        self.status_code = status_code
        self.response_data = response_data


class ConfigError(GTPlannerException):
    """配置相关错误"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.CONFIG_VALIDATION_ERROR,
        config_file: Optional[str] = None,
        config_key: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if config_file:
            details['config_file'] = config_file
        if config_key:
            details['config_key'] = config_key
        
        super().__init__(message, error_code, details, **kwargs)
        self.config_file = config_file
        self.config_key = config_key


class ValidationError(GTPlannerException):
    """验证相关错误"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.VALIDATION_FAILED,
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
        expected_type: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if field_name:
            details['field_name'] = field_name
        if field_value is not None:
            details['field_value'] = str(field_value)
        if expected_type:
            details['expected_type'] = expected_type
        
        super().__init__(message, error_code, details, **kwargs)
        self.field_name = field_name
        self.field_value = field_value
        self.expected_type = expected_type


class ProcessingError(GTPlannerException):
    """处理相关错误"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.PROCESSING_FAILED,
        node_name: Optional[str] = None,
        flow_name: Optional[str] = None,
        stage: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if node_name:
            details['node_name'] = node_name
        if flow_name:
            details['flow_name'] = flow_name
        if stage:
            details['stage'] = stage
        
        super().__init__(message, error_code, details, **kwargs)
        self.node_name = node_name
        self.flow_name = flow_name
        self.stage = stage


class NetworkError(GTPlannerException):
    """网络相关错误"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.NETWORK_ERROR,
        url: Optional[str] = None,
        timeout: Optional[float] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if url:
            details['url'] = url
        if timeout:
            details['timeout'] = timeout
        
        super().__init__(message, error_code, details, **kwargs)
        self.url = url
        self.timeout = timeout


class StorageError(GTPlannerException):
    """存储相关错误"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.STORAGE_ERROR,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if file_path:
            details['file_path'] = file_path
        if operation:
            details['operation'] = operation
        
        super().__init__(message, error_code, details, **kwargs)
        self.file_path = file_path
        self.operation = operation


# 异常映射函数
def map_standard_exception(exc: Exception) -> GTPlannerException:
    """将标准异常映射为自定义异常"""
    
    # 网络相关异常
    if isinstance(exc, (ConnectionError, TimeoutError)):
        return NetworkError(
            message=str(exc),
            error_code=ErrorCode.NETWORK_ERROR if isinstance(exc, ConnectionError) else ErrorCode.CONNECTION_TIMEOUT
        )
    
    # 文件相关异常
    if isinstance(exc, FileNotFoundError):
        return StorageError(
            message=str(exc),
            error_code=ErrorCode.FILE_NOT_FOUND,
            file_path=getattr(exc, 'filename', None)
        )
    
    if isinstance(exc, PermissionError):
        return StorageError(
            message=str(exc),
            error_code=ErrorCode.FILE_PERMISSION_ERROR,
            file_path=getattr(exc, 'filename', None)
        )
    
    # 值相关异常
    if isinstance(exc, ValueError):
        return ValidationError(
            message=str(exc),
            error_code=ErrorCode.DATA_TYPE_ERROR
        )
    
    if isinstance(exc, TypeError):
        return ValidationError(
            message=str(exc),
            error_code=ErrorCode.DATA_TYPE_ERROR
        )
    
    # 键相关异常
    if isinstance(exc, KeyError):
        return ValidationError(
            message=f"缺少必需的键: {str(exc)}",
            error_code=ErrorCode.MISSING_REQUIRED_FIELD,
            field_name=str(exc).strip("'\"")
        )
    
    # 默认映射
    return GTPlannerException(
        message=str(exc),
        error_code=ErrorCode.UNKNOWN_ERROR,
        details={"original_exception": type(exc).__name__}
    )


# 异常处理装饰器
def handle_exceptions(
    default_error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
    reraise: bool = True
):
    """异常处理装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except GTPlannerException:
                # 已经是自定义异常，直接重新抛出
                if reraise:
                    raise
            except Exception as e:
                # 映射为自定义异常
                custom_exc = map_standard_exception(e)
                if reraise:
                    raise custom_exc
                return custom_exc
        
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except GTPlannerException:
                if reraise:
                    raise
            except Exception as e:
                custom_exc = map_standard_exception(e)
                if reraise:
                    raise custom_exc
                return custom_exc
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    
    return decorator


# 便捷函数
def raise_api_error(message: str, status_code: int = None, **kwargs):
    """抛出API错误"""
    error_code = ErrorCode.API_CONNECTION_ERROR
    if status_code:
        if status_code == 401:
            error_code = ErrorCode.API_AUTHENTICATION_ERROR
        elif status_code == 429:
            error_code = ErrorCode.API_RATE_LIMIT_ERROR
        elif status_code >= 500:
            error_code = ErrorCode.API_CONNECTION_ERROR
    
    raise APIError(message, error_code, status_code=status_code, **kwargs)


def raise_config_error(message: str, config_file: str = None, **kwargs):
    """抛出配置错误"""
    raise ConfigError(message, config_file=config_file, **kwargs)


def raise_validation_error(message: str, field_name: str = None, **kwargs):
    """抛出验证错误"""
    raise ValidationError(message, field_name=field_name, **kwargs)
