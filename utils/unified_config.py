"""
统一配置管理器

合并所有配置加载逻辑，提供统一的配置访问接口，支持缓存和热重载。
"""

import os
import time
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
from pathlib import Path

from utils.logger_config import get_logger

# 尝试导入 Dynaconf
try:
    from dynaconf import Dynaconf
    DYNACONF_AVAILABLE = True
except ImportError:
    DYNACONF_AVAILABLE = False
    Dynaconf = None


@dataclass
class ConfigCache:
    """配置缓存"""
    data: Any
    timestamp: float
    ttl: float = 300.0  # 5分钟缓存
    
    def is_expired(self) -> bool:
        """检查缓存是否过期"""
        return time.time() - self.timestamp > self.ttl


class UnifiedConfigManager:
    """
    统一配置管理器
    
    合并了原来分散在各个模块中的配置加载逻辑，提供统一的配置访问接口。
    """
    
    def __init__(self, settings_files: Optional[list] = None):
        """
        初始化配置管理器
        
        Args:
            settings_files: 配置文件列表
        """
        self.logger = get_logger("unified_config")
        self.settings_files = settings_files or [
            "settings.toml",
            "settings.local.toml", 
            ".secrets.toml"
        ]
        
        # 配置缓存
        self._cache: Dict[str, ConfigCache] = {}
        self._settings: Optional[Dynaconf] = None
        self._load_settings()
    
    def _load_settings(self) -> None:
        """加载配置文件"""
        if not DYNACONF_AVAILABLE:
            self.logger.warning("Dynaconf不可用，将使用环境变量")
            self._settings = None
            return
        
        try:
            self._settings = Dynaconf(
                settings_files=self.settings_files,
                environments=True,
                env_switcher="ENV_FOR_DYNACONF",
                load_dotenv=True,
                envvar_prefix="GTPLANNER"
            )
            self.logger.info(f"成功加载配置文件: {self.settings_files}")
        except Exception as e:
            self.logger.warning(f"加载Dynaconf配置失败: {e}，将使用环境变量")
            self._settings = None
    
    def get_setting(
        self,
        key: str,
        default: Any = None,
        use_cache: bool = True,
        cache_ttl: float = 300.0
    ) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            use_cache: 是否使用缓存
            cache_ttl: 缓存生存时间（秒）
            
        Returns:
            配置值
        """
        # 检查缓存
        if use_cache and key in self._cache:
            cache_entry = self._cache[key]
            if not cache_entry.is_expired():
                return cache_entry.data
        
        # 获取配置值
        value = self._get_setting_impl(key, default)
        
        # 更新缓存
        if use_cache:
            self._cache[key] = ConfigCache(
                data=value,
                timestamp=time.time(),
                ttl=cache_ttl
            )
        
        return value
    
    def _get_setting_impl(self, key: str, default: Any = None) -> Any:
        """实际的配置获取实现"""
        # 首先尝试从环境变量获取
        env_key = f"GTPLANNER_{key.upper()}"
        env_value = os.getenv(env_key)
        if env_value is not None:
            return self._convert_env_value(env_value)
        
        # 然后尝试从Dynaconf获取
        if self._settings is not None:
            try:
                return self._settings.get(key, default)
            except Exception as e:
                self.logger.warning(f"从Dynaconf获取配置 {key} 失败: {e}")
        
        # 最后返回默认值
        return default
    
    def _convert_env_value(self, value: str) -> Union[str, int, float, bool]:
        """转换环境变量值到合适的类型"""
        # 布尔值
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # 整数
        try:
            return int(value)
        except ValueError:
            pass
        
        # 浮点数
        try:
            return float(value)
        except ValueError:
            pass
        
        # 字符串
        return value
    
    def get_openai_config(self) -> Dict[str, Any]:
        """
        获取OpenAI配置
        
        Returns:
            OpenAI配置字典
        """
        return {
            "api_key": self.get_setting("openai_api_key") or os.getenv("OPENAI_API_KEY"),
            "base_url": self.get_setting("openai_base_url") or os.getenv("OPENAI_BASE_URL"),
            "model": self.get_setting("openai_model", "gpt-4"),
            "temperature": self.get_setting("openai_temperature", 0.0),
            "max_tokens": self.get_setting("openai_max_tokens"),
            "timeout": self.get_setting("openai_timeout", 120.0),
            "max_retries": self.get_setting("openai_max_retries", 3),
            "retry_delay": self.get_setting("openai_retry_delay", 2.0),
            "log_requests": self.get_setting("openai_log_requests", True),
            "log_responses": self.get_setting("openai_log_responses", True),
            "function_calling_enabled": self.get_setting("openai_function_calling_enabled", True),
            "tool_choice": self.get_setting("openai_tool_choice", "auto")
        }
    
    def get_multilingual_config(self) -> Dict[str, Any]:
        """
        获取多语言配置
        
        Returns:
            多语言配置字典
        """
        return {
            "default_language": self.get_setting("default_language", "zh"),
            "supported_languages": self.get_setting("supported_languages", ["zh", "en", "ja", "es", "fr"]),
            "auto_detect": self.get_setting("auto_detect_language", True),
            "fallback_language": self.get_setting("fallback_language", "en")
        }
    
    def get_jina_config(self) -> Dict[str, Any]:
        """
        获取Jina API配置
        
        Returns:
            Jina配置字典
        """
        return {
            "api_key": self.get_setting("jina_api_key") or os.getenv("JINA_API_KEY"),
            "base_url": self.get_setting("jina_base_url", "https://r.jina.ai/"),
            "timeout": self.get_setting("jina_timeout", 30.0),
            "max_retries": self.get_setting("jina_max_retries", 3)
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        获取日志配置
        
        Returns:
            日志配置字典
        """
        return {
            "level": self.get_setting("log_level", "INFO"),
            "format": self.get_setting("log_format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            "file_path": self.get_setting("log_file_path", "logs/gtplanner.log"),
            "max_file_size": self.get_setting("log_max_file_size", 10 * 1024 * 1024),  # 10MB
            "backup_count": self.get_setting("log_backup_count", 5),
            "enable_console": self.get_setting("log_enable_console", True),
            "enable_file": self.get_setting("log_enable_file", True)
        }
    
    def get_performance_config(self) -> Dict[str, Any]:
        """
        获取性能配置
        
        Returns:
            性能配置字典
        """
        return {
            "max_concurrent_requests": self.get_setting("max_concurrent_requests", 10),
            "request_timeout": self.get_setting("request_timeout", 300.0),
            "connection_pool_size": self.get_setting("connection_pool_size", 20),
            "enable_caching": self.get_setting("enable_caching", True),
            "cache_ttl": self.get_setting("cache_ttl", 300.0),
            "enable_compression": self.get_setting("enable_compression", True),
            "compression_threshold": self.get_setting("compression_threshold", 8000)
        }
    
    def get_streaming_config(self) -> Dict[str, Any]:
        """
        获取流式响应配置
        
        Returns:
            流式响应配置字典
        """
        return {
            "enable_streaming": self.get_setting("enable_streaming", True),
            "chunk_size": self.get_setting("streaming_chunk_size", 1024),
            "heartbeat_interval": self.get_setting("streaming_heartbeat_interval", 30.0),
            "max_connection_time": self.get_setting("streaming_max_connection_time", 3600.0),
            "buffer_size": self.get_setting("streaming_buffer_size", 8192)
        }
    
    def reload_config(self) -> None:
        """重新加载配置"""
        self._cache.clear()
        self._load_settings()
        self.logger.info("配置已重新加载")
    
    def clear_cache(self) -> None:
        """清空配置缓存"""
        self._cache.clear()
        self.logger.info("配置缓存已清空")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        total_entries = len(self._cache)
        expired_entries = sum(1 for cache in self._cache.values() if cache.is_expired())
        
        return {
            "total_entries": total_entries,
            "expired_entries": expired_entries,
            "active_entries": total_entries - expired_entries,
            "cache_keys": list(self._cache.keys())
        }


# 全局配置管理器实例
_global_config_manager: Optional[UnifiedConfigManager] = None


def get_config_manager() -> UnifiedConfigManager:
    """获取全局配置管理器实例"""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = UnifiedConfigManager()
    return _global_config_manager


def get_config(key: str, default: Any = None) -> Any:
    """
    便捷的配置获取函数
    
    Args:
        key: 配置键
        default: 默认值
        
    Returns:
        配置值
    """
    return get_config_manager().get_setting(key, default)


def reload_config() -> None:
    """重新加载全局配置"""
    get_config_manager().reload_config()


def clear_config_cache() -> None:
    """清空全局配置缓存"""
    get_config_manager().clear_cache()
