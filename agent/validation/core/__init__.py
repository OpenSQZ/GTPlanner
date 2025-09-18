"""
验证系统核心组件

包含所有基础接口、数据结构和核心类的定义。
"""

from .interfaces import (
    IValidator,
    IValidationStrategy,
    IValidationChain,
    IValidationObserver,
    IValidationMiddleware,
    IValidationCache,
    IValidationMetrics,
    ValidatorPriority
)

from .validation_context import ValidationContext, ValidationMode
from .validation_result import (
    ValidationResult,
    ValidationError,
    ValidationStatus,
    ValidationSeverity,
    ValidationMetrics
)

# from .base_validator import BaseValidator  # 暂时注释掉，避免dynaconf依赖

__all__ = [
    "IValidator",
    "IValidationStrategy",
    "IValidationChain", 
    "IValidationObserver",
    "IValidationMiddleware",
    "IValidationCache",
    "IValidationMetrics",
    "ValidatorPriority",
    "ValidationContext",
    "ValidationMode",
    "ValidationResult",
    "ValidationError",
    "ValidationStatus",
    "ValidationSeverity",
    "ValidationMetrics",
    # "BaseValidator",
]

