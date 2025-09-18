"""
验证器工厂

基于工厂模式的验证器创建和管理，提供：
- 验证器类型注册
- 验证器实例创建
- 配置驱动的验证器创建
- 验证器单例管理
- 验证器依赖注入
"""

from typing import Dict, Any, Optional, Type, Callable, List
from ..core.interfaces import IValidator, IValidationStrategy
from ..core.validation_result import ValidationError, ValidationSeverity


class ValidatorRegistry:
    """验证器注册表 - 管理验证器类型和创建逻辑"""
    
    def __init__(self):
        self._validator_classes: Dict[str, Type[IValidator]] = {}
        self._strategy_classes: Dict[str, Type[IValidationStrategy]] = {}
        self._factory_functions: Dict[str, Callable[[Dict[str, Any]], IValidator]] = {}
        self._singletons: Dict[str, IValidator] = {}
    
    def register_validator_class(self, validator_type: str, validator_class: Type[IValidator]) -> None:
        """注册验证器类
        
        Args:
            validator_type: 验证器类型标识
            validator_class: 验证器类
        """
        self._validator_classes[validator_type] = validator_class
    
    def register_strategy_class(self, strategy_type: str, strategy_class: Type[IValidationStrategy]) -> None:
        """注册验证策略类
        
        Args:
            strategy_type: 策略类型标识
            strategy_class: 策略类
        """
        self._strategy_classes[strategy_type] = strategy_class
    
    def register_factory_function(self, validator_type: str, factory_func: Callable[[Dict[str, Any]], IValidator]) -> None:
        """注册验证器工厂函数
        
        Args:
            validator_type: 验证器类型标识
            factory_func: 工厂函数
        """
        self._factory_functions[validator_type] = factory_func
    
    def create_validator(self, validator_type: str, config: Dict[str, Any], use_singleton: bool = False) -> Optional[IValidator]:
        """创建验证器实例
        
        Args:
            validator_type: 验证器类型
            config: 验证器配置
            use_singleton: 是否使用单例模式
            
        Returns:
            验证器实例，如果创建失败则返回None
        """
        # 检查单例缓存
        if use_singleton and validator_type in self._singletons:
            return self._singletons[validator_type]
        
        validator = None
        
        try:
            # 优先使用工厂函数
            if validator_type in self._factory_functions:
                validator = self._factory_functions[validator_type](config)
            
            # 其次使用注册的验证器类
            elif validator_type in self._validator_classes:
                validator_class = self._validator_classes[validator_type]
                validator = validator_class(config)
            
            # 最后尝试使用策略类包装
            elif validator_type in self._strategy_classes:
                strategy_class = self._strategy_classes[validator_type]
                strategy = strategy_class(config)
                validator = StrategyValidator(strategy, validator_type)
            
            # 如果使用单例模式，缓存实例
            if validator and use_singleton:
                self._singletons[validator_type] = validator
            
            return validator
            
        except Exception as e:
            # 创建失败，返回None
            print(f"Warning: Failed to create validator {validator_type}: {e}")
            return None
    
    def list_validator_types(self) -> List[str]:
        """列出所有已注册的验证器类型
        
        Returns:
            验证器类型列表
        """
        all_types = set()
        all_types.update(self._validator_classes.keys())
        all_types.update(self._strategy_classes.keys())
        all_types.update(self._factory_functions.keys())
        return sorted(list(all_types))
    
    def is_registered(self, validator_type: str) -> bool:
        """检查验证器类型是否已注册
        
        Args:
            validator_type: 验证器类型
            
        Returns:
            True表示已注册，False表示未注册
        """
        return (validator_type in self._validator_classes or
                validator_type in self._strategy_classes or
                validator_type in self._factory_functions)
    
    def unregister(self, validator_type: str) -> bool:
        """注销验证器类型
        
        Args:
            validator_type: 验证器类型
            
        Returns:
            True表示注销成功，False表示类型不存在
        """
        removed = False
        
        if validator_type in self._validator_classes:
            del self._validator_classes[validator_type]
            removed = True
        
        if validator_type in self._strategy_classes:
            del self._strategy_classes[validator_type]
            removed = True
        
        if validator_type in self._factory_functions:
            del self._factory_functions[validator_type]
            removed = True
        
        if validator_type in self._singletons:
            del self._singletons[validator_type]
        
        return removed
    
    def clear_singletons(self) -> None:
        """清空所有单例缓存"""
        self._singletons.clear()


class StrategyValidator(IValidator):
    """策略验证器包装器 - 将验证策略包装为验证器"""
    
    def __init__(self, strategy: IValidationStrategy, validator_name: str):
        self.strategy = strategy
        self.validator_name = validator_name
    
    async def validate(self, context) -> 'ValidationResult':
        """执行验证"""
        return await self.strategy.execute(context.request_data, context.validation_rules)
    
    def get_validator_name(self) -> str:
        return self.validator_name
    
    def get_priority(self):
        # 默认优先级，可以通过配置覆盖
        from ..core.interfaces import ValidatorPriority
        return ValidatorPriority.MEDIUM
    
    def supports_async(self) -> bool:
        return True


