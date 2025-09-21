"""
统一错误处理系统测试
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch

# 添加项目根目录到 Python 路径
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.error_handler import (
    UnifiedErrorHandler,
    ErrorContext,
    ErrorSeverity,
    ErrorRecoveryStrategy,
    unified_error_handler,
    get_error_handler,
    reset_error_handler
)


class TestErrorContext:
    """ErrorContext 测试类"""

    def test_error_context_creation(self):
        """测试错误上下文创建"""
        context = ErrorContext(
            source="test_module",
            error_message="Test error",
            error_type="TestError",
            timestamp=time.time(),
            severity=ErrorSeverity.HIGH
        )
        
        assert context.source == "test_module"
        assert context.error_message == "Test error"
        assert context.error_type == "TestError"
        assert context.severity == ErrorSeverity.HIGH
        assert context.metadata == {}
        assert context.traceback_info is None


class TestUnifiedErrorHandler:
    """UnifiedErrorHandler 测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        reset_error_handler()
        self.handler = UnifiedErrorHandler()
        self.shared = {}

    def test_record_error_with_string(self):
        """测试记录字符串错误"""
        error_context = self.handler.record_error(
            shared=self.shared,
            source="test_source",
            error="Test error message",
            severity=ErrorSeverity.MEDIUM
        )
        
        assert error_context.source == "test_source"
        assert error_context.error_message == "Test error message"
        assert error_context.error_type == "CustomError"
        assert error_context.severity == ErrorSeverity.MEDIUM
        
        # 检查共享状态
        assert "errors" in self.shared
        assert len(self.shared["errors"]) == 1
        assert self.shared["errors"][0]["source"] == "test_source"

    def test_record_error_with_exception(self):
        """测试记录异常错误"""
        test_exception = ValueError("Test exception")
        
        error_context = self.handler.record_error(
            shared=self.shared,
            source="test_source",
            error=test_exception,
            severity=ErrorSeverity.HIGH
        )
        
        assert error_context.error_type == "ValueError"
        assert error_context.error_message == "Test exception"
        assert error_context.traceback_info is not None

    def test_error_history_management(self):
        """测试错误历史管理"""
        # 记录多个错误
        for i in range(5):
            self.handler.record_error(
                shared=self.shared,
                source=f"test_source_{i}",
                error=f"Error {i}",
                severity=ErrorSeverity.LOW
            )
        
        assert len(self.handler.error_history) == 5
        
        # 测试历史大小限制
        self.handler.max_history_size = 3
        for i in range(5, 8):
            self.handler.record_error(
                shared=self.shared,
                source=f"test_source_{i}",
                error=f"Error {i}",
                severity=ErrorSeverity.LOW
            )
        
        assert len(self.handler.error_history) == 3

    def test_get_error_summary(self):
        """测试获取错误摘要"""
        # 记录不同严重程度的错误
        self.handler.record_error(self.shared, "source1", "Error 1", ErrorSeverity.LOW)
        self.handler.record_error(self.shared, "source2", "Error 2", ErrorSeverity.MEDIUM)
        self.handler.record_error(self.shared, "source3", "Error 3", ErrorSeverity.HIGH)
        
        summary = self.handler.get_error_summary()
        
        assert summary["total_errors"] == 3
        assert summary["by_severity"]["low"] == 1
        assert summary["by_severity"]["medium"] == 1
        assert summary["by_severity"]["high"] == 1
        assert len(summary["recent_errors"]) == 3

    def test_get_error_summary_with_session_filter(self):
        """测试按会话ID过滤错误摘要"""
        # 记录不同会话的错误
        self.handler.record_error(self.shared, "source1", "Error 1", session_id="session1")
        self.handler.record_error(self.shared, "source2", "Error 2", session_id="session2")
        self.handler.record_error(self.shared, "source3", "Error 3", session_id="session1")
        
        summary = self.handler.get_error_summary(session_id="session1")
        
        assert summary["total_errors"] == 2
        assert len(summary["recent_errors"]) == 2


class TestUnifiedErrorHandlerDecorator:
    """统一错误处理装饰器测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        reset_error_handler()

    @pytest.mark.asyncio
    async def test_async_function_success(self):
        """测试异步函数成功执行"""
        @unified_error_handler(source="test_async")
        async def test_async_func(shared):
            return "success"
        
        shared = {}
        result = await test_async_func(shared)
        assert result == "success"
        assert "errors" not in shared

    @pytest.mark.asyncio
    async def test_async_function_error_fail_fast(self):
        """测试异步函数错误处理 - 快速失败"""
        @unified_error_handler(
            source="test_async",
            recovery_strategy=ErrorRecoveryStrategy.FAIL_FAST
        )
        async def test_async_func(shared):
            raise ValueError("Test error")
        
        shared = {}
        with pytest.raises(ValueError, match="Test error"):
            await test_async_func(shared)
        
        assert "errors" in shared
        assert len(shared["errors"]) == 1

    @pytest.mark.asyncio
    async def test_async_function_error_fallback(self):
        """测试异步函数错误处理 - 备用方案"""
        @unified_error_handler(
            source="test_async",
            recovery_strategy=ErrorRecoveryStrategy.FALLBACK,
            fallback_value="fallback_result"
        )
        async def test_async_func(shared):
            raise ValueError("Test error")
        
        shared = {}
        result = await test_async_func(shared)
        assert result == "fallback_result"
        assert "errors" in shared

    @pytest.mark.asyncio
    async def test_async_function_error_graceful_degradation(self):
        """测试异步函数错误处理 - 优雅降级"""
        @unified_error_handler(
            source="test_async",
            recovery_strategy=ErrorRecoveryStrategy.GRACEFUL_DEGRADATION
        )
        async def test_async_func(shared):
            raise ValueError("Test error")
        
        shared = {}
        result = await test_async_func(shared)
        assert result["success"] is False
        assert result["fallback"] is True
        assert "Test error" in result["error"]

    def test_sync_function_success(self):
        """测试同步函数成功执行"""
        @unified_error_handler(source="test_sync")
        def test_sync_func(shared):
            return "success"
        
        shared = {}
        result = test_sync_func(shared)
        assert result == "success"
        assert "errors" not in shared

    def test_sync_function_error_ignore(self):
        """测试同步函数错误处理 - 忽略错误"""
        @unified_error_handler(
            source="test_sync",
            recovery_strategy=ErrorRecoveryStrategy.IGNORE,
            fallback_value="ignored"
        )
        def test_sync_func(shared):
            raise ValueError("Test error")
        
        shared = {}
        result = test_sync_func(shared)
        assert result == "ignored"
        assert "errors" in shared

    def test_function_without_shared_dict(self):
        """测试没有shared字典的函数"""
        @unified_error_handler(
            source="test_no_shared",
            recovery_strategy=ErrorRecoveryStrategy.GRACEFUL_DEGRADATION
        )
        def test_func():
            raise ValueError("Test error")
        
        result = test_func()
        assert result["success"] is False
        assert result["fallback"] is True


class TestGlobalErrorHandler:
    """全局错误处理器测试类"""

    def test_get_error_handler_singleton(self):
        """测试全局错误处理器单例模式"""
        reset_error_handler()
        
        handler1 = get_error_handler()
        handler2 = get_error_handler()
        
        assert handler1 is handler2

    def test_reset_error_handler(self):
        """测试重置全局错误处理器"""
        handler1 = get_error_handler()
        reset_error_handler()
        handler2 = get_error_handler()
        
        assert handler1 is not handler2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
