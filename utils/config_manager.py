"""
Configuration manager for GTPlanner multilingual settings.

This module provides centralized configuration management for multilingual
functionality, integrating with dynaconf settings.
"""

import os
from typing import List, Optional, Dict, Any
import logging

try:
    from dynaconf import Dynaconf
except ImportError:
    Dynaconf = None

from utils.language_detection import get_supported_languages, is_supported_language

logger = logging.getLogger(__name__)


class MultilingualConfig:
    """Configuration manager for multilingual settings."""
    
    def __init__(self, settings_file: str = "settings.toml"):
        """Initialize the configuration manager.
        
        Args:
            settings_file: Path to the settings file
        """
        self.settings_file = settings_file
        self._settings = None
        self._load_settings()
    
    def _load_settings(self):
        """Load settings from dynaconf or environment variables."""
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
        """Get the default language setting.
        
        Returns:
            The default language code
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
        """Check if automatic language detection is enabled.
        
        Returns:
            True if auto-detection is enabled, False otherwise
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
        """Check if fallback to default language is enabled.
        
        Returns:
            True if fallback is enabled, False otherwise
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
        """Get the list of supported languages from configuration.
        
        Returns:
            List of supported language codes
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
        """Get user's language preference.
        
        Args:
            user_id: Optional user identifier for user-specific preferences
            
        Returns:
            The user's preferred language code, or None if not set
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
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all multilingual configuration as a dictionary.
        
        Returns:
            Dictionary containing all configuration values
        """
        return {
            "default_language": self.get_default_language(),
            "auto_detect_enabled": self.is_auto_detect_enabled(),
            "fallback_enabled": self.is_fallback_enabled(),
            "supported_languages": self.get_supported_languages_config(),
            "all_available_languages": get_supported_languages()
        }
    
    def validate_config(self) -> List[str]:
        """Validate the current configuration.
        
        Returns:
            List of validation warnings/errors
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


# Global configuration manager instance
multilingual_config = MultilingualConfig()


def get_default_language() -> str:
    """Convenience function to get the default language.
    
    Returns:
        The default language code
    """
    return multilingual_config.get_default_language()


def is_auto_detect_enabled() -> bool:
    """Convenience function to check if auto-detection is enabled.
    
    Returns:
        True if auto-detection is enabled
    """
    return multilingual_config.is_auto_detect_enabled()


def is_fallback_enabled() -> bool:
    """Convenience function to check if fallback is enabled.
    
    Returns:
        True if fallback is enabled
    """
    return multilingual_config.is_fallback_enabled()


def get_supported_languages_config() -> List[str]:
    """Convenience function to get supported languages from config.
    
    Returns:
        List of supported language codes
    """
    return multilingual_config.get_supported_languages_config()


def get_language_preference(user_id: Optional[str] = None) -> Optional[str]:
    """Convenience function to get user's language preference.
    
    Args:
        user_id: Optional user identifier
        
    Returns:
        The user's preferred language code, or None if not set
    """
    return multilingual_config.get_language_preference(user_id)
