"""
配置工厂

基于工厂模式的配置管理，提供：
- 验证配置加载和解析
- 配置验证和校验
- 环境变量覆盖支持
- 配置缓存和热重载
- 配置模板和继承
"""

import os
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass


@dataclass
class ConfigValidationResult:
    """配置验证结果"""
    is_valid: bool
    warnings: List[str]
    errors: List[str]
    
    def has_issues(self) -> bool:
        """是否有问题"""
        return len(self.warnings) > 0 or len(self.errors) > 0
    
    def get_summary(self) -> str:
        """获取摘要"""
        if not self.has_issues():
            return "配置验证通过"
        return f"配置验证完成：{len(self.errors)} 个错误，{len(self.warnings)} 个警告"


class ConfigTemplate:
    """配置模板 - 预定义的配置模板"""
    
    @staticmethod
    def get_minimal_config() -> Dict[str, Any]:
        """最小配置模板"""
        return {
            "enabled": True,
            "mode": "lenient",
            "max_request_size": 1048576,
            "enable_caching": True,
            "validators": [
                {
                    "name": "security",
                    "type": "security",
                    "enabled": True,
                    "priority": "critical",
                    "config": {"enable_xss_protection": True}
                },
                {
                    "name": "size",
                    "type": "size", 
                    "enabled": True,
                    "priority": "high",
                    "config": {"max_request_size": 1048576}
                }
            ],
            "endpoints": {
                "/api/*": ["security", "size"]
            }
        }
    
    @staticmethod
    def get_standard_config() -> Dict[str, Any]:
        """标准配置模板"""
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
            "validators": [
                {
                    "name": "security",
                    "type": "security",
                    "enabled": True,
                    "priority": "critical",
                    "config": {
                        "enable_xss_protection": True,
                        "enable_sql_injection_detection": True
                    }
                },
                {
                    "name": "size",
                    "type": "size",
                    "enabled": True,
                    "priority": "high",
                    "config": {
                        "max_request_size": 1048576,
                        "max_string_length": 10000
                    }
                },
                {
                    "name": "format",
                    "type": "format",
                    "enabled": True,
                    "priority": "high",
                    "config": {
                        "validate_required_fields": True,
                        "strict_field_types": True
                    }
                },
                {
                    "name": "content",
                    "type": "content",
                    "enabled": True,
                    "priority": "medium",
                    "config": {
                        "max_message_length": 10000,
                        "enable_spam_detection": True
                    }
                }
            ],
            "endpoints": {
                "/api/chat/agent": ["security", "size", "format", "content"],
                "/api/*": ["security", "size", "format"],
                "/health": ["size"]
            }
        }
    
    @staticmethod
    def get_strict_config() -> Dict[str, Any]:
        """严格配置模板"""
        config = ConfigTemplate.get_standard_config()
        
        # 添加更多验证器
        config["validators"].extend([
            {
                "name": "rate_limit",
                "type": "rate_limit",
                "enabled": True,
                "priority": "high",
                "config": {
                    "requests_per_minute": 30,  # 更严格的限制
                    "enable_ip_based_limiting": True
                }
            },
            {
                "name": "language",
                "type": "language",
                "enabled": True,
                "priority": "low",
                "config": {
                    "auto_detect_language": True,
                    "validate_language_consistency": True
                }
            },
            {
                "name": "session",
                "type": "session",
                "enabled": True,
                "priority": "medium",
                "config": {
                    "validate_session_id_format": True,
                    "require_valid_session": False
                }
            }
        ])
        
        # 更新端点配置
        config["endpoints"]["/api/chat/agent"] = [
            "security", "rate_limit", "size", "format", "content", "language", "session"
        ]
        
        return config


