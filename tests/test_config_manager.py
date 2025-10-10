"""
Unit tests for configuration manager module.

This module tests configuration management functionality including:
- Configuration loading and validation
- API key validation
- URL validation
- Health status checking
- Language configuration
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from utils.config_manager import (
    MultilingualConfig,
    get_default_language,
    is_auto_detect_enabled,
    is_fallback_enabled,
    get_supported_languages_config,
    get_jina_api_key,
    get_llm_config,
    get_vector_service_config,
    multilingual_config
)


class TestMultilingualConfig:
    """Test suite for MultilingualConfig class."""

    def test_init_default(self):
        """Test initialization with default settings file."""
        config = MultilingualConfig()
        assert config.settings_file == "settings.toml"

    def test_init_custom_settings_file(self):
        """Test initialization with custom settings file."""
        config = MultilingualConfig(settings_file="custom_settings.toml")
        assert config.settings_file == "custom_settings.toml"

    def test_get_default_language_from_env(self):
        """Test getting default language from environment variable."""
        with patch.dict(os.environ, {"GTPLANNER_DEFAULT_LANGUAGE": "zh"}):
            config = MultilingualConfig()
            result = config.get_default_language()
            assert result == "zh"

    def test_get_default_language_fallback(self):
        """Test default language fallback to English."""
        with patch.dict(os.environ, {}, clear=True):
            config = MultilingualConfig()
            # When no settings and no env var, should default to 'en'
            result = config.get_default_language()
            assert result == "en"

    def test_is_auto_detect_enabled_from_env(self):
        """Test auto-detect setting from environment."""
        with patch.dict(os.environ, {"GTPLANNER_AUTO_DETECT": "false"}):
            config = MultilingualConfig()
            assert config.is_auto_detect_enabled() == False

        with patch.dict(os.environ, {"GTPLANNER_AUTO_DETECT": "true"}):
            config = MultilingualConfig()
            assert config.is_auto_detect_enabled() == True

    def test_is_fallback_enabled_from_env(self):
        """Test fallback setting from environment."""
        with patch.dict(os.environ, {"GTPLANNER_FALLBACK_ENABLED": "false"}):
            config = MultilingualConfig()
            assert config.is_fallback_enabled() == False

    def test_get_jina_api_key_from_env(self):
        """Test getting Jina API key from environment."""
        test_key = "jina_test_key_1234567890abcdef"
        with patch.dict(os.environ, {"JINA_API_KEY": test_key}):
            config = MultilingualConfig()
            result = config.get_jina_api_key()
            assert result == test_key

    def test_get_jina_api_key_none(self):
        """Test getting Jina API key when not set."""
        with patch.dict(os.environ, {}, clear=True):
            config = MultilingualConfig()
            result = config.get_jina_api_key()
            assert result is None

    def test_get_llm_config_from_env(self):
        """Test getting LLM config from environment."""
        test_env = {
            "LLM_API_KEY": "test_api_key_12345678901234567890",
            "LLM_BASE_URL": "https://api.example.com/v1",
            "LLM_MODEL": "gpt-4"
        }
        with patch.dict(os.environ, test_env):
            config = MultilingualConfig()
            llm_config = config.get_llm_config()
            assert llm_config["api_key"] == test_env["LLM_API_KEY"]
            assert llm_config["base_url"] == test_env["LLM_BASE_URL"]
            assert llm_config["model"] == test_env["LLM_MODEL"]

    def test_get_vector_service_config_from_env(self):
        """Test getting vector service config from environment."""
        test_url = "https://vector.example.com"
        with patch.dict(os.environ, {"VECTOR_SERVICE_BASE_URL": test_url}):
            config = MultilingualConfig()
            vector_config = config.get_vector_service_config()
            assert vector_config["base_url"] == test_url


class TestConfigValidation:
    """Test suite for configuration validation."""

    def test_validate_config_basic(self):
        """Test basic configuration validation."""
        config = MultilingualConfig()
        warnings = config.validate_config()
        assert isinstance(warnings, list)

    def test_validate_llm_config_missing_api_key(self):
        """Test LLM validation with missing API key."""
        with patch.dict(os.environ, {}, clear=True):
            config = MultilingualConfig()
            warnings = config._validate_llm_config()
            assert any("API key" in w for w in warnings)

    def test_validate_llm_config_invalid_url(self):
        """Test LLM validation with invalid URL."""
        test_env = {
            "LLM_API_KEY": "test_key_12345678901234567890",
            "LLM_BASE_URL": "not-a-valid-url",
            "LLM_MODEL": "gpt-4"
        }
        with patch.dict(os.environ, test_env):
            config = MultilingualConfig()
            warnings = config._validate_llm_config()
            assert any("URL" in w and "invalid" in w for w in warnings)

    def test_validate_api_keys_placeholder(self):
        """Test API key validation with placeholder values."""
        with patch.dict(os.environ, {"JINA_API_KEY": "@format_placeholder"}):
            config = MultilingualConfig()
            warnings = config._validate_api_keys()
            assert any("placeholder" in w for w in warnings)

    def test_is_valid_api_key(self):
        """Test API key format validation."""
        # Valid keys
        assert MultilingualConfig._is_valid_api_key("sk-1234567890abcdefghij1234567890") == True
        assert MultilingualConfig._is_valid_api_key("jina_api_key_12345678901234567890") == True
        
        # Invalid keys
        assert MultilingualConfig._is_valid_api_key("") == False
        assert MultilingualConfig._is_valid_api_key("   ") == False
        assert MultilingualConfig._is_valid_api_key("your-api-key") == False
        assert MultilingualConfig._is_valid_api_key("@format_placeholder") == False
        assert MultilingualConfig._is_valid_api_key("sk-xxx") == False
        assert MultilingualConfig._is_valid_api_key("short") == False
        assert MultilingualConfig._is_valid_api_key("<your-key-here>") == False

    def test_is_valid_url(self):
        """Test URL validation."""
        # Valid URLs
        assert MultilingualConfig._is_valid_url("https://api.openai.com/v1") == True
        assert MultilingualConfig._is_valid_url("http://localhost:8000") == True
        assert MultilingualConfig._is_valid_url("https://example.com:443/path") == True
        
        # Invalid URLs
        assert MultilingualConfig._is_valid_url("") == False
        assert MultilingualConfig._is_valid_url("   ") == False
        assert MultilingualConfig._is_valid_url("not-a-url") == False
        assert MultilingualConfig._is_valid_url("//no-scheme.com") == False


class TestHealthStatus:
    """Test suite for health status checking."""

    def test_get_health_status_structure(self):
        """Test health status response structure."""
        config = MultilingualConfig()
        status = config.get_health_status()
        
        assert "healthy" in status
        assert "warnings" in status
        assert "errors" in status
        assert "components" in status
        assert isinstance(status["warnings"], list)
        assert isinstance(status["errors"], list)
        assert isinstance(status["components"], dict)

    def test_get_health_status_multilingual_component(self):
        """Test multilingual component in health status."""
        config = MultilingualConfig()
        status = config.get_health_status()
        
        assert "multilingual" in status["components"]
        ml_component = status["components"]["multilingual"]
        assert "status" in ml_component
        assert "default_language" in ml_component
        assert "auto_detect" in ml_component
        assert "supported_languages" in ml_component

    def test_get_health_status_llm_component(self):
        """Test LLM component in health status."""
        config = MultilingualConfig()
        status = config.get_health_status()
        
        assert "llm" in status["components"]
        llm_component = status["components"]["llm"]
        assert "status" in llm_component
        assert "configured" in llm_component
        assert "has_api_key" in llm_component
        assert "has_base_url" in llm_component
        assert "has_model" in llm_component

    def test_get_health_status_with_valid_llm_config(self):
        """Test health status with valid LLM configuration."""
        test_env = {
            "LLM_API_KEY": "test_key_12345678901234567890",
            "LLM_BASE_URL": "https://api.example.com/v1",
            "LLM_MODEL": "gpt-4"
        }
        with patch.dict(os.environ, test_env):
            config = MultilingualConfig()
            status = config.get_health_status()
            
            llm_component = status["components"]["llm"]
            assert llm_component["has_api_key"] == True
            assert llm_component["has_base_url"] == True
            assert llm_component["has_model"] == True

    def test_get_health_status_jina_component(self):
        """Test Jina component in health status."""
        config = MultilingualConfig()
        status = config.get_health_status()
        
        assert "jina" in status["components"]
        jina_component = status["components"]["jina"]
        assert "status" in jina_component
        assert "configured" in jina_component

    def test_get_health_status_vector_service_component(self):
        """Test vector service component in health status."""
        config = MultilingualConfig()
        status = config.get_health_status()
        
        assert "vector_service" in status["components"]
        vector_component = status["components"]["vector_service"]
        assert "status" in vector_component
        assert "configured" in vector_component


class TestGlobalFunctions:
    """Test suite for global convenience functions."""

    def test_get_default_language_function(self):
        """Test global get_default_language function."""
        result = get_default_language()
        assert isinstance(result, str)
        assert len(result) == 2  # Should be a language code like 'en'

    def test_is_auto_detect_enabled_function(self):
        """Test global is_auto_detect_enabled function."""
        result = is_auto_detect_enabled()
        assert isinstance(result, bool)

    def test_is_fallback_enabled_function(self):
        """Test global is_fallback_enabled function."""
        result = is_fallback_enabled()
        assert isinstance(result, bool)

    def test_get_supported_languages_config_function(self):
        """Test global get_supported_languages_config function."""
        result = get_supported_languages_config()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_get_jina_api_key_function(self):
        """Test global get_jina_api_key function."""
        result = get_jina_api_key()
        # Result can be None or a string
        assert result is None or isinstance(result, str)

    def test_get_llm_config_function(self):
        """Test global get_llm_config function."""
        result = get_llm_config()
        assert isinstance(result, dict)

    def test_get_vector_service_config_function(self):
        """Test global get_vector_service_config function."""
        result = get_vector_service_config()
        assert isinstance(result, dict)


class TestGlobalConfigInstance:
    """Test suite for global multilingual_config instance."""

    def test_global_instance_exists(self):
        """Test that global config instance exists."""
        assert multilingual_config is not None
        assert isinstance(multilingual_config, MultilingualConfig)

    def test_global_instance_methods(self):
        """Test global instance methods."""
        # Should not raise exceptions
        result = multilingual_config.get_default_language()
        assert isinstance(result, str)
        
        result = multilingual_config.is_auto_detect_enabled()
        assert isinstance(result, bool)


class TestEdgeCases:
    """Test suite for edge cases."""

    def test_invalid_language_code_in_env(self):
        """Test handling of invalid language code in environment."""
        with patch.dict(os.environ, {"GTPLANNER_DEFAULT_LANGUAGE": "invalid_lang"}):
            config = MultilingualConfig()
            result = config.get_default_language()
            # Should fall back to English
            assert result == "en"

    def test_supported_languages_from_env_comma_separated(self):
        """Test parsing comma-separated supported languages from env."""
        with patch.dict(os.environ, {"GTPLANNER_SUPPORTED_LANGUAGES": "en,zh,ja"}):
            config = MultilingualConfig()
            result = config.get_supported_languages_config()
            assert "en" in result
            assert "zh" in result
            assert "ja" in result

    def test_auto_detect_various_values(self):
        """Test auto-detect with various environment values."""
        test_cases = [
            ("true", True),
            ("1", True),
            ("yes", True),
            ("on", True),
            ("false", False),
            ("0", False),
            ("no", False),
            ("off", False),
        ]
        
        for env_value, expected in test_cases:
            with patch.dict(os.environ, {"GTPLANNER_AUTO_DETECT": env_value}):
                config = MultilingualConfig()
                assert config.is_auto_detect_enabled() == expected

    def test_get_all_config(self):
        """Test getting all configuration as dictionary."""
        config = MultilingualConfig()
        all_config = config.get_all_config()
        
        assert isinstance(all_config, dict)
        assert "default_language" in all_config
        assert "auto_detect_enabled" in all_config
        assert "fallback_enabled" in all_config
        assert "supported_languages" in all_config
        assert "jina_api_key" in all_config
        assert "llm_config" in all_config
        assert "vector_service_config" in all_config

    def test_validate_config_with_missing_settings_file(self):
        """Test validation when settings file is missing."""
        config = MultilingualConfig(settings_file="nonexistent_file.toml")
        warnings = config.validate_config()
        # Should handle gracefully and return warnings list
        assert isinstance(warnings, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
