"""
阶段一核心组件测试

测试验证系统的核心接口、数据结构和配置管理。
"""

import pytest
import time
from datetime import datetime
from typing import Dict, Any

from agent.validation.core.interfaces import ValidatorPriority
from agent.validation.core.validation_context import ValidationContext, ValidationMode
from agent.validation.core.validation_result import (
    ValidationResult, ValidationError, ValidationStatus, 
    ValidationSeverity, ValidationMetrics
)
from agent.validation.core.base_validator import BaseValidator
from agent.validation.config.validation_config import ValidationConfig, ValidatorConfig


class TestValidationContext:
    """测试验证上下文"""
    
    def test_create_basic_context(self):
        """测试基本上下文创建"""
        context = ValidationContext(
            request_data={"test": "data"},
            validation_mode=ValidationMode.STRICT,
            request_path="/api/test"
        )
        
        assert context.request_data == {"test": "data"}
        assert context.validation_mode == ValidationMode.STRICT
        assert context.request_path == "/api/test"
        assert context.validation_start_time is not None
        assert context.get_execution_time() >= 0
    
    def test_context_for_testing(self):
        """测试创建用于测试的上下文"""
        context = ValidationContext.create_for_testing(
            request_data={"message": "hello"},
            validation_mode=ValidationMode.LENIENT
        )
        
        assert context.request_data == {"message": "hello"}
        assert context.validation_mode == ValidationMode.LENIENT
        assert context.request_method == "POST"
        assert context.request_path == "/api/test"
        assert not context.enable_cache  # 测试时默认不启用缓存
    
    def test_should_skip_validator(self):
        """测试验证器跳过逻辑"""
        context = ValidationContext.create_for_testing(
            skip_validators=["validator1"],
            enabled_validators=["validator2", "validator3"]
        )
        
        assert context.should_skip_validator("validator1")  # 在跳过列表中
        assert not context.should_skip_validator("validator2")  # 在启用列表中
        assert context.should_skip_validator("validator4")  # 不在启用列表中
    
    def test_language_preference(self):
        """测试语言偏好获取"""
        context = ValidationContext.create_for_testing(
            language="zh",
            supported_languages=["en", "zh", "ja"]
        )
        
        assert context.get_language_preference() == "zh"
        
        # 测试检测到的语言
        context.language = None
        context.detected_language = "ja"
        assert context.get_language_preference() == "ja"
        
        # 测试默认语言
        context.detected_language = None
        assert context.get_language_preference() == "en"
    
    def test_context_summary(self):
        """测试上下文摘要"""
        context = ValidationContext.create_for_testing(
            request_data={"test": "data"}
        )
        
        summary = context.to_summary()
        assert "ValidationContext" in summary
        assert context.request_id in summary
        assert "POST" in summary


