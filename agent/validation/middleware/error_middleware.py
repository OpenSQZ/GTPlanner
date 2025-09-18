"""
错误处理中间件

基于装饰器模式的错误处理中间件，提供：
- 验证异常捕获和处理
- 错误响应格式化
- 错误日志记录
- 错误指标收集
- 流式错误事件发送
"""

import time
import traceback
from typing import Dict, Any, Optional, Callable, List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

try:
    from fastapi import Request, Response, HTTPException
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    Request = Any
    Response = Any
    HTTPException = Exception

from ..core.interfaces import IValidationObserver
from ..core.validation_result import ValidationError, ValidationResult, ValidationStatus, ValidationSeverity


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """错误处理中间件 - 统一处理验证和应用错误
    
    负责捕获和处理验证过程中的各种异常，提供：
    - 验证异常的统一处理
    - 应用异常的优雅降级
    - 错误响应的标准化格式
    - 错误事件的观察者通知
    """
    
    def __init__(self, app, config: Optional[Dict[str, Any]] = None):
        super().__init__(app)
        self.config = config or {}
        self.observers: List[IValidationObserver] = []
        
        # 错误处理配置
        self.include_error_details = self.config.get("include_error_details", True)
        self.include_stack_trace = self.config.get("include_stack_trace", False)
        self.mask_sensitive_data = self.config.get("mask_sensitive_data", True)
        self.max_error_message_length = self.config.get("max_error_message_length", 500)
        
        print(f"ErrorHandlingMiddleware initialized")
    
    def add_observer(self, observer: IValidationObserver) -> None:
        """添加错误观察者
        
        Args:
            observer: 观察者实例
        """
        if observer not in self.observers:
            self.observers.append(observer)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求和错误
        
        Args:
            request: FastAPI请求对象
            call_next: 下一个中间件或路由处理器
            
        Returns:
            HTTP响应对象
        """
        start_time = time.time()
        
        try:
            # 正常处理请求
            response = await call_next(request)
            return response
            
        except HTTPException as http_exc:
            # FastAPI HTTP异常
            execution_time = time.time() - start_time
            return await self._handle_http_exception(http_exc, request, execution_time)
            
        except Exception as exc:
            # 其他异常
            execution_time = time.time() - start_time
            return await self._handle_general_exception(exc, request, execution_time)
    
    async def _handle_http_exception(
        self, 
        http_exc: HTTPException, 
        request: Request, 
        execution_time: float
    ) -> JSONResponse:
        """处理HTTP异常
        
        Args:
            http_exc: HTTP异常
            request: 请求对象
            execution_time: 执行时间
            
        Returns:
            JSON错误响应
        """
        # 创建标准化的错误响应
        error_response = {
            "success": False,
            "error": "HTTP_ERROR",
            "status_code": http_exc.status_code,
            "message": str(http_exc.detail),
            "path": request.url.path if hasattr(request, 'url') else "unknown",
            "method": request.method if hasattr(request, 'method') else "unknown",
            "execution_time": round(execution_time, 3)
        }
        
        # 添加请求ID（如果可用）
        if hasattr(request.state, 'validation_context'):
            context = request.state.validation_context
            if context and context.request_id:
                error_response["request_id"] = context.request_id
        
        # 通知观察者
        await self._notify_error_observers(http_exc, request, execution_time)
        
        return JSONResponse(
            status_code=http_exc.status_code,
            content=error_response
        )
    
    async def _handle_general_exception(
        self, 
        exc: Exception, 
        request: Request, 
        execution_time: float
    ) -> JSONResponse:
        """处理一般异常
        
        Args:
            exc: 异常对象
            request: 请求对象
            execution_time: 执行时间
            
        Returns:
            JSON错误响应
        """
        # 生成请求ID
        request_id = f"error_{int(time.time() * 1000)}"
        
        # 截断错误消息
        error_message = str(exc)
        if len(error_message) > self.max_error_message_length:
            error_message = error_message[:self.max_error_message_length] + "..."
        
        # 创建错误响应
        error_response = {
            "success": False,
            "error": "INTERNAL_ERROR",
            "message": "内部服务器错误" if self.mask_sensitive_data else error_message,
            "request_id": request_id,
            "path": request.url.path if hasattr(request, 'url') else "unknown",
            "method": request.method if hasattr(request, 'method') else "unknown",
            "execution_time": round(execution_time, 3)
        }
        
        # 添加错误详情（如果启用）
        if self.include_error_details and not self.mask_sensitive_data:
            error_response["error_type"] = type(exc).__name__
            error_response["error_details"] = error_message
        
        # 添加堆栈跟踪（如果启用且非生产环境）
        if self.include_stack_trace and not self.mask_sensitive_data:
            error_response["stack_trace"] = traceback.format_exc().split('\n')
        
        # 通知观察者
        await self._notify_error_observers(exc, request, execution_time)
        
        return JSONResponse(
            status_code=500,
            content=error_response
        )
    
    async def _notify_error_observers(self, error: Exception, request: Request, execution_time: float) -> None:
        """通知错误观察者
        
        Args:
            error: 异常对象
            request: 请求对象
            execution_time: 执行时间
        """
        # 创建简化的验证上下文
        context = None
        if hasattr(request.state, 'validation_context'):
            context = request.state.validation_context
        
        for observer in self.observers:
            try:
                await observer.on_validation_error(error, context)
                
                # 如果观察者支持错误记录
                if hasattr(observer, 'record_error'):
                    path = request.url.path if hasattr(request, 'url') else "unknown"
                    await observer.record_error(path, str(error), execution_time)
                    
            except Exception as obs_error:
                # 观察者异常不应影响错误处理
                print(f"Warning: Observer {observer.get_observer_name()} failed on error notification: {obs_error}")


def create_error_middleware(config: Optional[Dict[str, Any]] = None) -> Callable:
    """创建错误处理中间件的便捷函数
    
    Args:
        config: 错误处理配置
        
    Returns:
        中间件工厂函数
    """
    def middleware_factory(app):
        return ErrorHandlingMiddleware(app, config)
    
    return middleware_factory
