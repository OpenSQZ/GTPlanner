"""
FastAPI验证适配器

基于适配器模式的FastAPI集成，提供：
- FastAPI Request对象适配
- HTTP状态码映射
- 响应格式适配
- 中间件集成适配
"""

from typing import Dict, Any, Optional, List, Callable
from ..core.interfaces import IValidationStrategy
from ..core.validation_context import ValidationContext, ValidationMode
from ..core.validation_result import (
    ValidationResult, ValidationError, ValidationStatus, ValidationSeverity
)

# 尝试导入FastAPI
try:
    from fastapi import Request, Response, HTTPException, status
    from starlette.responses import JSONResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    Request = Any
    Response = Any
    HTTPException = Exception
    status = None


class FastAPIValidationAdapter:
    """FastAPI验证适配器 - 与FastAPI系统的深度集成
    
    提供FastAPI特定的验证功能：
    - Request对象的深度解析
    - HTTP状态码的智能映射
    - 响应格式的标准化
    - 中间件的无缝集成
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.enable_request_validation = self.config.get("enable_request_validation", True)
        self.enable_response_enhancement = self.config.get("enable_response_enhancement", True)
        self.include_debug_info = self.config.get("include_debug_info", False)
        
        if not FASTAPI_AVAILABLE:
            print("Warning: FastAPI not available, adapter will be limited")
    
    async def create_context_from_request(self, request: Request, **kwargs) -> ValidationContext:
        """从FastAPI Request创建验证上下文
        
        Args:
            request: FastAPI Request对象
            **kwargs: 额外的上下文参数
            
        Returns:
            验证上下文实例
        """
        # 提取请求数据
        request_data = await self._extract_request_data(request)
        
        # 提取用户和会话信息
        user_id, session_id = self._extract_user_session_info(request, request_data)
        
        # 创建验证上下文
        context = ValidationContext.create_from_request(
            request=request,
            request_data=request_data,
            user_id=user_id,
            session_id=session_id,
            **kwargs
        )
        
        # 添加FastAPI特定的元数据
        context.add_metadata("fastapi_request", True)
        context.add_metadata("request_size", len(str(request_data)) if request_data else 0)
        
        return context
    
    async def _extract_request_data(self, request: Request) -> Optional[Any]:
        """提取请求数据
        
        Args:
            request: FastAPI Request对象
            
        Returns:
            请求数据，如果提取失败则返回None
        """
        if not FASTAPI_AVAILABLE or not request:
            return None
        
        try:
            # 检查Content-Type
            content_type = request.headers.get("content-type", "")
            
            if "application/json" in content_type:
                # JSON数据
                return await request.json()
            elif "application/x-www-form-urlencoded" in content_type:
                # 表单数据
                form_data = await request.form()
                return dict(form_data)
            elif "multipart/form-data" in content_type:
                # 多部分表单数据
                form_data = await request.form()
                return dict(form_data)
            else:
                # 原始数据
                body = await request.body()
                if body:
                    try:
                        return body.decode('utf-8')
                    except UnicodeDecodeError:
                        return body
                return None
                
        except Exception as e:
            print(f"Warning: Failed to extract request data: {e}")
            return None
    
    def _extract_user_session_info(self, request: Request, request_data: Any) -> tuple[Optional[str], Optional[str]]:
        """提取用户和会话信息
        
        Args:
            request: FastAPI Request对象
            request_data: 请求数据
            
        Returns:
            (用户ID, 会话ID)
        """
        user_id = None
        session_id = None
        
        # 从请求数据中提取
        if isinstance(request_data, dict):
            user_id = request_data.get("user_id")
            session_id = request_data.get("session_id")
        
        # 从请求头中提取
        if FASTAPI_AVAILABLE and request:
            if not user_id:
                user_id = request.headers.get("X-User-ID")
            if not session_id:
                session_id = request.headers.get("X-Session-ID")
        
        # 从查询参数中提取
        if FASTAPI_AVAILABLE and request and hasattr(request, 'query_params'):
            if not user_id:
                user_id = request.query_params.get("user_id")
            if not session_id:
                session_id = request.query_params.get("session_id")
        
        return user_id, session_id
    
    def map_validation_result_to_http_status(self, result: ValidationResult) -> int:
        """将验证结果映射为HTTP状态码
        
        Args:
            result: 验证结果
            
        Returns:
            HTTP状态码
        """
        if result.is_valid:
            return 200  # OK
        
        # 检查是否有严重错误
        if result.has_critical_errors:
            return 403  # Forbidden
        
        # 根据错误类型映射状态码
        status_code_mapping = {
            "XSS_DETECTED": 403,
            "SQL_INJECTION_DETECTED": 403,
            "MALICIOUS_SCRIPT_DETECTED": 403,
            "RATE_LIMIT": 429,
            "SIZE_LIMIT_EXCEEDED": 413,
            "STRING_LENGTH_EXCEEDED": 413,
            "ARRAY_LENGTH_EXCEEDED": 413,
            "JSON_DEPTH_EXCEEDED": 413,
            "MISSING_REQUIRED_FIELDS": 422,
            "INVALID_FORMAT": 422,
            "INVALID_MESSAGE_ROLE": 422,
            "MISSING_FIELD": 422,
            "INVALID_TYPE": 422,
            "INVALID_SESSION_ID_FORMAT": 422,
            "MISSING_SESSION_ID": 422,
            "UNSUPPORTED_LANGUAGE": 422,
            "INVALID_CONTENT_TYPE": 415,
            "MISSING_CONTENT_TYPE": 400
        }
        
        # 查找匹配的错误代码
        for error in result.errors:
            for error_pattern, status_code in status_code_mapping.items():
                if error.code.startswith(error_pattern):
                    return status_code
        
        # 默认错误状态码
        return 400  # Bad Request
    
    def create_http_response(self, result: ValidationResult, context: Optional[ValidationContext] = None) -> JSONResponse:
        """创建HTTP响应
        
        Args:
            result: 验证结果
            context: 验证上下文
            
        Returns:
            JSONResponse对象
        """
        if not FASTAPI_AVAILABLE:
            # 如果FastAPI不可用，返回简化响应
            return {"status": "error", "message": "FastAPI not available"}
        
        # 确定状态码
        status_code = self.map_validation_result_to_http_status(result)
        
        # 格式化响应内容
        content = result.to_http_response()
        
        # 添加FastAPI特定的信息
        if self.include_debug_info and context:
            content["debug_info"] = {
                "request_path": context.request_path,
                "request_method": context.request_method,
                "validation_mode": context.validation_mode.value,
                "execution_time": result.execution_time
            }
        
        # 设置响应头
        headers = {}
        if result.request_id:
            headers["X-Request-ID"] = result.request_id
        
        # 添加CORS头（如果需要）
        if self.config.get("enable_cors_headers", True):
            headers.update({
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Request-ID"
            })
        
        # 添加缓存控制头
        if not result.is_valid:
            headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        
        # 添加重试信息（如果是频率限制）
        retry_after = self._extract_retry_after(result)
        if retry_after:
            headers["Retry-After"] = str(retry_after)
        
        return JSONResponse(
            status_code=status_code,
            content=content,
            headers=headers
        )
    
    def _extract_retry_after(self, result: ValidationResult) -> Optional[int]:
        """提取重试等待时间
        
        Args:
            result: 验证结果
            
        Returns:
            重试等待时间（秒）
        """
        for error in result.errors:
            if error.code.startswith("RATE_LIMIT") and error.metadata:
                retry_after = error.metadata.get("retry_after")
                if retry_after:
                    return int(retry_after)
        return None
    
    def enhance_request_state(self, request: Request, result: ValidationResult, context: ValidationContext) -> None:
        """增强请求状态信息
        
        Args:
            request: FastAPI Request对象
            result: 验证结果
            context: 验证上下文
        """
        if not FASTAPI_AVAILABLE or not hasattr(request, 'state'):
            return
        
        # 添加验证相关的状态信息
        request.state.validation_result = result
        request.state.validation_context = context
        request.state.validation_passed = result.is_valid
        request.state.validation_execution_time = result.execution_time
        
        # 添加用户和会话信息
        if context.user_id:
            request.state.user_id = context.user_id
        if context.session_id:
            request.state.session_id = context.session_id
        
        # 添加语言信息
        request.state.detected_language = context.detected_language
        request.state.language_preference = context.get_language_preference()
    
    def create_validation_exception(self, result: ValidationResult) -> HTTPException:
        """创建验证异常
        
        Args:
            result: 验证结果
            
        Returns:
            HTTPException实例
        """
        if not FASTAPI_AVAILABLE:
            return Exception("Validation failed")
        
        status_code = self.map_validation_result_to_http_status(result)
        detail = result.to_http_response()
        
        return HTTPException(
            status_code=status_code,
            detail=detail
        )
    
    def get_request_info(self, request: Request) -> Dict[str, Any]:
        """获取请求信息摘要
        
        Args:
            request: FastAPI Request对象
            
        Returns:
            请求信息字典
        """
        if not FASTAPI_AVAILABLE or not request:
            return {}
        
        info = {
            "method": request.method,
            "path": str(request.url.path),
            "query_params": dict(request.query_params) if hasattr(request, 'query_params') else {},
            "headers": dict(request.headers),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "content_type": request.headers.get("content-type"),
            "content_length": request.headers.get("content-length")
        }
        
        # 过滤敏感头部信息
        sensitive_headers = ["authorization", "cookie", "x-api-key"]
        for header in sensitive_headers:
            if header in info["headers"]:
                info["headers"][header] = "[REDACTED]"
        
        return info


class FastAPIResponseEnhancer:
    """FastAPI响应增强器 - 增强API响应的验证信息"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.include_validation_info = self.config.get("include_validation_info", False)
        self.include_performance_info = self.config.get("include_performance_info", False)
    
    def enhance_success_response(self, response: Response, result: ValidationResult, context: ValidationContext) -> Response:
        """增强成功响应
        
        Args:
            response: 原始响应
            result: 验证结果
            context: 验证上下文
            
        Returns:
            增强后的响应
        """
        if not FASTAPI_AVAILABLE:
            return response
        
        # 添加验证相关的响应头
        if self.include_validation_info:
            response.headers["X-Validation-Status"] = result.status.value
            response.headers["X-Validation-Time"] = f"{result.execution_time:.3f}"
            
            if result.request_id:
                response.headers["X-Request-ID"] = result.request_id
        
        # 添加性能信息
        if self.include_performance_info:
            response.headers["X-Validators-Executed"] = str(result.metrics.executed_validators)
            response.headers["X-Cache-Hit-Rate"] = f"{result.metrics.get_cache_hit_rate():.2f}"
        
        # 添加语言信息
        if context.detected_language:
            response.headers["X-Detected-Language"] = context.detected_language
        
        return response
    
    def create_validation_failed_response(self, result: ValidationResult, context: Optional[ValidationContext] = None) -> JSONResponse:
        """创建验证失败响应
        
        Args:
            result: 验证结果
            context: 验证上下文
            
        Returns:
            验证失败的JSONResponse
        """
        adapter = FastAPIValidationAdapter(self.config)
        return adapter.create_http_response(result, context)


