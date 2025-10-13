"""
自定义异常类

提供统一的异常处理和错误码管理。
"""

from typing import Optional, Dict, Any
from enum import Enum


class ErrorCode(str, Enum):
    """错误码枚举"""
    
    # 通用错误 (1000-1999)
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    
    # 验证错误 (2000-2999)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_REQUEST = "INVALID_REQUEST"
    INVALID_PARAMETER = "INVALID_PARAMETER"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    
    # 认证/授权错误 (3000-3999)
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_API_KEY = "INVALID_API_KEY"
    API_KEY_EXPIRED = "API_KEY_EXPIRED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # 资源错误 (4000-4999)
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    
    # Session/Context错误 (5000-5999)
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    INVALID_SESSION_STATE = "INVALID_SESSION_STATE"
    CONTEXT_CORRUPTED = "CONTEXT_CORRUPTED"
    
    # LLM相关错误 (6000-6999)
    LLM_API_ERROR = "LLM_API_ERROR"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_RATE_LIMIT = "LLM_RATE_LIMIT"
    LLM_INVALID_RESPONSE = "LLM_INVALID_RESPONSE"
    LLM_TOKEN_LIMIT_EXCEEDED = "LLM_TOKEN_LIMIT_EXCEEDED"
    
    # 工具相关错误 (7000-7999)
    TOOL_EXECUTION_ERROR = "TOOL_EXECUTION_ERROR"
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    TOOL_TIMEOUT = "TOOL_TIMEOUT"
    INVALID_TOOL_ARGUMENTS = "INVALID_TOOL_ARGUMENTS"
    
    # 搜索相关错误 (8000-8999)
    SEARCH_API_ERROR = "SEARCH_API_ERROR"
    SEARCH_TIMEOUT = "SEARCH_TIMEOUT"
    INVALID_SEARCH_QUERY = "INVALID_SEARCH_QUERY"
    
    # 数据相关错误 (9000-9999)
    DATABASE_ERROR = "DATABASE_ERROR"
    CACHE_ERROR = "CACHE_ERROR"
    COMPRESSION_ERROR = "COMPRESSION_ERROR"
    SERIALIZATION_ERROR = "SERIALIZATION_ERROR"


class GTBaseException(Exception):
    """GTPlanner基础异常类"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
    ):
        """
        初始化异常
        
        Args:
            message: 错误消息
            error_code: 错误码
            status_code: HTTP状态码
            details: 额外的错误详情
            original_exception: 原始异常（如果有）
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.original_exception = original_exception
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "error": True,
            "error_code": self.error_code.value,
            "message": self.message,
            "status_code": self.status_code,
        }
        
        if self.details:
            result["details"] = self.details
        
        if self.original_exception:
            result["original_error"] = str(self.original_exception)
        
        return result
    
    def __str__(self) -> str:
        return f"[{self.error_code.value}] {self.message}"


# ===== 验证错误 =====

class ValidationError(GTBaseException):
    """验证错误"""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if field:
            details["field"] = field
        
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=400,
            details=details,
            **kwargs
        )


