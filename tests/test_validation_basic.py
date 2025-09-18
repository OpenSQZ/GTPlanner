"""
验证系统基础测试

测试阶段一实现的核心功能：
- 验证上下文创建和使用
- 验证结果处理
- 配置系统集成
- 基础验证器功能
"""

import pytest
import asyncio
from datetime import datetime

# 导入验证系统组件
from agent.validation.core.validation_context import ValidationContext, ValidationMode
from agent.validation.core.validation_result import (
    ValidationResult, ValidationError, ValidationSeverity, ValidationStatus
)
from agent.validation.core.base_validator import BaseValidator
from agent.validation.core.interfaces import ValidatorPriority
from agent.validation.config.validation_config import ValidationConfig, get_validation_config


class TestValidationContext:
    """验证上下文测试"""
    
    def test_create_context_for_testing(self):
        """测试创建测试用验证上下文"""
        request_data = {"test": "data"}
        
        context = ValidationContext.create_for_testing(
            request_data=request_data,
            validation_mode=ValidationMode.STRICT,
            user_id="test_user"
        )
        
        assert context.request_data == request_data
        assert context.validation_mode == ValidationMode.STRICT
        assert context.user_id == "test_user"
        assert context.request_method == "POST"
        assert context.request_path == "/api/test"
        assert not context.enable_cache  # 测试时默认禁用缓存
    
    def test_context_language_preference(self):
        """测试语言偏好获取"""
        context = ValidationContext.create_for_testing()
        
        # 默认语言
        assert context.get_language_preference() == "en"
        
        # 设置检测到的语言
        context.detected_language = "zh"
        assert context.get_language_preference() == "zh"
        
        # 显式设置语言（优先级最高）
        context.language = "fr"
        assert context.get_language_preference() == "fr"
    
    def test_context_user_identifier(self):
        """测试用户标识符获取"""
        context = ValidationContext.create_for_testing()
        
        # 默认匿名用户
        assert context.get_user_identifier() == "anonymous"
        
        # 设置用户ID
        context.user_id = "user123"
        assert context.get_user_identifier() == "user123"
        
        # 设置会话ID（用户ID优先）
        context.session_id = "session456"
        assert context.get_user_identifier() == "user123"
        
        # 清除用户ID，使用会话ID
        context.user_id = None
        assert context.get_user_identifier() == "session456"
    
    def test_should_skip_validator(self):
        """测试验证器跳过逻辑"""
        context = ValidationContext.create_for_testing()
        
        # 默认不跳过
        assert not context.should_skip_validator("test_validator")
        
        # 添加到跳过列表
        context.skip_validators = ["test_validator"]
        assert context.should_skip_validator("test_validator")
        
        # 启用列表测试
        context.skip_validators = []
        context.enabled_validators = ["other_validator"]
        assert context.should_skip_validator("test_validator")  # 不在启用列表中
        
        context.enabled_validators = ["test_validator"]
        assert not context.should_skip_validator("test_validator")  # 在启用列表中


class TestValidationResult:
    """验证结果测试"""
    
    def test_create_success_result(self):
        """测试创建成功结果"""
        result = ValidationResult.create_success(
            metadata={"test": "success"},
            request_id="req123"
        )
        
        assert result.status == ValidationStatus.SUCCESS
        assert result.is_valid
        assert not result.has_errors
        assert not result.has_warnings
        assert result.request_id == "req123"
        assert result.metadata["test"] == "success"
    
    def test_create_error_result(self):
        """测试创建错误结果"""
        error = ValidationError(
            code="TEST_ERROR",
            message="测试错误",
            severity=ValidationSeverity.HIGH
        )
        
        result = ValidationResult.create_error(error, request_id="req123")
        
        assert result.status == ValidationStatus.ERROR
        assert not result.is_valid
        assert result.has_errors
        assert len(result.errors) == 1
        assert result.errors[0].code == "TEST_ERROR"
        assert result.request_id == "req123"
    
    def test_merge_results(self):
        """测试结果合并"""
        # 创建两个结果
        result1 = ValidationResult.create_success()
        
        error = ValidationError(code="ERROR", message="错误")
        result2 = ValidationResult.create_error(error)
        
        # 合并结果
        merged = result1.merge(result2)
        
        # 合并后的状态应该是更严重的状态
        assert merged.status == ValidationStatus.ERROR
        assert not merged.is_valid
        assert len(merged.errors) == 1
        assert merged.metrics.executed_validators == 0  # 合并的指标
    
    def test_result_to_http_response(self):
        """测试转换为HTTP响应格式"""
        # 成功结果
        success_result = ValidationResult.create_success(request_id="req123")
        http_response = success_result.to_http_response()
        
        assert http_response["success"] is True
        assert http_response["status"] == "success"
        assert http_response["request_id"] == "req123"
        
        # 错误结果
        error = ValidationError(code="ERROR", message="错误")
        error_result = ValidationResult.create_error(error, request_id="req123")
        http_response = error_result.to_http_response()
        
        assert http_response["success"] is False
        assert http_response["status"] == "error"
        assert len(http_response["errors"]) == 1
        assert http_response["request_id"] == "req123"


