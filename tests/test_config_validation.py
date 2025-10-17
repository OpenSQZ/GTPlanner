"""
Tests for GTPlanner configuration validation and type safety enhancements.
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config_validator import ConfigValidator, ConfigValidationResult, validate_and_get_config
from utils.type_safety import TypeValidator, validate_config, create_validated_dataclass
from utils.config_enhancer import ConfigEnhancer


class TestConfigValidator:
    """Test configuration validation functionality."""

    def test_valid_configuration(self):
        """Test validation of valid configuration."""
        valid_config = {
            "llm": {
                "api_key": "sk-test123456789",
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-4"
            },
            "multilingual": {
                "default_language": "en",
                "auto_detect": True,
                "fallback_enabled": True,
                "supported_languages": ["en", "zh"]
            }
        }

        validator = ConfigValidator()
        result = validator.validate_configuration(valid_config)

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert "llm" in result.validated_config
        assert "multilingual" in result.validated_config

    def test_missing_required_fields(self):
        """Test validation with missing required fields."""
        invalid_config = {
            "llm": {
                # Missing api_key and base_url
                "model": "gpt-4"
            }
        }

        validator = ConfigValidator()
        result = validator.validate_configuration(invalid_config)

        assert result.is_valid is False
        assert len(result.errors) >= 2  # Should have errors for missing api_key and base_url

    def test_invalid_types(self):
        """Test validation with invalid field types."""
        invalid_config = {
            "llm": {
                "api_key": "sk-test123456789",
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-4"
            },
            "multilingual": {
                "default_language": "en",
                "auto_detect": "not-a-boolean",  # Should be bool
                "fallback_enabled": True,
                "supported_languages": "not-a-list"  # Should be list
            }
        }

        validator = ConfigValidator()
        result = validator.validate_configuration(invalid_config)

        assert result.is_valid is False
        # Should have errors for invalid types
        assert any("should be type" in error["message"] for error in result.errors)

    def test_url_validation(self):
        """Test URL validation functionality."""
        validator = ConfigValidator()

        # Valid URLs
        assert validator._validate_url("https://api.openai.com/v1", "base_url", "llm") is None
        assert validator._validate_url("http://localhost:8080", "base_url", "llm") is None

        # Invalid URLs
        result = validator._validate_url("not-a-url", "base_url", "llm")
        assert result is not None
        assert "URL format" in result["message"]

    def test_api_key_validation(self):
        """Test API key validation functionality."""
        validator = ConfigValidator()

        # Valid API keys
        assert validator._validate_api_key("sk-test12345678901234567890", "api_key", "llm") is None

        # API keys that generate warnings
        result = validator._validate_api_key("sk-test", "api_key", "llm")
        assert result is not None
        assert "too short" in result["message"]

        # Invalid API keys
        result = validator._validate_api_key("", "api_key", "llm")
        assert result is not None
        assert "non-empty string" in result["message"]


class TestTypeSafety:
    """Test type safety functionality."""

    def test_validate_type_basic(self):
        """Test basic type validation."""
        # Valid cases
        TypeValidator.validate_type("test", str, "test_field")
        TypeValidator.validate_type(123, int, "test_field")
        TypeValidator.validate_type(True, bool, "test_field")

        # Invalid cases
        with pytest.raises(Exception):
            TypeValidator.validate_type("test", int, "test_field")

    def test_validate_dict_structure(self):
        """Test dictionary structure validation."""
        schema = {
            "name": str,
            "age": int,
            "active": bool
        }

        # Valid data
        valid_data = {
            "name": "John",
            "age": 30,
            "active": True
        }
        validate_config(valid_data, schema)

        # Invalid data
        invalid_data = {
            "name": "John",
            "age": "thirty",  # Should be int
            "active": True
        }
        with pytest.raises(Exception):
            validate_config(invalid_data, schema)

    def test_validate_type_complex(self):
        """Test complex type validation (Union, Optional, List)."""
        from typing import Union, Optional, List

        # Union types
        assert TypeValidator._is_valid_type("test", Union[str, int])
        assert TypeValidator._is_valid_type(123, Union[str, int])

        # Optional types
        assert TypeValidator._is_valid_type(None, Optional[str])
        assert TypeValidator._is_valid_type("test", Optional[str])

        # List types
        assert TypeValidator._is_valid_type(["a", "b"], List[str])
        assert not TypeValidator._is_valid_type(["a", 1], List[str])


class TestConfigEnhancer:
    """Test enhanced configuration management."""

    @patch('utils.config_enhancer.os.getenv')
    def test_load_from_environment(self, mock_getenv):
        """Test loading configuration from environment variables."""
        mock_getenv.side_effect = lambda key: {
            "GTPLANNER_LLM_API_KEY": "env-api-key",
            "LLM_BASE_URL": "env-base-url",
            "GTPLANNER_LLM_MODEL": "env-model"
        }.get(key)

        enhancer = ConfigEnhancer()
        config = enhancer._load_from_environment()

        assert "llm" in config
        assert config["llm"]["api_key"] == "env-api-key"
        assert config["llm"]["base_url"] == "env-base-url"
        assert config["llm"]["model"] == "env-model"

    def test_apply_defaults(self):
        """Test applying default values."""
        enhancer = ConfigEnhancer()
        config = {
            "llm": {
                "api_key": "test-key"
            }
        }

        enhanced_config = enhancer._apply_defaults(config)

        # Should have multilingual defaults
        assert "multilingual" in enhanced_config
        assert enhanced_config["multilingual"]["default_language"] == "en"
        assert enhanced_config["multilingual"]["auto_detect"] is True

        # Should preserve existing values
        assert enhanced_config["llm"]["api_key"] == "test-key"

    def test_get_config_value(self):
        """Test getting configuration values using dot notation."""
        enhancer = ConfigEnhancer()
        enhancer._config_cache = {
            "llm": {
                "api_key": "test-key",
                "base_url": "https://api.test.com"
            }
        }

        assert enhancer.get_config_value("llm.api_key") == "test-key"
        assert enhancer.get_config_value("llm.base_url") == "https://api.test.com"
        assert enhancer.get_config_value("llm.nonexistent", "default") == "default"


class TestIntegration:
    """Integration tests for configuration system."""

    def test_validate_and_get_config(self):
        """Test the convenience function for configuration validation."""
        config = {
            "llm": {
                "api_key": "sk-test123",
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-4"
            }
        }

        validated_config, errors, warnings = validate_and_get_config(config)

        assert "llm" in validated_config
        # Should have no critical errors with valid config
        assert len([e for e in errors if "critical" in e.lower()]) == 0

    def test_config_enhancer_integration(self):
        """Test the complete configuration enhancement flow."""
        with patch('utils.config_enhancer.os.path.exists', return_value=False):
            with patch('utils.config_enhancer.os.getenv', return_value=None):
                enhancer = ConfigEnhancer()
                config = enhancer.load_config_with_fallback()

                # Should have defaults applied
                assert "multilingual" in config
                assert "llm" in config
                assert "vector_service" in config

                # LLM config should be present but incomplete
                assert "api_key" in config["llm"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])