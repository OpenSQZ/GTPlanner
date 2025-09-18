"""
验证中间件

基于装饰器模式的FastAPI中间件实现，提供：
- 请求路径匹配和验证链选择
- 验证上下文创建和管理
- 并行/串行验证执行
- 验证结果处理和错误响应
- 观察者事件触发
- 性能指标收集
"""

import time
import json
from typing import Dict, Any, Optional, Callable, List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

try:
    from fastapi import Request, Response
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    Request = Any
    Response = Any

from ..core.interfaces import IValidationObserver
from ..core.validation_context import ValidationContext, ValidationMode
from ..core.validation_result import ValidationResult, ValidationStatus
from ..factories.chain_factory import ValidationChainFactory
from ..factories.config_factory import ConfigFactory


class ValidationMiddleware(BaseHTTPMiddleware):
    """请求验证中间件 - 统一处理所有请求验证
    
    这是验证系统与FastAPI的主要集成点，负责：
    - 拦截HTTP请求并创建验证上下文
    - 选择合适的验证链并执行验证
    - 处理验证结果并生成相应的HTTP响应
    - 触发观察者事件进行日志记录和指标收集
    """
    
    def __init__(self, app, config: Optional[Dict[str, Any]] = None):
        super().__init__(app)
        
        # 加载配置
        if config is None:
            config_factory = ConfigFactory()
            config = config_factory.create_from_template("standard") or {}
        
        self.config = config
        
        # 初始化组件
        self.chain_factory = ValidationChainFactory(config)
        self.observers: List[IValidationObserver] = []
        
        # 配置选项
        self.enabled = config.get("enabled", True)
        self.excluded_paths = config.get("excluded_paths", ["/health", "/metrics", "/static"])
        self.included_paths = config.get("included_paths", ["/api"])
        self.enable_parallel_validation = config.get("enable_parallel_validation", True)
        self.enable_streaming_validation = config.get("enable_streaming_validation", False)
        
        print(f"ValidationMiddleware initialized: enabled={self.enabled}")
    
    def add_observer(self, observer: IValidationObserver) -> None:
        """添加验证观察者
        
        Args:
            observer: 观察者实例
        """
        if observer not in self.observers:
            self.observers.append(observer)
    
    def remove_observer(self, observer: IValidationObserver) -> None:
        """移除验证观察者
        
        Args:
            observer: 观察者实例
        """
        if observer in self.observers:
            self.observers.remove(observer)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求验证
        
        Args:
            request: FastAPI请求对象
            call_next: 下一个中间件或路由处理器
            
        Returns:
            HTTP响应对象
        """
        # 检查是否需要验证
        if not self._should_validate(request):
            return await call_next(request)
        
        start_time = time.time()
        context = None
        
        try:
            # 创建验证上下文
            context = await self._create_validation_context(request)
            
            # 获取验证链
            validation_chain = self.chain_factory.create_chain_for_endpoint(
                request.url.path
            )
            
            if not validation_chain:
                # 没有匹配的验证链，直接通过
                return await call_next(request)
            
            # 添加流式验证观察者（如果启用）
            if self.enable_streaming_validation and hasattr(request.state, 'streaming_session'):
                context.streaming_session = request.state.streaming_session
                context.enable_streaming_validation = True
            
            # 通知验证开始
            await self._notify_validation_start(context)
            
            # 执行验证
            if self.enable_parallel_validation:
                result = await validation_chain.validate_parallel(context)
            else:
                result = await validation_chain.validate(context)
            
            # 通知验证完成
            await self._notify_validation_complete(result)
            
            # 检查验证结果
            if not result.is_valid:
                return await self._handle_validation_failure(result, context)
            
            # 将验证结果添加到请求状态
            request.state.validation_result = result
            request.state.validation_context = context
            
            # 继续处理请求
            response = await call_next(request)
            
            # 记录成功指标
            execution_time = time.time() - start_time
            await self._record_success_metrics(context, execution_time)
            
            return response
            
        except Exception as e:
            # 通知验证错误
            await self._notify_validation_error(e, context)
            
            # 记录错误指标
            execution_time = time.time() - start_time
            await self._record_error_metrics(
                request.url.path if hasattr(request, 'url') else "unknown", 
                str(e), 
                execution_time
            )
            
            # 返回内部错误
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal validation error",
                    "request_id": getattr(context, 'request_id', 'unknown') if context else 'unknown',
                    "message": "验证系统内部错误，请联系管理员"
                }
            )
    
    def _should_validate(self, request: Request) -> bool:
        """判断是否需要验证请求
        
        Args:
            request: FastAPI请求对象
            
        Returns:
            True表示需要验证，False表示跳过验证
        """
        if not self.enabled:
            return False
        
        if not hasattr(request, 'url'):
            return False
        
        path = request.url.path
        method = request.method
        
        # 检查排除路径
        for excluded_path in self.excluded_paths:
            if path.startswith(excluded_path):
                return False
        
        # 检查包含路径
        if self.included_paths:
            return any(path.startswith(included) for included in self.included_paths)
        
        # 默认验证API端点
        return path.startswith('/api/')
    
    async def _create_validation_context(self, request: Request) -> ValidationContext:
        """创建验证上下文
        
        Args:
            request: FastAPI请求对象
            
        Returns:
            验证上下文实例
        """
        # 读取请求体
        request_data = None
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                # 尝试解析JSON
                request_data = await request.json()
            except Exception:
                try:
                    # 如果JSON解析失败，读取原始数据
                    request_data = await request.body()
                    if isinstance(request_data, bytes):
                        request_data = request_data.decode('utf-8', errors='ignore')
                except Exception:
                    request_data = None
        
        # 提取用户和会话信息
        user_id = None
        session_id = None
        
        if isinstance(request_data, dict):
            user_id = request_data.get("user_id")
            session_id = request_data.get("session_id")
        
        # 创建验证上下文
        context = ValidationContext.create_from_request(
            request=request,
            request_data=request_data,
            validation_mode=ValidationMode(self.config.get("mode", "strict")),
            enable_cache=self.config.get("enable_caching", True),
            cache_ttl=self.config.get("cache_ttl", 300),
            user_id=user_id,
            session_id=session_id
        )
        
        return context
    
    async def _handle_validation_failure(
        self, 
        result: ValidationResult, 
        context: ValidationContext
    ) -> JSONResponse:
        """处理验证失败
        
        Args:
            result: 验证结果
            context: 验证上下文
            
        Returns:
            错误响应
        """
        # 确定HTTP状态码
        status_code = self._determine_status_code(result)
        
        # 格式化错误响应
        error_response = result.to_http_response()
        
        # 添加额外的响应头
        headers = {}
        if result.request_id:
            headers["X-Request-ID"] = result.request_id
        
        # 添加重试信息（如果是频率限制）
        if any(error.code.startswith('RATE_LIMIT') for error in result.errors):
            retry_after = self._extract_retry_after(result)
            if retry_after:
                headers["Retry-After"] = str(retry_after)
        
        return JSONResponse(
            status_code=status_code,
            content=error_response,
            headers=headers
        )
    
    def _determine_status_code(self, result: ValidationResult) -> int:
        """确定HTTP状态码
        
        Args:
            result: 验证结果
            
        Returns:
            HTTP状态码
        """
        # 检查是否有严重错误
        if result.has_critical_errors:
            return 403  # Forbidden
        
        # 检查特定错误类型
        for error in result.errors:
            if error.code.startswith('RATE_LIMIT'):
                return 429  # Too Many Requests
            elif error.code.startswith('SIZE') or error.code.endswith('TOO_LARGE'):
                return 413  # Payload Too Large
            elif error.code.startswith('XSS') or error.code.startswith('SQL_INJECTION'):
                return 403  # Forbidden
            elif error.code.startswith('MISSING') or error.code.startswith('INVALID_FORMAT'):
                return 422  # Unprocessable Entity
        
        # 默认错误状态码
        return 400  # Bad Request
    
    def _extract_retry_after(self, result: ValidationResult) -> Optional[int]:
        """提取重试等待时间
        
        Args:
            result: 验证结果
            
        Returns:
            重试等待时间（秒），如果没有则返回None
        """
        for error in result.errors:
            if error.code.startswith('RATE_LIMIT') and error.metadata:
                retry_after = error.metadata.get("retry_after")
                if retry_after:
                    return int(retry_after)
        return None
    
    async def _notify_validation_start(self, context: ValidationContext) -> None:
        """通知验证开始事件
        
        Args:
            context: 验证上下文
        """
        for observer in self.observers:
            try:
                await observer.on_validation_start(context)
            except Exception as e:
                # 观察者异常不应影响主流程
                print(f"Warning: Observer {observer.get_observer_name()} failed on validation start: {e}")
    
    async def _notify_validation_complete(self, result: ValidationResult) -> None:
        """通知验证完成事件
        
        Args:
            result: 验证结果
        """
        for observer in self.observers:
            try:
                await observer.on_validation_complete(result)
            except Exception as e:
                print(f"Warning: Observer {observer.get_observer_name()} failed on validation complete: {e}")
    
    async def _notify_validation_error(self, error: Exception, context: Optional[ValidationContext] = None) -> None:
        """通知验证错误事件
        
        Args:
            error: 发生的异常
            context: 验证上下文（可能为None）
        """
        for observer in self.observers:
            try:
                await observer.on_validation_error(error, context)
            except Exception as e:
                print(f"Warning: Observer {observer.get_observer_name()} failed on validation error: {e}")
    
    async def _record_success_metrics(self, context: ValidationContext, execution_time: float) -> None:
        """记录成功指标
        
        Args:
            context: 验证上下文
            execution_time: 执行时间
        """
        for observer in self.observers:
            if hasattr(observer, 'record_success'):
                try:
                    await observer.record_success(context, execution_time)
                except Exception as e:
                    print(f"Warning: Observer {observer.get_observer_name()} failed to record success: {e}")
    
    async def _record_error_metrics(self, path: str, error: str, execution_time: float) -> None:
        """记录错误指标
        
        Args:
            path: 请求路径
            error: 错误信息
            execution_time: 执行时间
        """
        for observer in self.observers:
            if hasattr(observer, 'record_error'):
                try:
                    await observer.record_error(path, error, execution_time)
                except Exception as e:
                    print(f"Warning: Observer {observer.get_observer_name()} failed to record error: {e}")


def create_validation_middleware(config: Optional[Dict[str, Any]] = None) -> Callable:
    """创建验证中间件的便捷函数
    
    Args:
        config: 验证配置
        
    Returns:
        中间件工厂函数
    """
    def middleware_factory(app):
        return ValidationMiddleware(app, config)
    
    return middleware_factory