class InvalidRequestError(GTBaseException):
    """无效请求错误"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code=ErrorCode.INVALID_REQUEST,
            status_code=400,
            **kwargs
        )


class MissingRequiredFieldError(ValidationError):
    """缺少必填字段错误"""
    
    def __init__(self, field: str, **kwargs):
        super().__init__(
            message=f"Missing required field: {field}",
            field=field,
            error_code=ErrorCode.MISSING_REQUIRED_FIELD,
            **kwargs
        )


# ===== 认证/授权错误 =====

class UnauthorizedError(GTBaseException):
    """未授权错误"""
    
    def __init__(self, message: str = "Unauthorized", **kwargs):
        super().__init__(
            message=message,
            error_code=ErrorCode.UNAUTHORIZED,
            status_code=401,
            **kwargs
        )


class ForbiddenError(GTBaseException):
    """禁止访问错误"""
    
    def __init__(self, message: str = "Forbidden", **kwargs):
        super().__init__(
            message=message,
            error_code=ErrorCode.FORBIDDEN,
            status_code=403,
            **kwargs
        )


class InvalidAPIKeyError(UnauthorizedError):
    """无效API密钥错误"""
    
    def __init__(self, **kwargs):
        super().__init__(
            message="Invalid API key",
            error_code=ErrorCode.INVALID_API_KEY,
            **kwargs
        )


class RateLimitExceededError(GTBaseException):
    """速率限制超出错误"""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if retry_after:
            details["retry_after"] = retry_after
        
        super().__init__(
            message=message,
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            status_code=429,
            details=details,
            **kwargs
        )


# ===== 资源错误 =====

class ResourceNotFoundError(GTBaseException):
    """资源未找到错误"""
    
    def __init__(
        self,
        resource_type: str,
        resource_id: Optional[str] = None,
        **kwargs
    ):
        message = f"{resource_type} not found"
        if resource_id:
            message += f": {resource_id}"
        
        details = kwargs.pop("details", {})
        details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        
        super().__init__(
            message=message,
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            status_code=404,
            details=details,
            **kwargs
        )


class ResourceAlreadyExistsError(GTBaseException):
    """资源已存在错误"""
    
    def __init__(
        self,
        resource_type: str,
        resource_id: Optional[str] = None,
        **kwargs
    ):
        message = f"{resource_type} already exists"
        if resource_id:
            message += f": {resource_id}"
        
        details = kwargs.pop("details", {})
        details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        
        super().__init__(
            message=message,
            error_code=ErrorCode.RESOURCE_ALREADY_EXISTS,
            status_code=409,
            details=details,
            **kwargs
        )


# ===== Session错误 =====

class SessionNotFoundError(ResourceNotFoundError):
    """会话未找到错误"""
    
    def __init__(self, session_id: str, **kwargs):
        super().__init__(
            resource_type="Session",
            resource_id=session_id,
            error_code=ErrorCode.SESSION_NOT_FOUND,
            **kwargs
        )


class SessionExpiredError(GTBaseException):
    """会话过期错误"""
    
    def __init__(self, session_id: str, **kwargs):
        super().__init__(
            message=f"Session expired: {session_id}",
            error_code=ErrorCode.SESSION_EXPIRED,
            status_code=410,
            details={"session_id": session_id},
            **kwargs
        )


class InvalidSessionStateError(GTBaseException):
    """无效会话状态错误"""
    
    def __init__(self, message: str, session_id: Optional[str] = None, **kwargs):
        details = kwargs.pop("details", {})
        if session_id:
            details["session_id"] = session_id
        
        super().__init__(
            message=message,
            error_code=ErrorCode.INVALID_SESSION_STATE,
            status_code=400,
            details=details,
            **kwargs
        )


# ===== LLM错误 =====

class LLMAPIError(GTBaseException):
    """LLM API错误"""
    
    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if provider:
            details["provider"] = provider
        
        super().__init__(
            message=message,
            error_code=ErrorCode.LLM_API_ERROR,
            status_code=502,
            details=details,
            **kwargs
        )


class LLMTimeoutError(GTBaseException):
    """LLM超时错误"""
    
    def __init__(self, timeout: Optional[float] = None, **kwargs):
        message = "LLM request timeout"
        details = kwargs.pop("details", {})
        if timeout:
            message += f" after {timeout}s"
            details["timeout"] = timeout
        
        super().__init__(
            message=message,
            error_code=ErrorCode.LLM_TIMEOUT,
            status_code=504,
            details=details,
            **kwargs
        )


class LLMRateLimitError(GTBaseException):
    """LLM速率限制错误"""
    
    def __init__(self, retry_after: Optional[int] = None, **kwargs):
        details = kwargs.pop("details", {})
        if retry_after:
            details["retry_after"] = retry_after
        
        super().__init__(
            message="LLM API rate limit exceeded",
            error_code=ErrorCode.LLM_RATE_LIMIT,
            status_code=429,
            details=details,
            **kwargs
        )


class LLMTokenLimitExceededError(GTBaseException):
    """LLM Token限制超出错误"""
    
    def __init__(
        self,
        token_count: Optional[int] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        message = "Token limit exceeded"
        details = kwargs.pop("details", {})
        
        if token_count and max_tokens:
            message += f": {token_count}/{max_tokens}"
            details.update({
                "token_count": token_count,
                "max_tokens": max_tokens
            })
        
        super().__init__(
            message=message,
            error_code=ErrorCode.LLM_TOKEN_LIMIT_EXCEEDED,
            status_code=400,
            details=details,
            **kwargs
        )


# ===== 工具错误 =====

class ToolExecutionError(GTBaseException):
    """工具执行错误"""
    
    def __init__(
        self,
        tool_name: str,
        message: str,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        details["tool_name"] = tool_name
        
        super().__init__(
            message=f"Tool execution failed ({tool_name}): {message}",
            error_code=ErrorCode.TOOL_EXECUTION_ERROR,
            status_code=500,
            details=details,
            **kwargs
        )


class ToolNotFoundError(ResourceNotFoundError):
    """工具未找到错误"""
    
    def __init__(self, tool_name: str, **kwargs):
        super().__init__(
            resource_type="Tool",
            resource_id=tool_name,
            error_code=ErrorCode.TOOL_NOT_FOUND,
            **kwargs
        )


class ToolTimeoutError(GTBaseException):
    """工具超时错误"""
    
    def __init__(
        self,
        tool_name: str,
        timeout: Optional[float] = None,
        **kwargs
    ):
        message = f"Tool execution timeout: {tool_name}"
        details = kwargs.pop("details", {})
        details["tool_name"] = tool_name
        
        if timeout:
            message += f" after {timeout}s"
            details["timeout"] = timeout
        
        super().__init__(
            message=message,
            error_code=ErrorCode.TOOL_TIMEOUT,
            status_code=504,
            details=details,
            **kwargs
        )


# ===== 搜索错误 =====

class SearchAPIError(GTBaseException):
    """搜索API错误"""
    
    def __init__(self, message: str, provider: Optional[str] = None, **kwargs):
        details = kwargs.pop("details", {})
        if provider:
            details["provider"] = provider
        
        super().__init__(
            message=message,
            error_code=ErrorCode.SEARCH_API_ERROR,
            status_code=502,
            details=details,
            **kwargs
        )


# ===== 数据错误 =====

class DatabaseError(GTBaseException):
    """数据库错误"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code=ErrorCode.DATABASE_ERROR,
            status_code=500,
            **kwargs
        )


class CacheError(GTBaseException):
    """缓存错误"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code=ErrorCode.CACHE_ERROR,
            status_code=500,
            **kwargs
        )


class CompressionError(GTBaseException):
    """压缩错误"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code=ErrorCode.COMPRESSION_ERROR,
            status_code=500,
            **kwargs
        )

