"""
验证链工厂

基于工厂模式的验证链创建和管理，提供：
- 端点级别的验证链创建
- 验证链模板管理
- 动态验证链配置
- 验证链缓存机制
- 热重载支持
"""

import re
from typing import Dict, Any, Optional, List, Pattern
from ..core.interfaces import IValidationChain
from ..chains.async_validation_chain import AsyncValidationChain
from ..chains.chain_builder import ValidationChainBuilder
from .validator_factory import ValidatorFactory


class EndpointMatcher:
    """端点匹配器 - 支持路径模式匹配"""
    
    def __init__(self):
        self._exact_matches: Dict[str, List[str]] = {}
        self._pattern_matches: List[tuple[Pattern, List[str]]] = []
    
    def add_exact_match(self, endpoint: str, validator_names: List[str]) -> None:
        """添加精确匹配
        
        Args:
            endpoint: 端点路径
            validator_names: 验证器名称列表
        """
        self._exact_matches[endpoint] = validator_names
    
    def add_pattern_match(self, pattern: str, validator_names: List[str]) -> None:
        """添加模式匹配
        
        Args:
            pattern: 路径模式（支持通配符）
            validator_names: 验证器名称列表
        """
        # 将通配符模式转换为正则表达式
        regex_pattern = pattern.replace("*", ".*").replace("?", ".") 
        compiled_pattern = re.compile(f"^{regex_pattern}$")
        self._pattern_matches.append((compiled_pattern, validator_names))
    
    def match(self, endpoint: str) -> Optional[List[str]]:
        """匹配端点并返回验证器列表
        
        Args:
            endpoint: 端点路径
            
        Returns:
            验证器名称列表，如果没有匹配则返回None
        """
        # 优先精确匹配
        if endpoint in self._exact_matches:
            return self._exact_matches[endpoint]
        
        # 模式匹配
        for pattern, validator_names in self._pattern_matches:
            if pattern.match(endpoint):
                return validator_names
        
        return None
    
    def get_all_endpoints(self) -> List[str]:
        """获取所有配置的端点
        
        Returns:
            端点列表
        """
        endpoints = list(self._exact_matches.keys())
        endpoints.extend([pattern.pattern for pattern, _ in self._pattern_matches])
        return endpoints


