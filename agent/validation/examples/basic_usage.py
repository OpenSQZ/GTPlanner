"""
GTPlanner 验证系统基本使用示例

演示如何使用验证系统的核心功能：
- 创建验证上下文
- 实现自定义验证器
- 使用配置管理
- 处理验证结果
"""

import asyncio
from typing import Dict, Any
from datetime import datetime

# 导入验证系统核心组件
from ..core.validation_context import ValidationContext, ValidationMode
from ..core.validation_result import ValidationResult, ValidationError, ValidationSeverity
from ..core.base_validator import BaseValidator
from ..core.interfaces import ValidatorPriority
from ..config.validation_config import get_validation_config


class ExampleValidator(BaseValidator):
    """示例验证器
    
    演示如何继承BaseValidator实现自定义验证器
    """
    
    def __init__(self):
        super().__init__("example", ValidatorPriority.MEDIUM)
    
    async def _execute_validation(self, context: ValidationContext) -> ValidationResult:
        """执行示例验证逻辑"""
        
        # 检查请求数据是否存在
        if not context.request_data:
            error = ValidationError(
                code="MISSING_DATA",
                message="请求数据不能为空",
                validator=self.validator_name,
                severity=ValidationSeverity.HIGH,
                suggestion="请提供有效的请求数据"
            )
            return ValidationResult.create_error(error, request_id=context.request_id)
        
        # 检查数据类型
        if not isinstance(context.request_data, dict):
            error = ValidationError(
                code="INVALID_DATA_TYPE",
                message="请求数据必须是字典格式",
                validator=self.validator_name,
                severity=ValidationSeverity.MEDIUM,
                suggestion="请确保请求数据为JSON对象格式"
            )
            return ValidationResult.create_error(error, request_id=context.request_id)
        
        # 检查必需字段
        required_fields = ["session_id", "dialogue_history"]
        missing_fields = []
        
        for field in required_fields:
            if field not in context.request_data:
                missing_fields.append(field)
        
        if missing_fields:
            error = ValidationError(
                code="MISSING_REQUIRED_FIELDS",
                message=f"缺少必需字段: {', '.join(missing_fields)}",
                validator=self.validator_name,
                severity=ValidationSeverity.HIGH,
                suggestion=f"请确保请求包含以下字段: {', '.join(required_fields)}"
            )
            return ValidationResult.create_error(error, request_id=context.request_id)
        
        # 验证成功
        return ValidationResult.create_success(
            metadata={"validated_fields": required_fields},
            request_id=context.request_id
        )


async def basic_usage_example():
    """基本使用示例"""
    print("=== GTPlanner 验证系统基本使用示例 ===\n")
    
    # 1. 创建验证上下文
    print("1. 创建验证上下文...")
    
    # 模拟请求数据
    request_data = {
        "session_id": "test_session_123",
        "dialogue_history": [
            {"role": "user", "content": "Hello, world!", "timestamp": "2023-01-01T00:00:00Z"}
        ],
        "tool_execution_results": {},
        "session_metadata": {"language": "en"}
    }
    
    # 创建验证上下文
    context = ValidationContext.create_for_testing(
        request_data=request_data,
        validation_mode=ValidationMode.STRICT,
        user_id="test_user",
        session_id="test_session_123"
    )
    
    print(f"验证上下文创建成功: {context.to_summary()}")
    print()
    
    # 2. 创建并使用验证器
    print("2. 创建并使用验证器...")
    
    validator = ExampleValidator()
    print(f"验证器: {validator}")
    print(f"配置摘要: {validator.get_config_summary()}")
    print()
    
    # 3. 执行验证
    print("3. 执行验证...")
    
    result = await validator.validate(context)
    
    print(f"验证结果: {result.to_summary()}")
    print(f"验证通过: {result.is_valid}")
    
    if result.errors:
        print("错误信息:")
        for error in result.errors:
            print(f"  - {error.code}: {error.message}")
    
    if result.warnings:
        print("警告信息:")
        for warning in result.warnings:
            print(f"  - {warning.code}: {warning.message}")
    
    print()
    
    # 4. 查看性能指标
    print("4. 查看性能指标...")
    
    metrics = validator.get_metrics()
    print("验证器指标:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    print()
    
    # 5. 配置系统示例
    print("5. 配置系统示例...")
    
    config = get_validation_config()
    print(f"验证功能启用: {config.is_validation_enabled()}")
    print(f"验证模式: {config.get_validation_mode()}")
    print(f"最大请求大小: {config.get_max_request_size()} 字节")
    print(f"缓存启用: {config.is_caching_enabled()}")
    print()


async def error_handling_example():
    """错误处理示例"""
    print("=== 错误处理示例 ===\n")
    
    # 创建无效的请求数据
    invalid_data = "这不是一个字典"
    
    context = ValidationContext.create_for_testing(
        request_data=invalid_data,
        validation_mode=ValidationMode.STRICT
    )
    
    validator = ExampleValidator()
    result = await validator.validate(context)
    
    print(f"验证结果: {result.to_summary()}")
    print("详细错误信息:")
    
    for error in result.errors:
        print(f"错误代码: {error.code}")
        print(f"错误消息: {error.message}")
        print(f"严重程度: {error.severity.name}")
        print(f"修复建议: {error.suggestion}")
        print(f"验证器: {error.validator}")
        print()


async def caching_example():
    """缓存示例"""
    print("=== 缓存示例 ===\n")
    
    request_data = {
        "session_id": "cache_test",
        "dialogue_history": [{"role": "user", "content": "Test message"}]
    }
    
    context = ValidationContext.create_for_testing(request_data=request_data)
    validator = ExampleValidator()
    
    # 第一次验证（会缓存结果）
    print("第一次验证（无缓存）...")
    start_time = datetime.now()
    result1 = await validator.validate(context)
    end_time = datetime.now()
    print(f"执行时间: {(end_time - start_time).total_seconds():.4f} 秒")
    
    # 第二次验证（使用缓存）
    print("第二次验证（使用缓存）...")
    start_time = datetime.now()
    result2 = await validator.validate(context)
    end_time = datetime.now()
    print(f"执行时间: {(end_time - start_time).total_seconds():.4f} 秒")
    
    # 查看缓存指标
    metrics = validator.get_metrics()
    print(f"缓存命中次数: {metrics['cache_hits']}")
    print(f"缓存未命中次数: {metrics['cache_misses']}")
    print(f"缓存命中率: {metrics['cache_hit_rate']:.2%}")
    print()


async def main():
    """主函数"""
    try:
        await basic_usage_example()
        await error_handling_example()
        await caching_example()
        
        print("=== 示例执行完成 ===")
        
    except Exception as e:
        print(f"示例执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
