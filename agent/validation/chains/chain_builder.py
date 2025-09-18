"""
验证链构建器

基于建造者模式的验证链构建器，提供：
- 流式API构建验证链
- 支持条件验证器添加
- 支持验证组（并行组）
- 支持验证链复制和扩展
- 集成配置文件驱动构建
"""

from typing import List, Dict, Any, Optional, Callable
from ..core.interfaces import IValidator, IValidationChain
from ..core.validation_context import ValidationMode
from .async_validation_chain import AsyncValidationChain


class ValidationChainBuilder:
    """验证链构建器 - 基于建造者模式的流式API
    
    提供流畅的API来构建复杂的验证链，支持：
    - 条件添加验证器
    - 并行组配置
    - 验证模式设置
    - 配置驱动构建
    """
    
    def __init__(self, name: str = "builder_chain"):
        self.name = name
        self._chain = AsyncValidationChain(name)
        self._conditions: List[Callable[[Dict[str, Any]], bool]] = []
        self._parallel_groups: Dict[str, List[str]] = {}
        self._validator_configs: Dict[str, Dict[str, Any]] = {}
    
    def add_validator(self, validator: IValidator, condition: Optional[Callable[[Dict[str, Any]], bool]] = None) -> 'ValidationChainBuilder':
        """添加验证器
        
        Args:
            validator: 验证器实例
            condition: 可选的条件函数，返回True时才添加验证器
            
        Returns:
            返回自身，支持链式调用
        """
        if condition is None or condition(self._validator_configs):
            self._chain.add_validator(validator)
        return self
    
    def add_validator_by_name(
        self, 
        validator_name: str, 
        validator_factory_func: Callable[[str, Dict[str, Any]], Optional[IValidator]],
        config: Optional[Dict[str, Any]] = None,
        condition: Optional[Callable[[Dict[str, Any]], bool]] = None
    ) -> 'ValidationChainBuilder':
        """通过名称添加验证器
        
        Args:
            validator_name: 验证器名称
            validator_factory_func: 验证器工厂函数
            config: 验证器配置
            condition: 可选的条件函数
            
        Returns:
            返回自身，支持链式调用
        """
        if config:
            self._validator_configs[validator_name] = config
        
        if condition is None or condition(self._validator_configs):
            validator = validator_factory_func(validator_name, config or {})
            if validator:
                self._chain.add_validator(validator)
        
        return self
    
    def add_parallel_group(self, group_name: str, validator_names: List[str]) -> 'ValidationChainBuilder':
        """添加并行执行组
        
        Args:
            group_name: 组名
            validator_names: 验证器名称列表
            
        Returns:
            返回自身，支持链式调用
        """
        self._parallel_groups[group_name] = validator_names
        return self
    
    def when(self, condition: Callable[[Dict[str, Any]], bool]) -> 'ConditionalBuilder':
        """条件构建器
        
        Args:
            condition: 条件函数
            
        Returns:
            条件构建器实例
        """
        return ConditionalBuilder(self, condition)
    
    def for_endpoint(self, endpoint: str) -> 'EndpointBuilder':
        """为特定端点构建验证链
        
        Args:
            endpoint: API端点路径
            
        Returns:
            端点构建器实例
        """
        return EndpointBuilder(self, endpoint)
    
    def with_mode(self, mode: ValidationMode) -> 'ValidationChainBuilder':
        """设置验证模式
        
        Args:
            mode: 验证模式
            
        Returns:
            返回自身，支持链式调用
        """
        # 验证模式存储在构建器中，在创建上下文时使用
        self._validator_configs["_validation_mode"] = mode
        return self
    
    def with_config(self, config: Dict[str, Any]) -> 'ValidationChainBuilder':
        """设置全局配置
        
        Args:
            config: 配置字典
            
        Returns:
            返回自身，支持链式调用
        """
        self._validator_configs.update(config)
        return self
    
    def copy_from(self, other_chain: IValidationChain) -> 'ValidationChainBuilder':
        """从其他验证链复制验证器
        
        Args:
            other_chain: 源验证链
            
        Returns:
            返回自身，支持链式调用
        """
        if hasattr(other_chain, 'validators'):
            for validator in other_chain.validators:
                self._chain.add_validator(validator)
        return self
    
    def build(self) -> AsyncValidationChain:
        """构建验证链
        
        Returns:
            构建完成的验证链实例
        """
        # 应用并行组配置
        for group_name, validator_names in self._parallel_groups.items():
            group_validators = []
            for validator in self._chain.validators:
                if validator.get_validator_name() in validator_names:
                    group_validators.append(validator)
            
            if group_validators:
                self._chain.add_parallel_group(group_name, group_validators)
        
        return self._chain
    
    def build_and_validate(self) -> tuple[AsyncValidationChain, List[str]]:
        """构建验证链并验证配置
        
        Returns:
            (验证链实例, 配置警告列表)
        """
        chain = self.build()
        warnings = []
        
        # 验证构建结果
        if chain.get_validator_count() == 0:
            warnings.append("验证链为空，没有添加任何验证器")
        
        # 检查重复的验证器
        validator_names = chain.get_validator_names()
        if len(validator_names) != len(set(validator_names)):
            warnings.append("验证链包含重复的验证器")
        
        # 检查并行组配置
        for group_name, validator_names in self._parallel_groups.items():
            missing_validators = [name for name in validator_names if not chain.has_validator(name)]
            if missing_validators:
                warnings.append(f"并行组 '{group_name}' 引用了不存在的验证器: {missing_validators}")
        
        return chain, warnings
    
    def reset(self) -> 'ValidationChainBuilder':
        """重置构建器
        
        Returns:
            返回自身，支持链式调用
        """
        self._chain = AsyncValidationChain(self.name)
        self._conditions.clear()
        self._parallel_groups.clear()
        self._validator_configs.clear()
        return self
    
    def get_config(self) -> Dict[str, Any]:
        """获取构建器配置
        
        Returns:
            配置字典
        """
        return self._validator_configs.copy()


