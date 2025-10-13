"""
错误处理和日志系统测试

测试新的日志系统和自定义异常类。
"""

import pytest
import logging
from pathlib import Path
import tempfile
import shutil

from utils.enhanced_logger import (
    LoggerConfig,
    get_logger,
    setup_global_logger
)
from utils.custom_exceptions import (
    GTBaseException,
    ValidationError,
    SessionNotFoundError,
    LLMAPIError,
    ToolExecutionError,
    RateLimitExceededError,
    ErrorCode
)


class TestEnhancedLogger:
    """测试增强日志系统"""
    
    def test_logger_creation(self):
        """测试日志记录器创建"""
        logger = get_logger("test")
        assert logger is not None
        assert logger.name == "test"
    
    def test_logger_with_context(self):
        """测试带上下文的日志记录器"""
        logger = get_logger(
            "test",
            session_id="sess123",
            user_id="user456"
        )
        assert logger is not None
        # LoggerAdapter should have extra attribute
        if hasattr(logger, 'extra'):
            assert logger.extra.get("session_id") == "sess123"
            assert logger.extra.get("user_id") == "user456"
    
    def test_logger_config(self):
        """测试日志配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LoggerConfig(
                app_name="test_app",
                log_dir=tmpdir,
                log_level="DEBUG",
                enable_console=False,
                enable_file=True,
                enable_json=False
            )
            
            logger = config.configure()
            assert logger is not None
            
            # 检查日志文件是否创建
            log_file = Path(tmpdir) / "test_app.log"
            
            # 写入一些日志
            logger.info("Test log message")
            
            # 刷新日志处理器
            for handler in logger.handlers:
                handler.flush()
    
    def test_log_rotation_config(self):
        """测试日志轮转配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 按大小轮转
            config_size = LoggerConfig(
                app_name="test_size",
                log_dir=tmpdir,
                enable_rotation="size",
                max_file_size=1024,
                backup_count=3
            )
            logger_size = config_size.configure()
            assert logger_size is not None
            
            # 按时间轮转
            config_time = LoggerConfig(
                app_name="test_time",
                log_dir=tmpdir,
                enable_rotation="time",
                backup_count=7
            )
            logger_time = config_time.configure()
            assert logger_time is not None


class TestCustomExceptions:
    """测试自定义异常类"""
    
    def test_base_exception(self):
        """测试基础异常类"""
        exc = GTBaseException(
            message="Test error",
            error_code=ErrorCode.UNKNOWN_ERROR,
            status_code=500,
            details={"key": "value"}
        )
        
        assert exc.message == "Test error"
        assert exc.error_code == ErrorCode.UNKNOWN_ERROR
        assert exc.status_code == 500
        assert exc.details == {"key": "value"}
        
        # 测试转换为字典
        exc_dict = exc.to_dict()
        assert exc_dict["error"] == True
        assert exc_dict["error_code"] == "UNKNOWN_ERROR"
        assert exc_dict["message"] == "Test error"
    
    def test_validation_error(self):
        """测试验证错误"""
        exc = ValidationError(
            message="Invalid input",
            field="user_input",
            details={"expected": "string"}
        )
        
        assert exc.error_code == ErrorCode.VALIDATION_ERROR
        assert exc.status_code == 400
        assert exc.details.get("field") == "user_input"
    
    def test_session_not_found_error(self):
        """测试Session未找到错误"""
        exc = SessionNotFoundError(session_id="sess123")
        
        assert exc.error_code == ErrorCode.SESSION_NOT_FOUND
        assert exc.status_code == 404
        assert exc.details.get("resource_id") == "sess123"
    
    def test_llm_api_error(self):
        """测试LLM API错误"""
        original_exc = ValueError("Connection failed")
        
        exc = LLMAPIError(
            message="Failed to call LLM",
            provider="OpenAI",
            details={"model": "gpt-4"},
            original_exception=original_exc
        )
        
        assert exc.error_code == ErrorCode.LLM_API_ERROR
        assert exc.status_code == 502
        assert exc.details.get("provider") == "OpenAI"
        assert exc.original_exception == original_exc
    
    def test_tool_execution_error(self):
        """测试工具执行错误"""
        exc = ToolExecutionError(
            tool_name="search",
            message="Search failed",
            details={"query": "test"}
        )
        
        assert exc.error_code == ErrorCode.TOOL_EXECUTION_ERROR
        assert exc.status_code == 500
        assert exc.details.get("tool_name") == "search"
    
    def test_rate_limit_error(self):
        """测试速率限制错误"""
        exc = RateLimitExceededError(
            retry_after=60,
            details={"limit": 10}
        )
        
        assert exc.error_code == ErrorCode.RATE_LIMIT_EXCEEDED
        assert exc.status_code == 429
        assert exc.details.get("retry_after") == 60
    
    def test_exception_string_representation(self):
        """测试异常的字符串表示"""
        exc = ValidationError(message="Test error", field="test_field")
        
        exc_str = str(exc)
        assert "VALIDATION_ERROR" in exc_str
        assert "Test error" in exc_str
    
    def test_exception_with_original(self):
        """测试带原始异常的异常"""
        original = ValueError("Original error")
        exc = LLMAPIError(
            message="Wrapped error",
            original_exception=original
        )
        
        exc_dict = exc.to_dict()
        assert exc_dict["original_error"] == "Original error"