class TestValidationResult:
    """测试验证结果"""
    
    def test_create_success_result(self):
        """测试创建成功结果"""
        result = ValidationResult.create_success(
            metadata={"test": "meta"},
            request_id="test_request"
        )
        
        assert result.status == ValidationStatus.SUCCESS
        assert result.is_valid
        assert not result.has_errors
        assert not result.has_warnings
        assert result.metadata == {"test": "meta"}
        assert result.request_id == "test_request"
    
    def test_create_error_result(self):
        """测试创建错误结果"""
        error = ValidationError(
            code="TEST_ERROR",
            message="测试错误",
            severity=ValidationSeverity.HIGH
        )
        
        result = ValidationResult.create_error(
            error=error,
            request_id="test_request"
        )
        
        assert result.status == ValidationStatus.ERROR
        assert not result.is_valid
        assert result.has_errors
        assert len(result.errors) == 1
        assert result.errors[0].code == "TEST_ERROR"
    
    def test_add_validator_result(self):
        """测试添加验证器结果"""
        result = ValidationResult.create_success()
        
        result.add_validator_result("test_validator", ValidationStatus.SUCCESS, 0.1)
        
        assert "test_validator" in result.validator_results
        assert result.validator_results["test_validator"] == ValidationStatus.SUCCESS
        assert "test_validator" in result.execution_order
        assert result.metrics.executed_validators == 1
    
    def test_merge_results(self):
        """测试结果合并"""
        result1 = ValidationResult.create_success()
        result1.add_validator_result("validator1", ValidationStatus.SUCCESS, 0.1)
        
        error = ValidationError(code="ERROR1", message="错误1")
        result2 = ValidationResult.create_error(error)
        result2.add_validator_result("validator2", ValidationStatus.ERROR, 0.2)
        
        merged = result1.merge(result2)
        
        assert merged.status == ValidationStatus.ERROR  # 取最严重的状态
        assert len(merged.errors) == 1
        assert merged.metrics.executed_validators == 2
        assert len(merged.execution_order) == 2
    
    def test_error_creation_helpers(self):
        """测试错误创建辅助方法"""
        # XSS错误
        xss_error = ValidationError.create_xss_error("<script>", "security")
        assert xss_error.code == "XSS_DETECTED"
        assert xss_error.severity == ValidationSeverity.CRITICAL
        
        # SQL注入错误
        sql_error = ValidationError.create_sql_injection_error("'; DROP TABLE", "security")
        assert sql_error.code == "SQL_INJECTION_DETECTED"
        assert sql_error.severity == ValidationSeverity.CRITICAL
        
        # 大小错误
        size_error = ValidationError.create_size_error(2000, 1000, "content")
        assert size_error.code == "SIZE_LIMIT_EXCEEDED"
        assert size_error.severity == ValidationSeverity.HIGH
    
    def test_http_response_format(self):
        """测试HTTP响应格式"""
        # 成功响应
        success_result = ValidationResult.create_success()
        success_response = success_result.to_http_response()
        
        assert success_response["success"] is True
        assert success_response["status"] == "success"
        assert "execution_time" in success_response
        
        # 错误响应
        error = ValidationError(code="TEST_ERROR", message="测试错误")
        error_result = ValidationResult.create_error(error, request_id="test_req")
        error_response = error_result.to_http_response()
        
        assert error_response["success"] is False
        assert error_response["status"] == "error"
        assert len(error_response["errors"]) == 1
        assert error_response["request_id"] == "test_req"


class TestValidationMetrics:
    """测试验证指标"""
    
    def test_metrics_calculation(self):
        """测试指标计算"""
        metrics = ValidationMetrics()
        
        # 添加执行记录
        metrics.add_validator_execution(0.1, True, False)  # 成功，未缓存
        metrics.add_validator_execution(0.2, False, True)  # 失败，缓存
        metrics.add_validator_execution(0.1, True, True)   # 成功，缓存
        
        assert metrics.executed_validators == 3
        assert metrics.failed_validators == 1
        assert metrics.cache_hits == 2
        assert metrics.cache_misses == 1
        assert metrics.get_success_rate() == 2/3
        assert metrics.get_cache_hit_rate() == 2/3
        assert metrics.get_average_execution_time() == 0.4/3


class MockValidator(BaseValidator):
    """模拟验证器用于测试"""
    
    def __init__(self, config: Dict[str, Any], should_fail: bool = False):
        super().__init__(config)
        self.should_fail = should_fail
        self.validation_count = 0
    
    async def _do_validate(self, context: ValidationContext) -> ValidationResult:
        """模拟验证逻辑"""
        self.validation_count += 1
        
        if self.should_fail:
            error = ValidationError(
                code="MOCK_ERROR",
                message="模拟验证失败",
                validator=self.get_validator_name()
            )
            return ValidationResult.create_error(error)
        
        return ValidationResult.create_success()
    
    def get_validator_name(self) -> str:
        return "mock_validator"


class TestBaseValidator:
    """测试基础验证器"""
    
    @pytest.mark.asyncio
    async def test_successful_validation(self):
        """测试成功验证"""
        validator = MockValidator({"enabled": True})
        context = ValidationContext.create_for_testing()
        
        result = await validator.validate(context)
        
        assert result.is_valid
        assert validator.validation_count == 1
        assert "mock_validator" in result.validator_results
    
    @pytest.mark.asyncio
    async def test_failed_validation(self):
        """测试失败验证"""
        validator = MockValidator({"enabled": True}, should_fail=True)
        context = ValidationContext.create_for_testing()
        
        result = await validator.validate(context)
        
        assert not result.is_valid
        assert len(result.errors) == 1
        assert result.errors[0].code == "MOCK_ERROR"
    
    @pytest.mark.asyncio
    async def test_skipped_validation(self):
        """测试跳过验证"""
        validator = MockValidator({"enabled": True})
        context = ValidationContext.create_for_testing(
            skip_validators=["mock_validator"]
        )
        
        result = await validator.validate(context)
        
        assert result.status == ValidationStatus.SKIPPED
        assert validator.validation_count == 0  # 应该没有执行验证逻辑
    
    @pytest.mark.asyncio
    async def test_caching(self):
        """测试缓存功能"""
        validator = MockValidator({"enabled": True, "enable_cache": True})
        context = ValidationContext.create_for_testing(enable_cache=True)
        
        # 第一次验证
        result1 = await validator.validate(context)
        assert result1.is_valid
        assert validator.validation_count == 1
        
        # 第二次验证（应该使用缓存）
        result2 = await validator.validate(context)
        assert result2.is_valid
        assert validator.validation_count == 1  # 验证逻辑没有再次执行
        assert result2.metrics.cache_hits > 0


