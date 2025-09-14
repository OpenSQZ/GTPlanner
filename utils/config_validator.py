"""
配置验证器

为GTPlanner提供全面的配置验证和优化功能，包括：
- 配置项验证
- 环境变量检查
- 配置优化建议
- 配置热重载
- 配置文档生成
"""

import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import toml

logger = logging.getLogger(__name__)


@dataclass
class ConfigValidationResult:
    """配置验证结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    optimized_config: Optional[Dict[str, Any]] = None


@dataclass
class ConfigItem:
    """配置项定义"""
    key: str
    required: bool
    data_type: type
    default_value: Any = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[Any]] = None
    description: str = ""
    env_var: Optional[str] = None


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self):
        self.config_schema: Dict[str, ConfigItem] = {}
        self._define_schema()
        
    def _define_schema(self):
        """定义配置模式"""
        schema = [
            # 基础配置
            ConfigItem("debug", False, bool, False, description="启用调试模式"),
            
            # 日志配置
            ConfigItem("logging.level", True, str, "INFO", 
                      allowed_values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                      description="日志级别"),
            ConfigItem("logging.file_enabled", False, bool, True, description="启用文件日志"),
            ConfigItem("logging.console_enabled", False, bool, False, description="启用控制台日志"),
            ConfigItem("logging.max_file_size", False, int, 10485760, min_value=1024,
                      description="最大日志文件大小（字节）"),
            ConfigItem("logging.backup_count", False, int, 5, min_value=1, max_value=50,
                      description="日志备份文件数量"),
            
            # LLM配置
            ConfigItem("llm.base_url", True, str, description="LLM API基础URL", env_var="LLM_BASE_URL"),
            ConfigItem("llm.api_key", True, str, description="LLM API密钥", env_var="LLM_API_KEY"),
            ConfigItem("llm.model", True, str, description="LLM模型名称"),
            ConfigItem("llm.max_tokens", False, int, 4000, min_value=100, max_value=32000,
                      description="最大token数"),
            ConfigItem("llm.temperature", False, float, 0.7, min_value=0.0, max_value=2.0,
                      description="温度参数"),
            ConfigItem("llm.timeout", False, int, 30, min_value=5, max_value=300,
                      description="请求超时时间（秒）"),
            ConfigItem("llm.retry_attempts", False, int, 3, min_value=1, max_value=10,
                      description="重试次数"),
            ConfigItem("llm.retry_delay", False, float, 1.0, min_value=0.1, max_value=60.0,
                      description="重试延迟（秒）"),
            
            # Jina配置
            ConfigItem("jina.api_key", False, str, description="Jina API密钥", env_var="JINA_API_KEY"),
            ConfigItem("jina.search_base_url", False, str, "https://s.jina.ai/",
                      description="Jina搜索API基础URL"),
            ConfigItem("jina.web_base_url", False, str, "https://r.jina.ai/",
                      description="Jina网页API基础URL"),
            ConfigItem("jina.timeout", False, int, 30, min_value=5, max_value=300,
                      description="Jina请求超时时间（秒）"),
            ConfigItem("jina.retry_attempts", False, int, 3, min_value=1, max_value=10,
                      description="Jina重试次数"),
            
            # 多语言配置
            ConfigItem("multilingual.default_language", False, str, "en",
                      allowed_values=["en", "zh", "es", "fr", "ja"],
                      description="默认语言"),
            ConfigItem("multilingual.auto_detect", False, bool, True, description="启用自动语言检测"),
            ConfigItem("multilingual.fallback_enabled", False, bool, True, description="启用回退机制"),
            ConfigItem("multilingual.supported_languages", False, list, ["en", "zh", "es", "fr", "ja"],
                      description="支持的语言列表"),
            
            # 性能配置
            ConfigItem("performance.enable_caching", False, bool, True, description="启用缓存"),
            ConfigItem("performance.cache_ttl", False, int, 3600, min_value=60, max_value=86400,
                      description="缓存TTL（秒）"),
            ConfigItem("performance.max_cache_size", False, int, 2000, min_value=100, max_value=10000,
                      description="最大缓存条目数"),
            ConfigItem("performance.max_cache_memory_mb", False, int, 200, min_value=10, max_value=2000,
                      description="最大缓存内存（MB）"),
            ConfigItem("performance.enable_monitoring", False, bool, True, description="启用性能监控"),
            ConfigItem("performance.monitoring_interval", False, float, 5.0, min_value=1.0, max_value=60.0,
                      description="监控间隔（秒）"),
            ConfigItem("performance.enable_compression", False, bool, True, description="启用压缩"),
            ConfigItem("performance.compression_threshold_messages", False, int, 50, min_value=10, max_value=1000,
                      description="压缩阈值（消息数）"),
            ConfigItem("performance.compression_threshold_tokens", False, int, 8000, min_value=1000, max_value=100000,
                      description="压缩阈值（token数）"),
            
            # 数据库配置
            ConfigItem("database.connection_pool_size", False, int, 10, min_value=1, max_value=100,
                      description="连接池大小"),
            ConfigItem("database.connection_timeout", False, int, 30, min_value=5, max_value=300,
                      description="连接超时时间（秒）"),
            ConfigItem("database.query_timeout", False, int, 30, min_value=5, max_value=300,
                      description="查询超时时间（秒）"),
            ConfigItem("database.enable_wal_mode", False, bool, True, description="启用WAL模式"),
            ConfigItem("database.enable_foreign_keys", False, bool, True, description="启用外键约束"),
            ConfigItem("database.vacuum_interval_hours", False, int, 24, min_value=1, max_value=168,
                      description="VACUUM间隔（小时）"),
            
            # 错误处理配置
            ConfigItem("error_handling.enable_retry", False, bool, True, description="启用重试机制"),
            ConfigItem("error_handling.max_retry_attempts", False, int, 3, min_value=1, max_value=10,
                      description="最大重试次数"),
            ConfigItem("error_handling.retry_base_delay", False, float, 1.0, min_value=0.1, max_value=60.0,
                      description="重试基础延迟（秒）"),
            ConfigItem("error_handling.retry_max_delay", False, float, 60.0, min_value=1.0, max_value=300.0,
                      description="重试最大延迟（秒）"),
            ConfigItem("error_handling.enable_exponential_backoff", False, bool, True, description="启用指数退避"),
            ConfigItem("error_handling.enable_jitter", False, bool, True, description="启用抖动"),
            ConfigItem("error_handling.log_all_errors", False, bool, True, description="记录所有错误"),
            ConfigItem("error_handling.error_history_size", False, int, 1000, min_value=100, max_value=10000,
                      description="错误历史大小"),
            
            # 安全配置
            ConfigItem("security.enable_input_validation", False, bool, True, description="启用输入验证"),
            ConfigItem("security.max_input_length", False, int, 10000, min_value=100, max_value=100000,
                      description="最大输入长度"),
            ConfigItem("security.enable_rate_limiting", False, bool, True, description="启用速率限制"),
            ConfigItem("security.rate_limit_requests_per_minute", False, int, 60, min_value=1, max_value=1000,
                      description="每分钟请求限制"),
            ConfigItem("security.enable_api_key_validation", False, bool, True, description="启用API密钥验证"),
        ]
        
        # 构建配置模式字典
        for item in schema:
            self.config_schema[item.key] = item
    
    def validate_config(self, config: Dict[str, Any]) -> ConfigValidationResult:
        """验证配置"""
        errors = []
        warnings = []
        suggestions = []
        
        # 检查必需配置项
        for key, item in self.config_schema.items():
            if item.required and not self._has_nested_key(config, key):
                errors.append(f"缺少必需的配置项: {key}")
        
        # 验证配置值
        for key, item in self.config_schema.items():
            value = self._get_nested_value(config, key)
            if value is not None:
                validation_result = self._validate_value(key, value, item)
                errors.extend(validation_result.get("errors", []))
                warnings.extend(validation_result.get("warnings", []))
                suggestions.extend(validation_result.get("suggestions", []))
        
        # 生成优化建议
        suggestions.extend(self._generate_optimization_suggestions(config))
        
        # 创建优化后的配置
        optimized_config = self._optimize_config(config)
        
        return ConfigValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            optimized_config=optimized_config
        )
    
    def _has_nested_key(self, config: Dict[str, Any], key: str) -> bool:
        """检查嵌套键是否存在"""
        keys = key.split('.')
        current = config
        
        for k in keys:
            if not isinstance(current, dict) or k not in current:
                return False
            current = current[k]
        
        return True
    
    def _get_nested_value(self, config: Dict[str, Any], key: str) -> Any:
        """获取嵌套值"""
        keys = key.split('.')
        current = config
        
        for k in keys:
            if not isinstance(current, dict) or k not in current:
                return None
            current = current[k]
        
        return current
    
    def _validate_value(self, key: str, value: Any, item: ConfigItem) -> Dict[str, List[str]]:
        """验证单个值"""
        errors = []
        warnings = []
        suggestions = []
        
        # 检查数据类型
        if not isinstance(value, item.data_type):
            errors.append(f"配置项 {key} 的类型错误，期望 {item.data_type.__name__}，实际 {type(value).__name__}")
            return {"errors": errors, "warnings": warnings, "suggestions": suggestions}
        
        # 检查数值范围
        if isinstance(value, (int, float)) and item.min_value is not None:
            if value < item.min_value:
                errors.append(f"配置项 {key} 的值 {value} 小于最小值 {item.min_value}")
        
        if isinstance(value, (int, float)) and item.max_value is not None:
            if value > item.max_value:
                errors.append(f"配置项 {key} 的值 {value} 大于最大值 {item.max_value}")
        
        # 检查允许值
        if item.allowed_values is not None and value not in item.allowed_values:
            errors.append(f"配置项 {key} 的值 {value} 不在允许值列表中: {item.allowed_values}")
        
        # 特殊验证
        if key == "llm.api_key" and value and len(value) < 10:
            warnings.append(f"LLM API密钥长度可能过短: {key}")
        
        if key == "performance.max_cache_memory_mb" and value > 1000:
            warnings.append(f"缓存内存设置较大，可能影响系统性能: {key}")
        
        return {"errors": errors, "warnings": warnings, "suggestions": suggestions}
    
    def _generate_optimization_suggestions(self, config: Dict[str, Any]) -> List[str]:
        """生成优化建议"""
        suggestions = []
        
        # 性能优化建议
        if config.get("performance", {}).get("enable_caching", True):
            cache_size = config.get("performance", {}).get("max_cache_size", 2000)
            if cache_size < 1000:
                suggestions.append("考虑增加缓存大小以提高性能")
        
        # 数据库优化建议
        db_config = config.get("database", {})
        if db_config.get("connection_pool_size", 10) < 5:
            suggestions.append("考虑增加数据库连接池大小")
        
        if not db_config.get("enable_wal_mode", True):
            suggestions.append("建议启用WAL模式以提高数据库性能")
        
        # 安全建议
        security_config = config.get("security", {})
        if not security_config.get("enable_input_validation", True):
            suggestions.append("建议启用输入验证以提高安全性")
        
        if not security_config.get("enable_rate_limiting", True):
            suggestions.append("建议启用速率限制以防止滥用")
        
        return suggestions
    
    def _optimize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """优化配置"""
        optimized = config.copy()
        
        # 应用默认值
        for key, item in self.config_schema.items():
            if not self._has_nested_key(optimized, key) and item.default_value is not None:
                self._set_nested_value(optimized, key, item.default_value)
        
        # 性能优化
        if optimized.get("performance", {}).get("max_cache_size", 2000) < 1000:
            self._set_nested_value(optimized, "performance.max_cache_size", 1000)
        
        # 数据库优化
        if optimized.get("database", {}).get("connection_pool_size", 10) < 5:
            self._set_nested_value(optimized, "database.connection_pool_size", 5)
        
        return optimized
    
    def _set_nested_value(self, config: Dict[str, Any], key: str, value: Any):
        """设置嵌套值"""
        keys = key.split('.')
        current = config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def check_environment_variables(self) -> Dict[str, Any]:
        """检查环境变量"""
        env_status = {}
        
        for key, item in self.config_schema.items():
            if item.env_var:
                env_value = os.getenv(item.env_var)
                env_status[item.env_var] = {
                    "exists": env_value is not None,
                    "value": env_value if env_value else None,
                    "config_key": key,
                    "description": item.description
                }
        
        return env_status
    
    def generate_config_documentation(self) -> str:
        """生成配置文档"""
        doc_lines = ["# GTPlanner 配置文档", ""]
        
        # 按类别组织配置项
        categories = {
            "基础配置": ["debug"],
            "日志配置": [k for k in self.config_schema.keys() if k.startswith("logging.")],
            "LLM配置": [k for k in self.config_schema.keys() if k.startswith("llm.")],
            "Jina配置": [k for k in self.config_schema.keys() if k.startswith("jina.")],
            "多语言配置": [k for k in self.config_schema.keys() if k.startswith("multilingual.")],
            "性能配置": [k for k in self.config_schema.keys() if k.startswith("performance.")],
            "数据库配置": [k for k in self.config_schema.keys() if k.startswith("database.")],
            "错误处理配置": [k for k in self.config_schema.keys() if k.startswith("error_handling.")],
            "安全配置": [k for k in self.config_schema.keys() if k.startswith("security.")]
        }
        
        for category, keys in categories.items():
            if keys:
                doc_lines.append(f"## {category}")
                doc_lines.append("")
                
                for key in keys:
                    item = self.config_schema[key]
                    doc_lines.append(f"### {key}")
                    doc_lines.append(f"- **描述**: {item.description}")
                    doc_lines.append(f"- **类型**: {item.data_type.__name__}")
                    doc_lines.append(f"- **必需**: {'是' if item.required else '否'}")
                    
                    if item.default_value is not None:
                        doc_lines.append(f"- **默认值**: {item.default_value}")
                    
                    if item.min_value is not None or item.max_value is not None:
                        range_str = []
                        if item.min_value is not None:
                            range_str.append(f"最小值: {item.min_value}")
                        if item.max_value is not None:
                            range_str.append(f"最大值: {item.max_value}")
                        doc_lines.append(f"- **范围**: {', '.join(range_str)}")
                    
                    if item.allowed_values is not None:
                        doc_lines.append(f"- **允许值**: {item.allowed_values}")
                    
                    if item.env_var:
                        doc_lines.append(f"- **环境变量**: {item.env_var}")
                    
                    doc_lines.append("")
        
        return "\n".join(doc_lines)


# 全局验证器实例
_global_validator: Optional[ConfigValidator] = None


def get_global_validator() -> ConfigValidator:
    """获取全局验证器实例"""
    global _global_validator
    if _global_validator is None:
        _global_validator = ConfigValidator()
    return _global_validator


def validate_settings_file(file_path: str = "settings.toml") -> ConfigValidationResult:
    """验证设置文件"""
    validator = get_global_validator()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config = toml.load(f)
        
        return validator.validate_config(config)
    except Exception as e:
        return ConfigValidationResult(
            is_valid=False,
            errors=[f"无法读取配置文件: {e}"],
            warnings=[],
            suggestions=[]
        )


def check_environment_setup() -> Dict[str, Any]:
    """检查环境设置"""
    validator = get_global_validator()
    return validator.check_environment_variables()


def generate_config_docs() -> str:
    """生成配置文档"""
    validator = get_global_validator()
    return validator.generate_config_documentation()