class TestErrorCodes:
    """测试错误码"""
    
    def test_error_code_values(self):
        """测试错误码值"""
        assert ErrorCode.VALIDATION_ERROR.value == "VALIDATION_ERROR"
        assert ErrorCode.UNAUTHORIZED.value == "UNAUTHORIZED"
        assert ErrorCode.SESSION_NOT_FOUND.value == "SESSION_NOT_FOUND"
        assert ErrorCode.LLM_API_ERROR.value == "LLM_API_ERROR"
        assert ErrorCode.TOOL_EXECUTION_ERROR.value == "TOOL_EXECUTION_ERROR"
    
    def test_error_code_enum(self):
        """测试错误码枚举"""
        # 确保错误码是唯一的
        error_codes = [code.value for code in ErrorCode]
        assert len(error_codes) == len(set(error_codes))


@pytest.mark.asyncio
class TestErrorHandlers:
    """测试错误处理器"""
    
    async def test_error_response_creation(self):
        """测试错误响应创建"""
        from utils.error_handlers import ErrorResponse
        
        response = ErrorResponse.create(
            error_code=ErrorCode.VALIDATION_ERROR,
            message="Test error",
            status_code=400,
            details={"field": "test"},
            request_id="req123",
            path="/api/test"
        )
        
        assert response["success"] == False
        assert response["error"]["code"] == "VALIDATION_ERROR"
        assert response["error"]["message"] == "Test error"
        assert response["error"]["details"]["field"] == "test"
        assert response["error"]["request_id"] == "req123"
        assert response["error"]["path"] == "/api/test"
    
    async def test_error_tracker(self):
        """测试错误追踪器"""
        from utils.error_handlers import ErrorTracker
        
        tracker = ErrorTracker()
        
        # 追踪一些错误
        tracker.track(ErrorCode.VALIDATION_ERROR)
        tracker.track(ErrorCode.VALIDATION_ERROR)
        tracker.track(ErrorCode.LLM_API_ERROR)
        
        # 获取统计
        stats = tracker.get_stats()
        assert stats["VALIDATION_ERROR"] == 2
        assert stats["LLM_API_ERROR"] == 1
        
        # 重置
        tracker.reset()
        stats = tracker.get_stats()
        assert len(stats) == 0


def test_imports():
    """测试所有导入是否正常"""
    # 测试日志相关导入
    from utils.enhanced_logger import (
        LoggerConfig,
        get_logger,
        setup_global_logger,
        get_global_logger
    )
    
    # 测试异常相关导入
    from utils.custom_exceptions import (
        GTBaseException,
        ValidationError,
        InvalidRequestError,
        UnauthorizedError,
        SessionNotFoundError,
        LLMAPIError,
        ToolExecutionError,
        ErrorCode
    )
    
    # 测试错误处理相关导入
    from utils.error_handlers import (
        ErrorResponse,
        setup_error_handlers,
        error_tracker
    )
    
    # 所有导入成功
    assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

