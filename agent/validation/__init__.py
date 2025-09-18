"""
GTPlanner 请求验证系统

基于现代设计模式的企业级请求验证框架，支持：
- 多层安全验证（XSS、SQL注入、敏感信息检测）
- 灵活的验证策略和责任链模式
- 实时流式验证事件
- 完整的性能监控和指标收集
- 与GTPlanner现有系统的无缝集成

主要组件：
- core: 核心接口和数据结构
- strategies: 验证策略实现
- chains: 验证责任链
- factories: 工厂模式实现
- middleware: FastAPI中间件集成
- observers: 观察者模式事件处理
- adapters: 适配器模式系统集成
- config: 配置管理
- utils: 工具类和辅助函数
"""

__version__ = "1.0.0"
__author__ = "GTPlanner Team"

# 导出核心类和接口
from .core.interfaces import (
    IValidator,
    IValidationStrategy,
    IValidationChain,
    IValidationObserver,
    IValidationMiddleware,
    IValidationCache,
    IValidationMetrics,
    ValidatorPriority
)

from .core.validation_context import ValidationContext, ValidationMode
from .core.validation_result import (
    ValidationResult,
    ValidationError,
    ValidationStatus,
    ValidationSeverity,
    ValidationMetrics
)

# from .config.validation_config import ValidationConfig  # 暂时注释掉，避免dynaconf依赖

__all__ = [
    # 接口
    "IValidator",
    "IValidationStrategy", 
    "IValidationChain",
    "IValidationObserver",
    "IValidationMiddleware",
    "IValidationCache",
    "IValidationMetrics",
    "ValidatorPriority",
    
    # 核心类
    "ValidationContext",
    "ValidationMode",
    "ValidationResult",
    "ValidationError",
    "ValidationStatus",
    "ValidationSeverity",
    "ValidationMetrics",
    
    # 配置
    # "ValidationConfig",
]