class TestValidationError:
    """验证错误测试"""
    
    def test_create_xss_error(self):
        """测试创建XSS错误"""
        error = ValidationError.create_xss_error("security_validator")
        
        assert error.code == "XSS_DETECTED"
        assert error.severity == ValidationSeverity.CRITICAL
        assert error.validator == "security_validator"
        assert error.is_critical()
        assert error.is_security_related()
    
    def test_create_sql_injection_error(self):
        """测试创建SQL注入错误"""
        error = ValidationError.create_sql_injection_error("security_validator")
        
        assert error.code == "SQL_INJECTION_DETECTED"
        assert error.severity == ValidationSeverity.CRITICAL
        assert error.validator == "security_validator"
        assert error.is_critical()
        assert error.is_security_related()
    
    def test_create_size_error(self):
        """测试创建大小错误"""
        error = ValidationError.create_size_error("size_validator", 1000, 2000)
        
        assert error.code == "SIZE_LIMIT_EXCEEDED"
        assert error.severity == ValidationSeverity.HIGH
        assert error.validator == "size_validator"
        assert "1000" in error.message
        assert "2000" in error.message


class TestValidationConfig:
    """验证配置测试"""
    
    def test_config_initialization(self):
        """测试配置初始化"""
        config = ValidationConfig()
        
        # 配置应该继承自MultilingualConfig
        assert hasattr(config, 'get_default_language')
        assert hasattr(config, 'is_validation_enabled')
        assert hasattr(config, 'get_validation_mode')
    
    def test_validation_enabled(self):
        """测试验证功能启用状态"""
        config = ValidationConfig()
        
        # 默认应该启用
        assert config.is_validation_enabled()
    
    def test_validation_mode(self):
        """测试验证模式获取"""
        config = ValidationConfig()
        
        mode = config.get_validation_mode()
        assert mode in ValidationMode
    
    def test_size_limits(self):
        """测试大小限制配置"""
        config = ValidationConfig()
        
        max_request_size = config.get_max_request_size()
        assert isinstance(max_request_size, int)
        assert max_request_size > 0
        
        max_message_length = config.get_max_message_length()
        assert isinstance(max_message_length, int)
        assert max_message_length > 0
    
    def test_get_global_config(self):
        """测试获取全局配置"""
        config = get_validation_config()
        assert isinstance(config, ValidationConfig)


class SimpleTestValidator(BaseValidator):
    """简单测试验证器"""
    
    def __init__(self):
        super().__init__("simple_test", ValidatorPriority.MEDIUM)
    
    async def _execute_validation(self, context: ValidationContext) -> ValidationResult:
        """简单的验证逻辑"""
        if context.request_data is None:
            error = ValidationError(
                code="NO_DATA",
                message="没有数据",
                validator=self.validator_name
            )
            return ValidationResult.create_error(error)
        
        return ValidationResult.create_success()


class TestBaseValidator:
    """基础验证器测试"""
    
    @pytest.mark.asyncio
    async def test_validator_basic_functionality(self):
        """测试验证器基本功能"""
        validator = SimpleTestValidator()
        
        assert validator.get_validator_name() == "simple_test"
        assert validator.get_priority() == ValidatorPriority.MEDIUM
        assert validator.supports_async()
        assert validator.can_cache_result()
    
    @pytest.mark.asyncio
    async def test_validator_success_case(self):
        """测试验证器成功情况"""
        validator = SimpleTestValidator()
        context = ValidationContext.create_for_testing(
            request_data={"test": "data"}
        )
        
        result = await validator.validate(context)
        
        assert result.is_valid
        assert result.status == ValidationStatus.SUCCESS
        assert not result.has_errors
    
    @pytest.mark.asyncio
    async def test_validator_error_case(self):
        """测试验证器错误情况"""
        validator = SimpleTestValidator()
        context = ValidationContext.create_for_testing(
            request_data=None  # 触发错误
        )
        
        result = await validator.validate(context)
        
        assert not result.is_valid
        assert result.status == ValidationStatus.ERROR
        assert result.has_errors
        assert len(result.errors) == 1
        assert result.errors[0].code == "NO_DATA"
    
    @pytest.mark.asyncio
    async def test_validator_metrics(self):
        """测试验证器指标收集"""
        validator = SimpleTestValidator()
        context = ValidationContext.create_for_testing(
            request_data={"test": "data"}
        )
        
        # 执行几次验证
        await validator.validate(context)
        await validator.validate(context)
        
        metrics = validator.get_metrics()
        
        assert metrics["total_validations"] == 2
        assert metrics["successful_validations"] >= 0
        assert metrics["total_execution_time"] > 0
        assert "success_rate" in metrics
        assert "cache_hit_rate" in metrics
    
    def test_validator_cache_key_generation(self):
        """测试缓存键生成"""
        validator = SimpleTestValidator()
        context = ValidationContext.create_for_testing(
            request_data={"test": "data"}
        )
        
        cache_key = validator.get_cache_key(context)
        
        assert cache_key is not None
        assert isinstance(cache_key, str)
        assert len(cache_key) > 0
        
        # 相同上下文应该生成相同的缓存键
        cache_key2 = validator.get_cache_key(context)
        assert cache_key == cache_key2


# 运行测试的便捷函数
def run_tests():
    """运行所有测试"""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_tests()
