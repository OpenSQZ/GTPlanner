"""
GTPlanner 多语言设置的配置管理器。

此模块提供了多语言功能的集中配置管理，集成了 dynaconf 设置。
"""

import os
from typing import List, Optional, Dict, Any
import logging

try:
    from dynaconf import Dynaconf
except ImportError:
    Dynaconf = None

from gtplanner.utils.language_detection import get_supported_languages, is_supported_language

logger = logging.getLogger(__name__)


class MultilingualConfig:
    """多语言设置和 API 密钥的配置管理器。"""

    def __init__(self, settings_file: str = "settings.toml"):
        """初始化配置管理器。

        参数:
            settings_file: 设置文件路径
        """
        self.settings_file = settings_file
        self._settings = None
        self._load_settings()
    
    def _load_settings(self):
        """从 dynaconf 或环境变量加载设置。"""
        if Dynaconf:
            try:
                self._settings = Dynaconf(
                    settings_files=[self.settings_file],
                    environments=True,
                    load_dotenv=True,
                    envvar_prefix="GTPLANNER"
                )
                logger.info(f"Loaded settings from {self.settings_file}")
            except Exception as e:
                logger.warning(f"Failed to load dynaconf settings: {e}")
                self._settings = None
        else:
            logger.warning("Dynaconf not available, using environment variables only")
            self._settings = None
    
    def get_default_language(self) -> str:
        """获取默认语言设置。
        
        返回:
            默认语言代码
        """
        # Try dynaconf settings first
        if self._settings:
            try:
                default_lang = self._settings.get("multilingual.default_language", "en")
                if is_supported_language(default_lang):
                    return default_lang.lower()
            except Exception as e:
                logger.warning(f"Error reading default language from settings: {e}")
        
        # Try environment variable
        env_lang = os.getenv("GTPLANNER_DEFAULT_LANGUAGE", "en").lower()
        if is_supported_language(env_lang):
            return env_lang
        
        # Final fallback
        return "en"
    
    def is_auto_detect_enabled(self) -> bool:
        """检查是否启用自动语言检测。
        
        返回:
            如果启用自动检测则为 True，否则为 False
        """
        # Try dynaconf settings first
        if self._settings:
            try:
                return self._settings.get("multilingual.auto_detect", True)
            except Exception as e:
                logger.warning(f"Error reading auto_detect setting: {e}")
        
        # Try environment variable
        env_auto_detect = os.getenv("GTPLANNER_AUTO_DETECT", "true").lower()
        return env_auto_detect in ("true", "1", "yes", "on")
    
    def is_fallback_enabled(self) -> bool:
        """检查是否启用默认语言回退。
        
        返回:
            如果启用回退则为 True，否则为 False
        """
        # Try dynaconf settings first
        if self._settings:
            try:
                return self._settings.get("multilingual.fallback_enabled", True)
            except Exception as e:
                logger.warning(f"Error reading fallback_enabled setting: {e}")
        
        # Try environment variable
        env_fallback = os.getenv("GTPLANNER_FALLBACK_ENABLED", "true").lower()
        return env_fallback in ("true", "1", "yes", "on")
    
    def get_supported_languages_config(self) -> List[str]:
        """从配置中获取支持的语言列表。
        
        返回:
            支持的语言代码列表
        """
        # Try dynaconf settings first
        if self._settings:
            try:
                config_langs = self._settings.get("multilingual.supported_languages", [])
                if config_langs and isinstance(config_langs, list):
                    # Filter to only include actually supported languages
                    valid_langs = [lang.lower() for lang in config_langs if is_supported_language(lang)]
                    if valid_langs:
                        return valid_langs
            except Exception as e:
                logger.warning(f"Error reading supported languages from settings: {e}")
        
        # Try environment variable
        env_langs = os.getenv("GTPLANNER_SUPPORTED_LANGUAGES", "")
        if env_langs:
            try:
                # Parse comma-separated list
                lang_list = [lang.strip().lower() for lang in env_langs.split(",")]
                valid_langs = [lang for lang in lang_list if is_supported_language(lang)]
                if valid_langs:
                    return valid_langs
            except Exception as e:
                logger.warning(f"Error parsing supported languages from environment: {e}")
        
        # Final fallback to all supported languages
        return get_supported_languages()
    
    def get_language_preference(self, user_id: Optional[str] = None) -> Optional[str]:
        """获取用户的语言偏好。
        
        参数:
            user_id: 用户特定偏好的可选用户标识符
            
        返回:
            用户的首选语言代码，如果未设置则为 None
        """
        # For now, we'll use environment variables for user preferences
        # In a real application, this might come from a database or user profile
        
        if user_id:
            # Try user-specific environment variable
            env_key = f"GTPLANNER_USER_{user_id.upper()}_LANGUAGE"
            user_lang = os.getenv(env_key)
            if user_lang and is_supported_language(user_lang):
                return user_lang.lower()
        
        # Try general user preference
        user_lang = os.getenv("GTPLANNER_USER_LANGUAGE")
        if user_lang and is_supported_language(user_lang):
            return user_lang.lower()
        
        return None

    def get_jina_api_key(self) -> Optional[str]:
        """从配置中获取 Jina API 密钥。

        返回:
            Jina API 密钥，如果未设置则为 None
        """
        # Try dynaconf settings first
        if self._settings:
            try:
                api_key = self._settings.get("jina.api_key")
                if api_key:
                    return api_key
            except Exception as e:
                logger.warning(f"Error reading Jina API key from settings: {e}")

        # Try environment variable
        api_key = os.getenv("JINA_API_KEY")
        if api_key:
            return api_key

        # Try GTPLANNER prefixed environment variable
        api_key = os.getenv("GTPLANNER_JINA_API_KEY")
        if api_key:
            return api_key

        return None

    def get_llm_config(self) -> Dict[str, Any]:
        """获取 LLM 配置。

        返回:
            包含 LLM 配置的字典
        """
        config = {}

        # Try dynaconf settings first
        if self._settings:
            try:
                config.update({
                    "api_key": self._settings.get("llm.api_key"),
                    "base_url": self._settings.get("llm.base_url"),
                    "model": self._settings.get("llm.model")
                })
            except Exception as e:
                logger.warning(f"Error reading LLM config from settings: {e}")

        # Try environment variables
        config.update({
            "api_key": config.get("api_key") or os.getenv("LLM_API_KEY"),
            "base_url": config.get("base_url") or os.getenv("LLM_BASE_URL"),
            "model": config.get("model") or os.getenv("LLM_MODEL")
        })

        return {k: v for k, v in config.items() if v is not None}

    def get_vector_service_config(self) -> Dict[str, Any]:
        """获取向量服务配置。

        返回:
            包含向量服务配置的字典
        """
        config = {}

        # Try dynaconf settings first
        if self._settings:
            try:
                config.update({
                    "base_url": self._settings.get("vector_service.base_url"),
                    "timeout": self._settings.get("vector_service.timeout", 30),
                    "prefabs_index_name": self._settings.get("vector_service.prefabs_index_name", "document_gtplanner_prefabs"),
                    "vector_field": self._settings.get("vector_service.vector_field", "combined_text")
                })
            except Exception as e:
                logger.warning(f"Error reading vector service config from settings: {e}")

        # Environment variables have higher priority than settings.toml
        config.update({
            "base_url": os.getenv("VECTOR_SERVICE_BASE_URL") or os.getenv("GTPLANNER_VECTOR_SERVICE_BASE_URL") or config.get("base_url"),
            "timeout": int(os.getenv("VECTOR_SERVICE_TIMEOUT") or config.get("timeout", 30)),
            "prefabs_index_name": os.getenv("VECTOR_SERVICE_INDEX_NAME") or config.get("prefabs_index_name", "document_gtplanner_prefabs"),
            "vector_field": os.getenv("VECTOR_SERVICE_VECTOR_FIELD") or config.get("vector_field", "combined_text")
        })

        return {k: v for k, v in config.items() if v is not None}

    def get_all_config(self) -> Dict[str, Any]:
        """获取所有配置作为字典。

        返回:
            包含所有配置值的字典
        """
        return {
            "default_language": self.get_default_language(),
            "auto_detect_enabled": self.is_auto_detect_enabled(),
            "fallback_enabled": self.is_fallback_enabled(),
            "supported_languages": self.get_supported_languages_config(),
            "all_available_languages": get_supported_languages(),
            "jina_api_key": self.get_jina_api_key(),
            "llm_config": self.get_llm_config(),
            "vector_service_config": self.get_vector_service_config()
        }
    
    def validate_config(self) -> List[str]:
        """验证当前配置。
        
        返回:
            验证警告/错误列表
        """
        warnings = []
        
        # Check default language
        default_lang = self.get_default_language()
        if not is_supported_language(default_lang):
            warnings.append(f"Default language '{default_lang}' is not supported")
        
        # Check supported languages list
        supported_langs = self.get_supported_languages_config()
        if not supported_langs:
            warnings.append("No supported languages configured")
        elif default_lang not in supported_langs:
            warnings.append(f"Default language '{default_lang}' is not in supported languages list")
        
        # Check if dynaconf is available but settings file doesn't exist
        if Dynaconf and not os.path.exists(self.settings_file):
            warnings.append(f"Settings file '{self.settings_file}' not found")
        
        return warnings


