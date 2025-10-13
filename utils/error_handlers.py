"""
统一错误处理中间件和处理器

提供FastAPI错误处理中间件、异常捕获、错误响应格式化等功能。
"""

import traceback
import sys
from typing import Union, Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .custom_exceptions import GTBaseException, ErrorCode
from .enhanced_logger import get_logger

logger = get_logger(__name__)


class ErrorResponse:
    """统一错误响应格式"""
    
    @staticmethod
    def create(
        error_code: Union[str, ErrorCode],
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        创建错误响应
        
        Args:
            error_code: 错误码
            message: 错误消息
            status_code: HTTP状态码
            details: 额外详情
            request_id: 请求ID
            path: 请求路径
        
        Returns:
            错误响应字典
        """
        response = {
            "success": False,
            "error": {
                "code": error_code.value if isinstance(error_code, ErrorCode) else error_code,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
            }
        }
        
        if details:
            response["error"]["details"] = details
        
        if request_id:
            response["error"]["request_id"] = request_id
        
        if path:
            response["error"]["path"] = path
        
        return response


async def gtplanner_exception_handler(
    request: Request,
    exc: GTBaseException
) -> JSONResponse:
    """
    GTPlanner自定义异常处理器
    
    Args:
        request: 请求对象
        exc: 异常对象
    
    Returns:
        JSON响应
    """
    # 获取请求ID（如果有）
    request_id = request.headers.get("X-Request-ID")
    
    # 记录错误日志
    logger.error(
        f"GTPlanner Exception: {exc.error_code.value}",
        extra={
            "error_code": exc.error_code.value,
            "message": exc.message,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
            "request_id": request_id,
            "details": exc.details,
        },
        exc_info=exc.original_exception if exc.original_exception else True
    )
    
    # 创建响应
    response_data = ErrorResponse.create(
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        request_id=request_id,
        path=request.url.path,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    请求验证错误处理器
    
    Args:
        request: 请求对象
        exc: 验证错误对象
    
    Returns:
        JSON响应
    """
    request_id = request.headers.get("X-Request-ID")
    
    # 提取验证错误详情
    validation_errors = []
    for error in exc.errors():
        validation_errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })
    
    # 记录错误日志
    logger.warning(
        "Validation Error",
        extra={
            "path": request.url.path,
            "method": request.method,
            "request_id": request_id,
            "validation_errors": validation_errors,
        }
    )
    
    # 创建响应
    response_data = ErrorResponse.create(
        error_code=ErrorCode.VALIDATION_ERROR,
        message="Request validation failed",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"validation_errors": validation_errors},
        request_id=request_id,
        path=request.url.path,
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_data
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> JSONResponse:
    """
    HTTP异常处理器
    
    Args:
        request: 请求对象
        exc: HTTP异常对象
    
    Returns:
        JSON响应
    """
    request_id = request.headers.get("X-Request-ID")
    
    # 记录错误日志
    logger.warning(
        f"HTTP Exception: {exc.status_code}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
            "method": request.method,
            "request_id": request_id,
        }
    )
    
    # 映射HTTP状态码到错误码
    error_code_mapping = {
        400: ErrorCode.INVALID_REQUEST,
        401: ErrorCode.UNAUTHORIZED,
        403: ErrorCode.FORBIDDEN,
        404: ErrorCode.RESOURCE_NOT_FOUND,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
        500: ErrorCode.INTERNAL_SERVER_ERROR,
        502: ErrorCode.LLM_API_ERROR,
        503: ErrorCode.SERVICE_UNAVAILABLE,
        504: ErrorCode.LLM_TIMEOUT,
    }
    
    error_code = error_code_mapping.get(
        exc.status_code,
        ErrorCode.UNKNOWN_ERROR
    )
    
    # 创建响应
    response_data = ErrorResponse.create(
        error_code=error_code,
        message=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
        status_code=exc.status_code,
        request_id=request_id,
        path=request.url.path,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    通用异常处理器（捕获所有未处理的异常）
    
    Args:
        request: 请求对象
        exc: 异常对象
    
    Returns:
        JSON响应
    """
    request_id = request.headers.get("X-Request-ID")
    
    # 获取异常详情
    exc_type = type(exc).__name__
    exc_message = str(exc)
    exc_traceback = "".join(
        traceback.format_exception(type(exc), exc, exc.__traceback__)
    )
    
    # 记录错误日志（包含完整堆栈）
    logger.critical(
        f"Unhandled Exception: {exc_type}",
        extra={
            "exception_type": exc_type,
            "exception_message": exc_message,
            "path": request.url.path,
            "method": request.method,
            "request_id": request_id,
            "traceback": exc_traceback,
        },
        exc_info=True
    )
    
    # 创建响应（生产环境不暴露详细错误）
    import os
    is_production = os.getenv("ENV", "development") == "production"
    
    if is_production:
        # 生产环境：隐藏详细信息
        response_data = ErrorResponse.create(
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            message="An internal error occurred",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            request_id=request_id,
            path=request.url.path,
        )
    else:
        # 开发环境：显示详细信息
        response_data = ErrorResponse.create(
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            message=exc_message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={
                "exception_type": exc_type,
                "traceback": exc_traceback.split("\n"),
            },
            request_id=request_id,
            path=request.url.path,
        )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data
    )


def setup_error_handlers(app: FastAPI) -> None:
    """
    设置所有错误处理器
    
    Args:
        app: FastAPI应用实例
    """
    # 注册自定义异常处理器
    app.add_exception_handler(GTBaseException, gtplanner_exception_handler)
    
    # 注册验证错误处理器
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # 注册HTTP异常处理器
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # 注册通用异常处理器（捕获所有未处理的异常）
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("Error handlers configured successfully")


class ErrorTracker:
    """错误追踪器"""
    
    def __init__(self):
        self.errors: Dict[str, int] = {}
    
    def track(self, error_code: Union[str, ErrorCode]) -> None:
        """记录错误"""
        code = error_code.value if isinstance(error_code, ErrorCode) else error_code
        self.errors[code] = self.errors.get(code, 0) + 1
    
    def get_stats(self) -> Dict[str, int]:
        """获取错误统计"""
        return self.errors.copy()
    
    def reset(self) -> None:
        """重置统计"""
        self.errors.clear()


# 全局错误追踪器
error_tracker = ErrorTracker()