class ValidatorFactory:
    """验证器工厂 - 统一的验证器创建和管理"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.registry = ValidatorRegistry()
        self._registered_defaults = False
    
    def register_default_validators(self) -> None:
        """注册默认的验证器"""
        if self._registered_defaults:
            return
        
        try:
            # 注册验证策略
            from ..strategies.security_validator import SecurityValidationStrategy
            self.registry.register_strategy_class("security", SecurityValidationStrategy)
        except ImportError:
            pass
        
        try:
            from ..strategies.size_validator import SizeValidationStrategy
            self.registry.register_strategy_class("size", SizeValidationStrategy)
        except ImportError:
            pass
        
        try:
            from ..strategies.format_validator import FormatValidationStrategy
            self.registry.register_strategy_class("format", FormatValidationStrategy)
        except ImportError:
            pass
        
        try:
            from ..strategies.content_validator import ContentValidationStrategy
            self.registry.register_strategy_class("content", ContentValidationStrategy)
        except ImportError:
            pass
        
        try:
            from ..strategies.language_validator import LanguageValidationStrategy
            self.registry.register_strategy_class("language", LanguageValidationStrategy)
        except ImportError:
            pass
        
        try:
            from ..strategies.rate_limit_validator import RateLimitValidationStrategy
            self.registry.register_strategy_class("rate_limit", RateLimitValidationStrategy)
        except ImportError:
            pass
        
        try:
            from ..strategies.session_validator import SessionValidationStrategy
            self.registry.register_strategy_class("session", SessionValidationStrategy)
        except ImportError:
            pass
        
        self._registered_defaults = True
    
    def create_validator(self, validator_type: str, config: Optional[Dict[str, Any]] = None) -> Optional[IValidator]:
        """创建验证器实例
        
        Args:
            validator_type: 验证器类型
            config: 验证器配置，如果为None则使用工厂默认配置
            
        Returns:
            验证器实例，如果创建失败则返回None
        """
        # 确保默认验证器已注册
        self.register_default_validators()
        
        # 合并配置
        merged_config = {**self.config.get(validator_type, {}), **(config or {})}
        
        # 检查验证器是否启用
        if not merged_config.get("enabled", True):
            return None
        
        return self.registry.create_validator(validator_type, merged_config)
    
    def create_validators(self, validator_configs: List[Dict[str, Any]]) -> List[IValidator]:
        """批量创建验证器
        
        Args:
            validator_configs: 验证器配置列表，每个配置应包含name和type字段
            
        Returns:
            验证器实例列表
        """
        validators = []
        
        for config in validator_configs:
            validator_type = config.get("type")
            validator_config = config.get("config", {})
            
            if validator_type:
                validator = self.create_validator(validator_type, validator_config)
                if validator:
                    validators.append(validator)
        
        return validators
    
    def create_validators_by_names(self, validator_names: List[str]) -> List[IValidator]:
        """通过名称列表创建验证器
        
        Args:
            validator_names: 验证器名称列表
            
        Returns:
            验证器实例列表
        """
        validators = []
        
        for name in validator_names:
            validator = self.create_validator(name)
            if validator:
                validators.append(validator)
        
        return validators
    
    def get_available_validators(self) -> List[str]:
        """获取所有可用的验证器类型
        
        Returns:
            可用验证器类型列表
        """
        self.register_default_validators()
        return self.registry.list_validator_types()
    
    def is_validator_available(self, validator_type: str) -> bool:
        """检查验证器是否可用
        
        Args:
            validator_type: 验证器类型
            
        Returns:
            True表示可用，False表示不可用
        """
        self.register_default_validators()
        return self.registry.is_registered(validator_type)
    
    def register_custom_validator(
        self, 
        validator_type: str, 
        validator_class: Type[IValidator]
    ) -> None:
        """注册自定义验证器
        
        Args:
            validator_type: 验证器类型标识
            validator_class: 验证器类
        """
        self.registry.register_validator_class(validator_type, validator_class)
    
    def register_custom_strategy(
        self, 
        strategy_type: str, 
        strategy_class: Type[IValidationStrategy]
    ) -> None:
        """注册自定义验证策略
        
        Args:
            strategy_type: 策略类型标识
            strategy_class: 策略类
        """
        self.registry.register_strategy_class(strategy_type, strategy_class)
    
    def validate_config(self, validator_configs: List[Dict[str, Any]]) -> List[str]:
        """验证验证器配置
        
        Args:
            validator_configs: 验证器配置列表
            
        Returns:
            配置警告列表
        """
        warnings = []
        
        for config in validator_configs:
            validator_name = config.get("name", "unknown")
            validator_type = config.get("type")
            
            if not validator_type:
                warnings.append(f"验证器 '{validator_name}' 缺少type字段")
                continue
            
            if not self.is_validator_available(validator_type):
                warnings.append(f"验证器类型 '{validator_type}' 不可用")
                continue
            
            # 尝试创建验证器以验证配置
            try:
                validator = self.create_validator(validator_type, config.get("config", {}))
                if validator is None:
                    warnings.append(f"验证器 '{validator_name}' 创建失败")
            except Exception as e:
                warnings.append(f"验证器 '{validator_name}' 配置错误: {str(e)}")
        
        return warnings
    
    def get_factory_stats(self) -> Dict[str, Any]:
        """获取工厂统计信息
        
        Returns:
            工厂统计信息字典
        """
        return {
            "available_validators": self.get_available_validators(),
            "registered_validator_classes": len(self.registry._validator_classes),
            "registered_strategy_classes": len(self.registry._strategy_classes),
            "registered_factory_functions": len(self.registry._factory_functions),
            "singleton_instances": len(self.registry._singletons),
            "defaults_registered": self._registered_defaults
        }