class ConfigFactory:
    """配置工厂 - 配置的加载、验证和管理"""
    
    def __init__(self):
        self._config_cache: Dict[str, Dict[str, Any]] = {}
        self._template_cache: Dict[str, Dict[str, Any]] = {}
        
        # 预加载模板
        self._load_templates()
    
    def _load_templates(self) -> None:
        """加载配置模板"""
        self._template_cache["minimal"] = ConfigTemplate.get_minimal_config()
        self._template_cache["standard"] = ConfigTemplate.get_standard_config()
        self._template_cache["strict"] = ConfigTemplate.get_strict_config()
    
    def create_config_from_template(self, template_name: str, overrides: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """从模板创建配置
        
        Args:
            template_name: 模板名称
            overrides: 覆盖配置
            
        Returns:
            配置字典，如果模板不存在则返回None
        """
        if template_name not in self._template_cache:
            return None
        
        # 深度复制模板配置
        config = self._deep_copy_config(self._template_cache[template_name])
        
        # 应用覆盖配置
        if overrides:
            config = self._merge_configs(config, overrides)
        
        return config
    
    def create_config_from_env(self, prefix: str = "GTPLANNER_VALIDATION") -> Dict[str, Any]:
        """从环境变量创建配置
        
        Args:
            prefix: 环境变量前缀
            
        Returns:
            从环境变量构建的配置字典
        """
        config = {}
        
        # 基本配置
        config["enabled"] = self._get_env_bool(f"{prefix}_ENABLED", True)
        config["mode"] = os.getenv(f"{prefix}_MODE", "strict")
        config["max_request_size"] = self._get_env_int(f"{prefix}_MAX_REQUEST_SIZE", 1048576)
        config["max_message_length"] = self._get_env_int(f"{prefix}_MAX_MESSAGE_LENGTH", 10000)
        config["enable_rate_limiting"] = self._get_env_bool(f"{prefix}_ENABLE_RATE_LIMITING", True)
        config["requests_per_minute"] = self._get_env_int(f"{prefix}_REQUESTS_PER_MINUTE", 60)
        config["enable_caching"] = self._get_env_bool(f"{prefix}_ENABLE_CACHING", True)
        config["cache_ttl"] = self._get_env_int(f"{prefix}_CACHE_TTL", 300)
        
        return config
    
    def _get_env_bool(self, key: str, default: bool) -> bool:
        """从环境变量获取布尔值"""
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")
    
    def _get_env_int(self, key: str, default: int) -> int:
        """从环境变量获取整数值"""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default
    
    def validate_config(self, config: Dict[str, Any]) -> ConfigValidationResult:
        """验证配置有效性
        
        Args:
            config: 配置字典
            
        Returns:
            配置验证结果
        """
        warnings = []
        errors = []
        
        # 验证基本字段
        if not isinstance(config.get("enabled"), bool):
            warnings.append("enabled字段应为布尔值")
        
        mode = config.get("mode", "strict")
        valid_modes = ["strict", "lenient", "fail_fast", "continue"]
        if mode not in valid_modes:
            errors.append(f"无效的验证模式: {mode}，有效模式: {valid_modes}")
        
        # 验证数值字段
        max_request_size = config.get("max_request_size", 0)
        if not isinstance(max_request_size, int) or max_request_size <= 0:
            errors.append("max_request_size必须为正整数")
        
        # 验证验证器配置
        validators = config.get("validators", [])
        if not isinstance(validators, list):
            errors.append("validators字段必须为数组")
        else:
            validator_names = set()
            for i, validator_config in enumerate(validators):
                if not isinstance(validator_config, dict):
                    errors.append(f"验证器配置 {i} 必须为对象")
                    continue
                
                name = validator_config.get("name")
                if not name:
                    errors.append(f"验证器配置 {i} 缺少name字段")
                elif name in validator_names:
                    errors.append(f"重复的验证器名称: {name}")
                else:
                    validator_names.add(name)
                
                if not validator_config.get("type"):
                    errors.append(f"验证器 '{name}' 缺少type字段")
        
        # 验证端点配置
        endpoints = config.get("endpoints", {})
        if not isinstance(endpoints, dict):
            errors.append("endpoints字段必须为对象")
        else:
            for endpoint, endpoint_validators in endpoints.items():
                if not isinstance(endpoint_validators, list):
                    errors.append(f"端点 '{endpoint}' 的验证器配置必须为数组")
                    continue
                
                for validator_name in endpoint_validators:
                    if validator_name not in validator_names:
                        warnings.append(f"端点 '{endpoint}' 引用了未定义的验证器: {validator_name}")
        
        return ConfigValidationResult(
            is_valid=len(errors) == 0,
            warnings=warnings,
            errors=errors
        )
    
    def _deep_copy_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """深度复制配置"""
        import copy
        return copy.deepcopy(config)
    
    def _merge_configs(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置"""
        result = base_config.copy()
        
        for key, value in override_config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # 递归合并字典
                result[key] = self._merge_configs(result[key], value)
            else:
                # 直接覆盖
                result[key] = value
        
        return result
    
    def normalize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """标准化配置
        
        Args:
            config: 原始配置
            
        Returns:
            标准化后的配置
        """
        normalized = config.copy()
        
        # 标准化验证模式
        mode = normalized.get("mode", "strict").lower()
        normalized["mode"] = mode
        
        # 标准化验证器优先级
        validators = normalized.get("validators", [])
        for validator_config in validators:
            if "priority" in validator_config:
                priority = validator_config["priority"].lower()
                validator_config["priority"] = priority
        
        # 标准化端点路径
        endpoints = normalized.get("endpoints", {})
        normalized_endpoints = {}
        for endpoint, validator_names in endpoints.items():
            # 确保端点以/开头
            normalized_endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
            normalized_endpoints[normalized_endpoint] = validator_names
        normalized["endpoints"] = normalized_endpoints
        
        return normalized
    
    def get_available_templates(self) -> List[str]:
        """获取可用模板列表
        
        Returns:
            模板名称列表
        """
        return list(self._template_cache.keys())
    
    def register_template(self, template_name: str, config: Dict[str, Any]) -> None:
        """注册配置模板
        
        Args:
            template_name: 模板名称
            config: 配置字典
        """
        self._template_cache[template_name] = self._deep_copy_config(config)
    
    def export_config(self, config: Dict[str, Any], format: str = "dict") -> Union[Dict[str, Any], str]:
        """导出配置
        
        Args:
            config: 配置字典
            format: 导出格式 (dict, json, toml)
            
        Returns:
            导出的配置
        """
        if format == "dict":
            return config
        elif format == "json":
            import json
            return json.dumps(config, indent=2, ensure_ascii=False)
        elif format == "toml":
            try:
                import toml
                return toml.dumps(config)
            except ImportError:
                # 如果没有toml库，返回简化的TOML格式
                return self._dict_to_simple_toml(config)
        else:
            raise ValueError(f"不支持的导出格式: {format}")
    
    def _dict_to_simple_toml(self, config: Dict[str, Any], prefix: str = "") -> str:
        """将字典转换为简单的TOML格式"""
        lines = []
        
        for key, value in config.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                lines.append(f"\n[{full_key}]")
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, str):
                        lines.append(f'{sub_key} = "{sub_value}"')
                    else:
                        lines.append(f'{sub_key} = {sub_value}')
            elif isinstance(value, list):
                lines.append(f'{key} = {value}')
            elif isinstance(value, str):
                lines.append(f'{key} = "{value}"')
            else:
                lines.append(f'{key} = {value}')
        
        return "\n".join(lines)


class ConfigFactory:
    """配置工厂 - 统一的配置创建和管理"""
    
    def __init__(self):
        self.template_manager = ConfigTemplate()
        self._config_cache: Dict[str, Dict[str, Any]] = {}
    
    def create_from_template(self, template_name: str, overrides: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """从模板创建配置
        
        Args:
            template_name: 模板名称 (minimal, standard, strict)
            overrides: 覆盖配置
            
        Returns:
            配置字典，如果模板不存在则返回None
        """
        # 获取模板配置
        if template_name == "minimal":
            base_config = self.template_manager.get_minimal_config()
        elif template_name == "standard":
            base_config = self.template_manager.get_standard_config()
        elif template_name == "strict":
            base_config = self.template_manager.get_strict_config()
        else:
            return None
        
        # 应用覆盖配置
        if overrides:
            base_config = self._merge_configs(base_config, overrides)
        
        return base_config
    
    def create_from_env(self, template_base: str = "standard") -> Dict[str, Any]:
        """从环境变量创建配置
        
        Args:
            template_base: 基础模板名称
            
        Returns:
            配置字典
        """
        # 从模板开始
        config = self.create_from_template(template_base) or {}
        
        # 环境变量覆盖
        env_overrides = self._extract_env_config()
        if env_overrides:
            config = self._merge_configs(config, env_overrides)
        
        return config
    
    def _extract_env_config(self) -> Dict[str, Any]:
        """从环境变量提取配置"""
        prefix = "GTPLANNER_VALIDATION"
        config = {}
        
        # 基本配置
        if os.getenv(f"{prefix}_ENABLED"):
            config["enabled"] = os.getenv(f"{prefix}_ENABLED").lower() in ("true", "1", "yes")
        
        if os.getenv(f"{prefix}_MODE"):
            config["mode"] = os.getenv(f"{prefix}_MODE").lower()
        
        if os.getenv(f"{prefix}_MAX_REQUEST_SIZE"):
            try:
                config["max_request_size"] = int(os.getenv(f"{prefix}_MAX_REQUEST_SIZE"))
            except ValueError:
                pass
        
        if os.getenv(f"{prefix}_REQUESTS_PER_MINUTE"):
            try:
                config["requests_per_minute"] = int(os.getenv(f"{prefix}_REQUESTS_PER_MINUTE"))
            except ValueError:
                pass
        
        return config
    
    def validate_config(self, config: Dict[str, Any]) -> ConfigValidationResult:
        """验证配置
        
        Args:
            config: 配置字典
            
        Returns:
            配置验证结果
        """
        warnings = []
        errors = []
        
        # 验证基本结构
        required_fields = ["enabled", "mode", "validators", "endpoints"]
        for field in required_fields:
            if field not in config:
                warnings.append(f"缺少推荐的配置字段: {field}")
        
        # 验证模式
        mode = config.get("mode", "strict")
        valid_modes = ["strict", "lenient", "fail_fast", "continue"]
        if mode not in valid_modes:
            errors.append(f"无效的验证模式: {mode}")
        
        # 验证验证器配置
        validators = config.get("validators", [])
        validator_names = set()
        
        for validator_config in validators:
            name = validator_config.get("name")
            if not name:
                errors.append("验证器配置缺少name字段")
                continue
            
            if name in validator_names:
                errors.append(f"重复的验证器名称: {name}")
            validator_names.add(name)
            
            if not validator_config.get("type"):
                errors.append(f"验证器 '{name}' 缺少type字段")
        
        # 验证端点配置
        endpoints = config.get("endpoints", {})
        for endpoint, endpoint_validators in endpoints.items():
            if not isinstance(endpoint_validators, list):
                errors.append(f"端点 '{endpoint}' 的验证器配置必须为数组")
                continue
            
            for validator_name in endpoint_validators:
                if validator_name not in validator_names:
                    warnings.append(f"端点 '{endpoint}' 引用了未定义的验证器: {validator_name}")
        
        return ConfigValidationResult(
            is_valid=len(errors) == 0,
            warnings=warnings,
            errors=errors
        )
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get_config_summary(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """获取配置摘要
        
        Args:
            config: 配置字典
            
        Returns:
            配置摘要信息
        """
        validators = config.get("validators", [])
        endpoints = config.get("endpoints", {})
        
        return {
            "enabled": config.get("enabled", False),
            "mode": config.get("mode", "unknown"),
            "validator_count": len(validators),
            "endpoint_count": len(endpoints),
            "validator_names": [v.get("name") for v in validators if v.get("name")],
            "endpoint_paths": list(endpoints.keys()),
            "has_rate_limiting": config.get("enable_rate_limiting", False),
            "has_caching": config.get("enable_caching", False),
            "max_request_size": config.get("max_request_size", 0)
        }


# 全局配置工厂实例
config_factory = ConfigFactory()


def create_config_from_template(template_name: str, overrides: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """创建配置的便捷函数
    
    Args:
        template_name: 模板名称
        overrides: 覆盖配置
        
    Returns:
        配置字典
    """
    return config_factory.create_from_template(template_name, overrides)


def validate_config(config: Dict[str, Any]) -> ConfigValidationResult:
    """验证配置的便捷函数
    
    Args:
        config: 配置字典
        
    Returns:
        配置验证结果
    """
    return config_factory.validate_config(config)
