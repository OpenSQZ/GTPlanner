"""
验证配置管理模块

基于现有的MultilingualConfig扩展，提供验证系统的完整配置管理：
- 继承现有配置系统的所有功能
- 扩展验证相关配置
- 支持验证器配置和端点映射
- 支持环境变量覆盖
- 配置验证和错误处理
"""

import os
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from utils.config_manager import MultilingualConfig
from utils.logger_config import get_logger

from ..core.validation_context import ValidationMode
from ..core.interfaces import ValidatorPriority


logger = get_logger("validation.config")


@dataclass
class ValidatorConfig:
    """单个验证器的配置"""
    name: str
    type: str
    enabled: bool = True
    priority: str = "medium"
    config: Dict[str, Any] = field(default_factory=dict)
    
    def get_priority_enum(self) -> ValidatorPriority:
        """获取优先级枚举值
        
        Returns:
            ValidatorPriority枚举值
        """
        priority_map = {
            "critical": ValidatorPriority.CRITICAL,
            "high": ValidatorPriority.HIGH,
            "medium": ValidatorPriority.MEDIUM,
            "low": ValidatorPriority.LOW
        }
        return priority_map.get(self.priority.lower(), ValidatorPriority.MEDIUM)


@dataclass
class CacheConfig:
    """缓存配置"""
    enabled: bool = True
    backend: str = "memory"
    default_ttl: int = 300
    max_size: int = 1000
    cleanup_interval: int = 60


@dataclass
class MetricsConfig:
    """指标配置"""
    enabled: bool = True
    include_timing: bool = True
    include_success_rate: bool = True
    include_error_details: bool = True
    export_interval: int = 60


@dataclass
class LoggingConfig:
    """验证日志配置"""
    enabled: bool = True
    level: str = "INFO"
    include_request_details: bool = True
    include_validation_path: bool = True
    include_performance_metrics: bool = True
    log_successful_validations: bool = False
    log_failed_validations: bool = True


@dataclass
class ErrorHandlingConfig:
    """错误处理配置"""
    include_suggestions: bool = True
    include_error_codes: bool = True
    include_field_details: bool = True
    mask_sensitive_data: bool = True
    max_error_message_length: int = 500


@dataclass
class StreamingConfig:
    """流式验证配置"""
    enabled: bool = False
    validate_chunks: bool = True
    buffer_size: int = 1024
    timeout: int = 30