# 全局配置管理器实例
multilingual_config = MultilingualConfig()


def get_default_language() -> str:
    """获取默认语言的便捷函数。
    
    返回:
        默认语言代码
    """
    return multilingual_config.get_default_language()


def is_auto_detect_enabled() -> bool:
    """检查是否启用自动检测的便捷函数。
    
    返回:
        如果启用自动检测则为 True
    """
    return multilingual_config.is_auto_detect_enabled()


def is_fallback_enabled() -> bool:
    """检查是否启用回退的便捷函数。
    
    返回:
        如果启用回退则为 True
    """
    return multilingual_config.is_fallback_enabled()


def get_supported_languages_config() -> List[str]:
    """从配置获取支持语言的便捷函数。
    
    返回:
        支持的语言代码列表
    """
    return multilingual_config.get_supported_languages_config()


def get_language_preference(user_id: Optional[str] = None) -> Optional[str]:
    """获取用户语言偏好的便捷函数。

    参数:
        user_id: 可选的用户标识符

    返回:
        用户的首选语言代码，如果未设置则为 None
    """
    return multilingual_config.get_language_preference(user_id)


def get_jina_api_key() -> Optional[str]:
    """获取 Jina API 密钥的便捷函数。

    返回:
        Jina API 密钥，如果未设置则为 None
    """
    return multilingual_config.get_jina_api_key()


def get_llm_config() -> Dict[str, Any]:
    """获取 LLM 配置的便捷函数。

    返回:
        包含 LLM 配置的字典
    """
    return multilingual_config.get_llm_config()


def get_vector_service_config() -> Dict[str, Any]:
    """获取向量服务配置的便捷函数。

    返回:
        包含向量服务配置的字典
    """
    return multilingual_config.get_vector_service_config()


def get_all_config() -> Dict[str, Any]:
    """获取所有配置的便捷函数。

    返回:
        包含所有配置值的字典
    """
    return multilingual_config.get_all_config()