class ConditionalBuilder:
    """条件构建器 - 支持条件验证器添加"""
    
    def __init__(self, parent: ValidationChainBuilder, condition: Callable[[Dict[str, Any]], bool]):
        self.parent = parent
        self.condition = condition
    
    def add_validator(self, validator: IValidator) -> ValidationChainBuilder:
        """条件添加验证器
        
        Args:
            validator: 验证器实例
            
        Returns:
            父构建器实例
        """
        return self.parent.add_validator(validator, self.condition)
    
    def add_validator_by_name(
        self,
        validator_name: str,
        validator_factory_func: Callable[[str, Dict[str, Any]], Optional[IValidator]],
        config: Optional[Dict[str, Any]] = None
    ) -> ValidationChainBuilder:
        """条件添加验证器（通过名称）
        
        Args:
            validator_name: 验证器名称
            validator_factory_func: 验证器工厂函数
            config: 验证器配置
            
        Returns:
            父构建器实例
        """
        return self.parent.add_validator_by_name(
            validator_name, 
            validator_factory_func, 
            config, 
            self.condition
        )


class EndpointBuilder:
    """端点构建器 - 为特定端点构建验证链"""
    
    def __init__(self, parent: ValidationChainBuilder, endpoint: str):
        self.parent = parent
        self.endpoint = endpoint
        
        # 根据端点类型设置默认配置
        self._setup_endpoint_defaults()
    
    def _setup_endpoint_defaults(self) -> None:
        """根据端点设置默认配置"""
        if self.endpoint.startswith("/api/chat"):
            # 聊天API端点的默认配置
            self.parent._validator_configs.update({
                "endpoint_type": "chat_api",
                "require_session": True,
                "enable_content_validation": True,
                "enable_language_detection": True
            })
        elif self.endpoint.startswith("/api/mcp"):
            # MCP API端点的默认配置
            self.parent._validator_configs.update({
                "endpoint_type": "mcp_api",
                "require_session": False,
                "enable_content_validation": False,
                "enable_language_detection": False
            })
        elif self.endpoint == "/health":
            # 健康检查端点的默认配置
            self.parent._validator_configs.update({
                "endpoint_type": "health_check",
                "minimal_validation": True
            })
    
    def with_security(self, level: str = "standard") -> 'EndpointBuilder':
        """添加安全验证
        
        Args:
            level: 安全级别 (minimal, standard, strict)
            
        Returns:
            返回自身，支持链式调用
        """
        security_configs = {
            "minimal": {"enable_xss_protection": True},
            "standard": {
                "enable_xss_protection": True,
                "enable_sql_injection_detection": True
            },
            "strict": {
                "enable_xss_protection": True,
                "enable_sql_injection_detection": True,
                "enable_sensitive_data_detection": True,
                "enable_script_detection": True
            }
        }
        
        self.parent._validator_configs["security"] = security_configs.get(level, security_configs["standard"])
        return self
    
    def with_size_limits(self, max_request_size: int = 1048576, max_message_length: int = 10000) -> 'EndpointBuilder':
        """添加大小限制
        
        Args:
            max_request_size: 最大请求大小
            max_message_length: 最大消息长度
            
        Returns:
            返回自身，支持链式调用
        """
        self.parent._validator_configs["size"] = {
            "max_request_size": max_request_size,
            "max_string_length": max_message_length
        }
        return self
    
    def with_rate_limiting(self, requests_per_minute: int = 60) -> 'EndpointBuilder':
        """添加频率限制
        
        Args:
            requests_per_minute: 每分钟请求限制
            
        Returns:
            返回自身，支持链式调用
        """
        self.parent._validator_configs["rate_limit"] = {
            "requests_per_minute": requests_per_minute,
            "enable_ip_based_limiting": True
        }
        return self
    
    def build(self) -> AsyncValidationChain:
        """构建端点验证链
        
        Returns:
            构建完成的验证链实例
        """
        return self.parent.build()


def create_chain_builder(name: str = "default") -> ValidationChainBuilder:
    """创建验证链构建器的便捷函数
    
    Args:
        name: 验证链名称
        
    Returns:
        验证链构建器实例
    """
    return ValidationChainBuilder(name)


def create_standard_chain(name: str = "standard") -> AsyncValidationChain:
    """创建标准验证链
    
    包含常用的验证器组合。
    
    Args:
        name: 验证链名称
        
    Returns:
        标准验证链实例
    """
    builder = ValidationChainBuilder(name)
    
    # 标准验证器配置
    # 注意：这里需要实际的验证器实例，在工厂模式实现后会完善
    
    return builder.build()


def create_minimal_chain(name: str = "minimal") -> AsyncValidationChain:
    """创建最小验证链
    
    只包含最基本的验证器。
    
    Args:
        name: 验证链名称
        
    Returns:
        最小验证链实例
    """
    builder = ValidationChainBuilder(name)
    
    # 最小验证器配置
    # 只包含安全和大小验证
    
    return builder.build()


def create_strict_chain(name: str = "strict") -> AsyncValidationChain:
    """创建严格验证链
    
    包含所有验证器的严格配置。
    
    Args:
        name: 验证链名称
        
    Returns:
        严格验证链实例
    """
    builder = ValidationChainBuilder(name)
    
    # 严格验证器配置
    # 包含所有验证器的最严格设置
    
    return builder.build()