class ValidationConfig(MultilingualConfig):
    """验证配置管理器
    
    继承MultilingualConfig，扩展验证系统的配置管理功能。
    提供完整的验证配置加载、验证和管理。
    """
    
    def __init__(self, settings_file: str = "settings.toml"):
        """初始化验证配置管理器
        
        Args:
            settings_file: 配置文件路径
        """
        super().__init__(settings_file)
        self._validation_config = None
        self._load_validation_config()
    
    def _load_validation_config(self) -> None:
        """加载验证配置"""
        try:
            if self._settings:
                self._validation_config = self._settings.get("validation", {})
                logger.info("验证配置加载成功")
            else:
                logger.warning("无法加载验证配置，使用默认配置")
                self._validation_config = self._get_default_validation_config()
        except Exception as e:
            logger.error(f"加载验证配置失败: {e}")
            self._validation_config = self._get_default_validation_config()
    
    def _get_default_validation_config(self) -> Dict[str, Any]:
        """获取默认验证配置
        
        Returns:
            默认验证配置字典
        """
        return {
            "enabled": True,
            "mode": "strict",
            "max_request_size": 1048576,
            "max_message_length": 10000,
            "enable_rate_limiting": True,
            "requests_per_minute": 60,
            "enable_caching": True,
            "cache_ttl": 300,
            "enable_metrics": True,
            "enable_streaming_validation": False,
            "enable_parallel_validation": True,
            "excluded_paths": ["/health", "/metrics", "/static"],
            "included_paths": ["/api"],
            "endpoints": {},
            "validators": [],
            "cache": {"enabled": True, "backend": "memory"},
            "metrics": {"enabled": True},
            "logging": {"enabled": True, "level": "INFO"},
            "error_handling": {"include_suggestions": True},
            "streaming": {"enabled": False}
        }
    
    @property
    def enabled(self) -> bool:
        """验证系统是否启用
        
        Returns:
            True表示启用，False表示禁用
        """
        return self._validation_config.get("enabled", True)
    
    @property
    def mode(self) -> ValidationMode:
        """获取验证模式
        
        Returns:
            ValidationMode枚举值
        """
        mode_str = self._validation_config.get("mode", "strict").lower()
        mode_map = {
            "strict": ValidationMode.STRICT,
            "lenient": ValidationMode.LENIENT,
            "fail_fast": ValidationMode.FAIL_FAST,
            "continue": ValidationMode.CONTINUE
        }
        return mode_map.get(mode_str, ValidationMode.STRICT)
    
    @property
    def max_request_size(self) -> int:
        """最大请求大小（字节）
        
        Returns:
            最大请求大小
        """
        return self._validation_config.get("max_request_size", 1048576)
    
    @property
    def max_message_length(self) -> int:
        """最大消息长度
        
        Returns:
            最大消息长度
        """
        return self._validation_config.get("max_message_length", 10000)
    
    @property
    def enable_rate_limiting(self) -> bool:
        """是否启用频率限制
        
        Returns:
            True表示启用，False表示禁用
        """
        return self._validation_config.get("enable_rate_limiting", True)
    
    @property
    def requests_per_minute(self) -> int:
        """每分钟请求限制
        
        Returns:
            每分钟最大请求数
        """
        return self._validation_config.get("requests_per_minute", 60)
    
    @property
    def enable_caching(self) -> bool:
        """是否启用缓存
        
        Returns:
            True表示启用，False表示禁用
        """
        return self._validation_config.get("enable_caching", True)
    
    @property
    def cache_ttl(self) -> int:
        """缓存生存时间（秒）
        
        Returns:
            缓存TTL
        """
        return self._validation_config.get("cache_ttl", 300)
    
    @property
    def enable_metrics(self) -> bool:
        """是否启用指标收集
        
        Returns:
            True表示启用，False表示禁用
        """
        return self._validation_config.get("enable_metrics", True)
    
    @property
    def enable_streaming_validation(self) -> bool:
        """是否启用流式验证
        
        Returns:
            True表示启用，False表示禁用
        """
        return self._validation_config.get("enable_streaming_validation", False)
    
    @property
    def enable_parallel_validation(self) -> bool:
        """是否启用并行验证
        
        Returns:
            True表示启用，False表示禁用
        """
        return self._validation_config.get("enable_parallel_validation", True)
    
    @property
    def excluded_paths(self) -> List[str]:
        """排除的路径列表
        
        Returns:
            排除路径列表
        """
        return self._validation_config.get("excluded_paths", ["/health", "/metrics", "/static"])
    
    @property
    def included_paths(self) -> List[str]:
        """包含的路径列表
        
        Returns:
            包含路径列表
        """
        return self._validation_config.get("included_paths", ["/api"])
    
    def get_endpoint_validators(self, endpoint: str) -> List[str]:
        """获取端点的验证器列表
        
        Args:
            endpoint: API端点路径
            
        Returns:
            验证器名称列表
        """
        endpoints_config = self._validation_config.get("endpoints", {})
        
        # 直接匹配
        if endpoint in endpoints_config:
            return endpoints_config[endpoint]
        
        # 通配符匹配
        for pattern, validators in endpoints_config.items():
            if pattern.endswith("/*") and endpoint.startswith(pattern[:-2]):
                return validators
        
        # 默认验证器（如果没有匹配的端点配置）
        return ["security", "size", "format"]
    
    def get_validator_configs(self) -> List[ValidatorConfig]:
        """获取所有验证器配置
        
        Returns:
            ValidatorConfig对象列表
        """
        validators_config = self._validation_config.get("validators", [])
        validator_configs = []
        
        for validator_data in validators_config:
            try:
                validator_config = ValidatorConfig(
                    name=validator_data.get("name"),
                    type=validator_data.get("type"),
                    enabled=validator_data.get("enabled", True),
                    priority=validator_data.get("priority", "medium"),
                    config=validator_data.get("config", {})
                )
                validator_configs.append(validator_config)
            except Exception as e:
                logger.warning(f"跳过无效的验证器配置: {e}")
        
        return validator_configs
    
    def get_validator_config(self, validator_name: str) -> Optional[ValidatorConfig]:
        """获取指定验证器的配置
        
        Args:
            validator_name: 验证器名称
            
        Returns:
            ValidatorConfig对象，如果不存在则返回None
        """
        for config in self.get_validator_configs():
            if config.name == validator_name:
                return config
        return None
    
    def get_cache_config(self) -> CacheConfig:
        """获取缓存配置
        
        Returns:
            CacheConfig对象
        """
        cache_data = self._validation_config.get("cache", {})
        return CacheConfig(
            enabled=cache_data.get("enabled", True),
            backend=cache_data.get("backend", "memory"),
            default_ttl=cache_data.get("default_ttl", 300),
            max_size=cache_data.get("max_size", 1000),
            cleanup_interval=cache_data.get("cleanup_interval", 60)
        )
    
    def get_metrics_config(self) -> MetricsConfig:
        """获取指标配置
        
        Returns:
            MetricsConfig对象
        """
        metrics_data = self._validation_config.get("metrics", {})
        return MetricsConfig(
            enabled=metrics_data.get("enabled", True),
            include_timing=metrics_data.get("include_timing", True),
            include_success_rate=metrics_data.get("include_success_rate", True),
            include_error_details=metrics_data.get("include_error_details", True),
            export_interval=metrics_data.get("export_interval", 60)
        )
    
    def get_logging_config(self) -> LoggingConfig:
        """获取日志配置
        
        Returns:
            LoggingConfig对象
        """
        logging_data = self._validation_config.get("logging", {})
        return LoggingConfig(
            enabled=logging_data.get("enabled", True),
            level=logging_data.get("level", "INFO"),
            include_request_details=logging_data.get("include_request_details", True),
            include_validation_path=logging_data.get("include_validation_path", True),
            include_performance_metrics=logging_data.get("include_performance_metrics", True),
            log_successful_validations=logging_data.get("log_successful_validations", False),
            log_failed_validations=logging_data.get("log_failed_validations", True)
        )
    
    def get_error_handling_config(self) -> ErrorHandlingConfig:
        """获取错误处理配置
        
        Returns:
            ErrorHandlingConfig对象
        """
        error_data = self._validation_config.get("error_handling", {})
        return ErrorHandlingConfig(
            include_suggestions=error_data.get("include_suggestions", True),
            include_error_codes=error_data.get("include_error_codes", True),
            include_field_details=error_data.get("include_field_details", True),
            mask_sensitive_data=error_data.get("mask_sensitive_data", True),
            max_error_message_length=error_data.get("max_error_message_length", 500)
        )
    
    def get_streaming_config(self) -> StreamingConfig:
        """获取流式配置
        
        Returns:
            StreamingConfig对象
        """
        streaming_data = self._validation_config.get("streaming", {})
        return StreamingConfig(
            enabled=streaming_data.get("enabled", False),
            validate_chunks=streaming_data.get("validate_chunks", True),
            buffer_size=streaming_data.get("buffer_size", 1024),
            timeout=streaming_data.get("timeout", 30)
        )
    
    def is_endpoint_validation_enabled(self, endpoint: str) -> bool:
        """检查端点是否启用验证
        
        Args:
            endpoint: API端点路径
            
        Returns:
            True表示启用验证，False表示禁用
        """
        if not self.enabled:
            return False
        
        # 检查排除路径
        for excluded_path in self.excluded_paths:
            if endpoint.startswith(excluded_path):
                return False
        
        # 检查包含路径
        if self.included_paths:
            return any(endpoint.startswith(included) for included in self.included_paths)
        
        # 默认启用验证
        return True
    
    def get_validator_priority(self, validator_name: str) -> ValidatorPriority:
        """获取验证器优先级
        
        Args:
            validator_name: 验证器名称
            
        Returns:
            ValidatorPriority枚举值
        """
        priorities = self._validation_config.get("priorities", {})
        priority_str = priorities.get(validator_name, "medium")
        
        priority_map = {
            "critical": ValidatorPriority.CRITICAL,
            "high": ValidatorPriority.HIGH,
            "medium": ValidatorPriority.MEDIUM,
            "low": ValidatorPriority.LOW
        }
        
        return priority_map.get(priority_str.lower(), ValidatorPriority.MEDIUM)
    
    def validate_config(self) -> List[str]:
        """验证配置的有效性
        
        Returns:
            配置警告和错误列表
        """
        warnings = []
        
        # 调用父类的配置验证
        parent_warnings = super().validate_config()
        warnings.extend(parent_warnings)
        
        # 验证验证系统配置
        if not self._validation_config:
            warnings.append("验证配置不存在，使用默认配置")
            return warnings
        
        # 验证模式
        mode = self._validation_config.get("mode", "strict")
        valid_modes = ["strict", "lenient", "fail_fast", "continue"]
        if mode not in valid_modes:
            warnings.append(f"无效的验证模式 '{mode}'，支持的模式: {valid_modes}")
        
        # 验证大小限制
        max_request_size = self.max_request_size
        if max_request_size <= 0:
            warnings.append(f"无效的最大请求大小: {max_request_size}")
        
        # 验证验证器配置
        validator_configs = self.get_validator_configs()
        validator_names = set()
        
        for config in validator_configs:
            if not config.name:
                warnings.append("发现没有名称的验证器配置")
                continue
            
            if config.name in validator_names:
                warnings.append(f"重复的验证器名称: {config.name}")
            validator_names.add(config.name)
            
            if not config.type:
                warnings.append(f"验证器 '{config.name}' 没有指定类型")
        
        # 验证端点配置
        endpoints = self._validation_config.get("endpoints", {})
        for endpoint, validators in endpoints.items():
            if not isinstance(validators, list):
                warnings.append(f"端点 '{endpoint}' 的验证器配置必须是列表")
                continue
            
            for validator_name in validators:
                if validator_name not in validator_names:
                    warnings.append(f"端点 '{endpoint}' 引用了未定义的验证器: {validator_name}")
        
        # 验证缓存配置
        cache_config = self.get_cache_config()
        if cache_config.enabled and cache_config.backend not in ["memory", "redis"]:
            warnings.append(f"不支持的缓存后端: {cache_config.backend}")
        
        return warnings
    
    def get_all_validation_config(self) -> Dict[str, Any]:
        """获取所有验证配置
        
        Returns:
            包含所有验证配置的字典
        """
        return {
            "enabled": self.enabled,
            "mode": self.mode.value,
            "max_request_size": self.max_request_size,
            "max_message_length": self.max_message_length,
            "enable_rate_limiting": self.enable_rate_limiting,
            "requests_per_minute": self.requests_per_minute,
            "enable_caching": self.enable_caching,
            "cache_ttl": self.cache_ttl,
            "enable_metrics": self.enable_metrics,
            "enable_streaming_validation": self.enable_streaming_validation,
            "enable_parallel_validation": self.enable_parallel_validation,
            "excluded_paths": self.excluded_paths,
            "included_paths": self.included_paths,
            "validator_configs": [
                {
                    "name": config.name,
                    "type": config.type,
                    "enabled": config.enabled,
                    "priority": config.priority,
                    "config": config.config
                }
                for config in self.get_validator_configs()
            ],
            "cache": self.get_cache_config().__dict__,
            "metrics": self.get_metrics_config().__dict__,
            "logging": self.get_logging_config().__dict__,
            "error_handling": self.get_error_handling_config().__dict__,
            "streaming": self.get_streaming_config().__dict__
        }
    
    def reload_config(self) -> None:
        """重新加载配置
        
        用于支持配置热重载
        """
        logger.info("重新加载验证配置")
        self._load_settings()  # 重新加载父类配置
        self._load_validation_config()  # 重新加载验证配置
        
        # 验证新配置
        warnings = self.validate_config()
        if warnings:
            logger.warning(f"配置重载完成，发现 {len(warnings)} 个警告:")
            for warning in warnings:
                logger.warning(f"  - {warning}")
        else:
            logger.info("配置重载完成，无警告")


# 全局验证配置管理器实例
validation_config = ValidationConfig()


def get_validation_config() -> ValidationConfig:
    """获取全局验证配置管理器
    
    Returns:
        ValidationConfig实例
    """
    return validation_config


def reload_validation_config() -> None:
    """重新加载验证配置"""
    validation_config.reload_config()