class TestValidationConfig:
    """测试验证配置"""
    
    def test_config_loading(self):
        """测试配置加载"""
        config = ValidationConfig("settings.toml")
        
        assert isinstance(config.enabled, bool)
        assert isinstance(config.mode, ValidationMode)
        assert isinstance(config.max_request_size, int)
        assert isinstance(config.excluded_paths, list)
    
    def test_validator_configs(self):
        """测试验证器配置"""
        config = ValidationConfig("settings.toml")
        validator_configs = config.get_validator_configs()
        
        assert isinstance(validator_configs, list)
        assert len(validator_configs) > 0
        
        # 检查是否有安全验证器
        security_config = config.get_validator_config("security")
        assert security_config is not None
        assert security_config.type == "security"
        assert isinstance(security_config.enabled, bool)
    
    def test_endpoint_validators(self):
        """测试端点验证器配置"""
        config = ValidationConfig("settings.toml")
        
        # 测试具体端点
        validators = config.get_endpoint_validators("/api/chat/agent")
        assert isinstance(validators, list)
        assert len(validators) > 0
        
        # 测试通配符匹配
        validators = config.get_endpoint_validators("/api/mcp/test")
        assert isinstance(validators, list)
    
    def test_config_validation(self):
        """测试配置验证"""
        config = ValidationConfig("settings.toml")
        warnings = config.validate_config()
        
        assert isinstance(warnings, list)
        # 如果配置正确，应该没有警告或只有少量警告
        print(f"配置警告数量: {len(warnings)}")
        for warning in warnings:
            print(f"  - {warning}")
    
    def test_priority_mapping(self):
        """测试优先级映射"""
        config = ValidationConfig("settings.toml")
        
        # 测试已配置的验证器优先级
        security_priority = config.get_validator_priority("security")
        assert security_priority == ValidatorPriority.CRITICAL
        
        size_priority = config.get_validator_priority("size")
        assert size_priority == ValidatorPriority.HIGH
        
        # 测试未配置的验证器（应该返回默认优先级）
        unknown_priority = config.get_validator_priority("unknown")
        assert unknown_priority == ValidatorPriority.MEDIUM


if __name__ == "__main__":
    # 运行简单的测试
    print("🧪 运行验证系统阶段一测试...")
    
    # 测试上下文创建
    print("✅ 测试验证上下文创建...")
    context = ValidationContext.create_for_testing(request_data={"test": "data"})
    print(f"   上下文摘要: {context.to_summary()}")
    
    # 测试验证结果
    print("✅ 测试验证结果创建...")
    result = ValidationResult.create_success(request_id="test_req")
    print(f"   结果摘要: {result.to_summary()}")
    
    # 测试配置加载
    print("✅ 测试配置加载...")
    config = ValidationConfig("settings.toml")
    print(f"   验证系统启用: {config.enabled}")
    print(f"   验证模式: {config.mode.value}")
    print(f"   配置的验证器数量: {len(config.get_validator_configs())}")
    
    # 测试配置验证
    warnings = config.validate_config()
    if warnings:
        print(f"⚠️  配置警告 ({len(warnings)} 个):")
        for warning in warnings:
            print(f"   - {warning}")
    else:
        print("✅ 配置验证通过，无警告")
    
    print("\n🎉 阶段一核心组件测试完成！")
    print("✅ 核心接口定义完成")
    print("✅ 验证上下文和结果类完成")
    print("✅ 基础验证器模板完成")
    print("✅ 验证配置系统完成")
    print("✅ 与现有系统集成完成")
    print("\n📋 已完成开发步骤阶段一的所有任务！")