class FastAPIIntegrationHelper:
    """FastAPI集成助手 - 提供集成相关的辅助功能"""
    
    @staticmethod
    def add_validation_middleware(app, config: Optional[Dict[str, Any]] = None) -> None:
        """添加验证中间件到FastAPI应用
        
        Args:
            app: FastAPI应用实例
            config: 验证配置
        """
        if not FASTAPI_AVAILABLE:
            print("Warning: FastAPI not available, cannot add middleware")
            return
        
        try:
            from ..middleware.validation_middleware import ValidationMiddleware
            from ..middleware.error_middleware import ErrorHandlingMiddleware
            
            # 添加错误处理中间件（先添加，后执行）
            app.add_middleware(ErrorHandlingMiddleware, config=config)
            
            # 添加验证中间件
            app.add_middleware(ValidationMiddleware, config=config)
            
            print("✅ 验证中间件已添加到FastAPI应用")
            
        except Exception as e:
            print(f"❌ 添加验证中间件失败: {e}")
    
    @staticmethod
    def add_validation_observers(middleware, config: Optional[Dict[str, Any]] = None) -> None:
        """添加验证观察者到中间件
        
        Args:
            middleware: 验证中间件实例
            config: 观察者配置
        """
        try:
            from ..observers.logging_observer import LoggingObserver
            from ..observers.metrics_observer import MetricsObserver
            from ..observers.streaming_observer import StreamingObserver
            
            observer_config = config or {}
            
            # 添加日志观察者
            if observer_config.get("enable_logging", True):
                logging_observer = LoggingObserver(observer_config.get("logging", {}))
                middleware.add_observer(logging_observer)
                print("✅ 日志观察者已添加")
            
            # 添加指标观察者
            if observer_config.get("enable_metrics", True):
                metrics_observer = MetricsObserver(observer_config.get("metrics", {}))
                middleware.add_observer(metrics_observer)
                print("✅ 指标观察者已添加")
            
            # 流式观察者将在运行时动态添加（基于请求状态）
            
        except Exception as e:
            print(f"❌ 添加验证观察者失败: {e}")
    
    @staticmethod
    def create_validation_endpoint(app, path: str = "/api/validation/status") -> None:
        """创建验证状态端点
        
        Args:
            app: FastAPI应用实例
            path: 端点路径
        """
        if not FASTAPI_AVAILABLE:
            return
        
        @app.get(path)
        async def get_validation_status():
            """获取验证系统状态"""
            try:
                from ..factories.config_factory import ConfigFactory
                from ..factories.chain_factory import ValidationChainFactory
                
                config_factory = ConfigFactory()
                validation_config = config_factory.create_from_template("standard")
                
                chain_factory = ValidationChainFactory(validation_config)
                factory_stats = chain_factory.get_factory_stats()
                
                return {
                    "status": "active",
                    "version": "1.0.0",
                    "config_valid": True,
                    "available_validators": factory_stats["validator_factory_stats"]["available_validators"],
                    "configured_endpoints": factory_stats["configured_endpoints"],
                    "cache_stats": factory_stats["cached_chains"]
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e)
                }
        
        print(f"✅ 验证状态端点已创建: {path}")
    
    @staticmethod
    def create_metrics_endpoint(app, path: str = "/api/validation/metrics") -> None:
        """创建指标端点
        
        Args:
            app: FastAPI应用实例
            path: 端点路径
        """
        if not FASTAPI_AVAILABLE:
            return
        
        # 这里需要访问全局的指标观察者实例
        # 在实际集成时，可以通过依赖注入或全局变量访问
        
        @app.get(path)
        async def get_validation_metrics():
            """获取验证指标"""
            return {
                "message": "指标端点已创建，需要集成指标观察者实例",
                "endpoint": path
            }
        
        print(f"✅ 验证指标端点已创建: {path}")


def create_fastapi_adapter(config: Optional[Dict[str, Any]] = None) -> FastAPIValidationAdapter:
    """创建FastAPI适配器的便捷函数
    
    Args:
        config: 适配器配置
        
    Returns:
        FastAPI适配器实例
    """
    return FastAPIValidationAdapter(config)


def setup_fastapi_validation(app, config: Optional[Dict[str, Any]] = None) -> None:
    """设置FastAPI验证系统的便捷函数
    
    Args:
        app: FastAPI应用实例
        config: 验证配置
    """
    if not FASTAPI_AVAILABLE:
        print("Warning: FastAPI not available, validation setup skipped")
        return
    
    print("🚀 设置GTPlanner验证系统...")
    
    # 添加中间件
    FastAPIIntegrationHelper.add_validation_middleware(app, config)
    
    # 创建状态端点
    FastAPIIntegrationHelper.create_validation_endpoint(app)
    FastAPIIntegrationHelper.create_metrics_endpoint(app)
    
    print("✅ GTPlanner验证系统设置完成")