class ValidationChainCache:
    """验证链缓存 - 提升链创建性能"""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._cache: Dict[str, AsyncValidationChain] = {}
        self._access_order: List[str] = []
    
    def get(self, cache_key: str) -> Optional[AsyncValidationChain]:
        """获取缓存的验证链
        
        Args:
            cache_key: 缓存键
            
        Returns:
            验证链实例，如果不存在则返回None
        """
        if cache_key in self._cache:
            # 更新访问顺序
            self._access_order.remove(cache_key)
            self._access_order.append(cache_key)
            
            # 克隆验证链以避免状态污染
            return self._cache[cache_key].clone()
        
        return None
    
    def set(self, cache_key: str, chain: AsyncValidationChain) -> None:
        """设置缓存的验证链
        
        Args:
            cache_key: 缓存键
            chain: 验证链实例
        """
        # 检查缓存大小限制
        if len(self._cache) >= self.max_size:
            # 移除最久未访问的条目
            oldest_key = self._access_order.pop(0)
            del self._cache[oldest_key]
        
        # 添加到缓存
        self._cache[cache_key] = chain.clone()  # 存储克隆版本
        self._access_order.append(cache_key)
    
    def invalidate(self, pattern: str) -> int:
        """失效匹配模式的缓存
        
        Args:
            pattern: 匹配模式
            
        Returns:
            失效的缓存条目数量
        """
        pattern_regex = re.compile(pattern.replace("*", ".*"))
        invalidated_keys = []
        
        for key in self._cache.keys():
            if pattern_regex.match(key):
                invalidated_keys.append(key)
        
        for key in invalidated_keys:
            del self._cache[key]
            self._access_order.remove(key)
        
        return len(invalidated_keys)
    
    def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()
        self._access_order.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            缓存统计信息字典
        """
        return {
            "cache_size": len(self._cache),
            "max_size": self.max_size,
            "cached_chains": list(self._cache.keys())
        }


class ValidationChainFactory:
    """验证链工厂 - 端点级别的验证链创建和管理"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.validator_factory = ValidatorFactory(config)
        self.endpoint_matcher = EndpointMatcher()
        self.chain_cache = ValidationChainCache(max_size=self.config.get("cache_max_size", 100))
        self._templates: Dict[str, AsyncValidationChain] = {}
        
        # 初始化默认配置
        self._setup_default_endpoints()
    
    def _setup_default_endpoints(self) -> None:
        """设置默认端点配置"""
        # 从配置中加载端点映射
        endpoints_config = self.config.get("endpoints", {})
        
        for endpoint, validator_names in endpoints_config.items():
            if "*" in endpoint or "?" in endpoint:
                self.endpoint_matcher.add_pattern_match(endpoint, validator_names)
            else:
                self.endpoint_matcher.add_exact_match(endpoint, validator_names)
        
        # 如果没有配置，添加默认端点
        if not endpoints_config:
            self._setup_fallback_endpoints()
    
    def _setup_fallback_endpoints(self) -> None:
        """设置回退端点配置"""
        # API端点默认配置
        self.endpoint_matcher.add_pattern_match(
            "/api/*", 
            ["security", "size", "format"]
        )
        
        # 聊天API特殊配置
        self.endpoint_matcher.add_exact_match(
            "/api/chat/agent",
            ["security", "rate_limit", "size", "format", "content", "language", "session"]
        )
        
        # 健康检查最小配置
        self.endpoint_matcher.add_exact_match(
            "/health",
            ["size"]
        )
    
    def create_chain_for_endpoint(self, endpoint: str) -> Optional[AsyncValidationChain]:
        """为端点创建验证链
        
        Args:
            endpoint: API端点路径
            
        Returns:
            验证链实例，如果没有匹配的配置则返回None
        """
        # 检查缓存
        cache_key = f"endpoint:{endpoint}"
        cached_chain = self.chain_cache.get(cache_key)
        if cached_chain:
            return cached_chain
        
        # 匹配端点配置
        validator_names = self.endpoint_matcher.match(endpoint)
        if not validator_names:
            return None
        
        # 创建验证链
        chain = self._create_chain_from_names(endpoint, validator_names)
        
        # 缓存验证链
        if chain:
            self.chain_cache.set(cache_key, chain)
        
        return chain
    
    def _create_chain_from_names(self, chain_name: str, validator_names: List[str]) -> Optional[AsyncValidationChain]:
        """从验证器名称列表创建验证链
        
        Args:
            chain_name: 验证链名称
            validator_names: 验证器名称列表
            
        Returns:
            验证链实例
        """
        # 创建验证器实例
        validators = self.validator_factory.create_validators_by_names(validator_names)
        
        if not validators:
            return None
        
        # 构建验证链
        chain = AsyncValidationChain(chain_name)
        for validator in validators:
            chain.add_validator(validator)
        
        return chain
    
    def create_chain_from_config(self, chain_config: Dict[str, Any]) -> Optional[AsyncValidationChain]:
        """从配置创建验证链
        
        Args:
            chain_config: 验证链配置
            
        Returns:
            验证链实例
        """
        chain_name = chain_config.get("name", "config_chain")
        validator_configs = chain_config.get("validators", [])
        
        if not validator_configs:
            return None
        
        # 创建验证器
        validators = self.validator_factory.create_validators(validator_configs)
        
        if not validators:
            return None
        
        # 构建验证链
        chain = AsyncValidationChain(chain_name)
        for validator in validators:
            chain.add_validator(validator)
        
        # 配置并行组
        parallel_groups = chain_config.get("parallel_groups", {})
        for group_name, group_validator_names in parallel_groups.items():
            group_validators = [v for v in validators if v.get_validator_name() in group_validator_names]
            if group_validators:
                chain.add_parallel_group(group_name, group_validators)
        
        return chain
    
    def create_template_chain(self, template_name: str) -> Optional[AsyncValidationChain]:
        """创建模板验证链
        
        Args:
            template_name: 模板名称
            
        Returns:
            验证链实例
        """
        if template_name in self._templates:
            return self._templates[template_name].clone()
        
        # 创建预定义模板
        if template_name == "minimal":
            return self._create_minimal_template()
        elif template_name == "standard":
            return self._create_standard_template()
        elif template_name == "strict":
            return self._create_strict_template()
        elif template_name == "api_only":
            return self._create_api_template()
        
        return None
    
    def _create_minimal_template(self) -> AsyncValidationChain:
        """创建最小模板"""
        validators = self.validator_factory.create_validators_by_names(["security", "size"])
        chain = AsyncValidationChain("minimal_template")
        for validator in validators:
            chain.add_validator(validator)
        return chain
    
    def _create_standard_template(self) -> AsyncValidationChain:
        """创建标准模板"""
        validators = self.validator_factory.create_validators_by_names([
            "security", "size", "format", "content"
        ])
        chain = AsyncValidationChain("standard_template")
        for validator in validators:
            chain.add_validator(validator)
        return chain
    
    def _create_strict_template(self) -> AsyncValidationChain:
        """创建严格模板"""
        validators = self.validator_factory.create_validators_by_names([
            "security", "rate_limit", "size", "format", "content", "language", "session"
        ])
        chain = AsyncValidationChain("strict_template")
        for validator in validators:
            chain.add_validator(validator)
        return chain
    
    def _create_api_template(self) -> AsyncValidationChain:
        """创建API模板"""
        validators = self.validator_factory.create_validators_by_names([
            "security", "rate_limit", "size", "format"
        ])
        chain = AsyncValidationChain("api_template")
        for validator in validators:
            chain.add_validator(validator)
        return chain
    
    def register_template(self, template_name: str, chain: AsyncValidationChain) -> None:
        """注册验证链模板
        
        Args:
            template_name: 模板名称
            chain: 验证链实例
        """
        self._templates[template_name] = chain.clone()
    
    def get_available_templates(self) -> List[str]:
        """获取可用模板列表
        
        Returns:
            模板名称列表
        """
        predefined = ["minimal", "standard", "strict", "api_only"]
        custom = list(self._templates.keys())
        return predefined + custom
    
    def reload_config(self, new_config: Dict[str, Any]) -> None:
        """重新加载配置
        
        Args:
            new_config: 新的配置
        """
        self.config = new_config
        self.validator_factory = ValidatorFactory(new_config)
        
        # 清空缓存
        self.chain_cache.clear()
        
        # 重新设置端点配置
        self.endpoint_matcher = EndpointMatcher()
        self._setup_default_endpoints()
    
    def invalidate_cache(self, pattern: str = "*") -> int:
        """失效缓存
        
        Args:
            pattern: 匹配模式，默认失效所有
            
        Returns:
            失效的缓存条目数量
        """
        return self.chain_cache.invalidate(pattern)
    
    def get_factory_stats(self) -> Dict[str, Any]:
        """获取工厂统计信息
        
        Returns:
            工厂统计信息字典
        """
        return {
            "configured_endpoints": len(self.endpoint_matcher._exact_matches),
            "pattern_endpoints": len(self.endpoint_matcher._pattern_matches),
            "cached_chains": self.chain_cache.get_stats(),
            "available_templates": self.get_available_templates(),
            "validator_factory_stats": self.validator_factory.get_factory_stats()
        }
    
    def validate_endpoint_config(self) -> List[str]:
        """验证端点配置
        
        Returns:
            配置警告列表
        """
        warnings = []
        
        # 检查端点配置
        all_endpoints = self.endpoint_matcher.get_all_endpoints()
        if not all_endpoints:
            warnings.append("没有配置任何端点验证规则")
        
        # 检查验证器可用性
        available_validators = self.validator_factory.get_available_validators()
        
        for endpoint in self.endpoint_matcher._exact_matches:
            validator_names = self.endpoint_matcher._exact_matches[endpoint]
            for validator_name in validator_names:
                if validator_name not in available_validators:
                    warnings.append(f"端点 '{endpoint}' 引用了不可用的验证器: {validator_name}")
        
        for pattern, validator_names in self.endpoint_matcher._pattern_matches:
            for validator_name in validator_names:
                if validator_name not in available_validators:
                    warnings.append(f"端点模式 '{pattern.pattern}' 引用了不可用的验证器: {validator_name}")
        
        return warnings


def create_chain_factory(config: Optional[Dict[str, Any]] = None) -> ValidationChainFactory:
    """创建验证链工厂的便捷函数
    
    Args:
        config: 工厂配置
        
    Returns:
        验证链工厂实例
    """
    return ValidationChainFactory(config)


def create_default_chain() -> AsyncValidationChain:
    """创建默认验证链
    
    Returns:
        默认验证链实例
    """
    factory = ValidationChainFactory()
    return factory.create_template_chain("standard") or AsyncValidationChain("default")
