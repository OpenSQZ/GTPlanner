"""
Enhanced configuration validation for GTPlanner.

This module provides comprehensive configuration validation with type safety,
default value management, and detailed error reporting.
"""

import os
import re
from typing import Dict, Any, List, Optional, Union, Tuple
from enum import Enum
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class ConfigErrorSeverity(Enum):
    """Severity levels for configuration errors."""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ConfigValidationResult:
    """Result of configuration validation."""
    is_valid: bool
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    validated_config: Dict[str, Any]


class ConfigValidator:
    """Enhanced configuration validator with type safety and validation rules."""

    def __init__(self, settings_file: str = "settings.toml"):
        """Initialize the configuration validator.

        Args:
            settings_file: Path to the settings file
        """
        self.settings_file = settings_file
        self.validation_rules = self._get_validation_rules()

    def _get_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Get validation rules for different configuration sections.

        Returns:
            Dictionary of validation rules
        """
        return {
            "llm": {
                "api_key": {
                    "required": True,
                    "type": str,
                    "env_var": "LLM_API_KEY",
                    "description": "LLM API key for authentication",
                    "validation": self._validate_api_key
                },
                "base_url": {
                    "required": True,
                    "type": str,
                    "env_var": "LLM_BASE_URL",
                    "description": "Base URL for LLM API",
                    "validation": self._validate_url
                },
                "model": {
                    "required": True,
                    "type": str,
                    "env_var": "LLM_MODEL",
                    "description": "Model name to use",
                    "validation": self._validate_model_name
                }
            },
            "multilingual": {
                "default_language": {
                    "required": False,
                    "type": str,
                    "default": "en",
                    "description": "Default system language",
                    "validation": self._validate_language_code
                },
                "auto_detect": {
                    "required": False,
                    "type": bool,
                    "default": True,
                    "description": "Enable automatic language detection"
                },
                "fallback_enabled": {
                    "required": False,
                    "type": bool,
                    "default": True,
                    "description": "Enable fallback to default language"
                },
                "supported_languages": {
                    "required": False,
                    "type": list,
                    "default": ["en", "zh", "es", "fr", "ja"],
                    "description": "List of supported language codes",
                    "validation": self._validate_language_list
                }
            },
            "jina": {
                "api_key": {
                    "required": False,
                    "type": str,
                    "env_var": "JINA_API_KEY",
                    "description": "Jina API key for search functionality"
                },
                "search_base_url": {
                    "required": False,
                    "type": str,
                    "default": "https://s.jina.ai/",
                    "description": "Base URL for Jina search API",
                    "validation": self._validate_url
                },
                "web_base_url": {
                    "required": False,
                    "type": str,
                    "default": "https://r.jina.ai/",
                    "description": "Base URL for Jina web API",
                    "validation": self._validate_url
                }
            },
            "vector_service": {
                "base_url": {
                    "required": False,
                    "type": str,
                    "default": "http://localhost:8080",
                    "env_var": "VECTOR_SERVICE_BASE_URL",
                    "description": "Base URL for vector service",
                    "validation": self._validate_url
                },
                "timeout": {
                    "required": False,
                    "type": int,
                    "default": 30,
                    "env_var": "VECTOR_SERVICE_TIMEOUT",
                    "description": "Timeout for vector service requests",
                    "validation": self._validate_positive_int
                },
                "tools_index_name": {
                    "required": False,
                    "type": str,
                    "default": "document_gtplanner_tools",
                    "env_var": "VECTOR_SERVICE_INDEX_NAME",
                    "description": "Index name for tools in vector service"
                },
                "vector_field": {
                    "required": False,
                    "type": str,
                    "default": "combined_text",
                    "env_var": "VECTOR_SERVICE_VECTOR_FIELD",
                    "description": "Vector field name for document embedding"
                }
            },
            "deep_design_docs": {
                "enable_deep_design_docs": {
                    "required": False,
                    "type": bool,
                    "default": False,
                    "env_var": "GTPLANNER_ENABLE_DEEP_DESIGN_DOCS",
                    "description": "Enable deep design documents feature"
                }
            },
            "logging": {
                "level": {
                    "required": False,
                    "type": str,
                    "default": "INFO",
                    "description": "Logging level",
                    "validation": self._validate_log_level
                },
                "file_enabled": {
                    "required": False,
                    "type": bool,
                    "default": True,
                    "description": "Enable file logging"
                },
                "console_enabled": {
                    "required": False,
                    "type": bool,
                    "default": False,
                    "description": "Enable console logging"
                },
                "max_file_size": {
                    "required": False,
                    "type": int,
                    "default": 10485760,
                    "description": "Maximum log file size in bytes",
                    "validation": self._validate_positive_int
                },
                "backup_count": {
                    "required": False,
                    "type": int,
                    "default": 5,
                    "description": "Number of backup log files to keep",
                    "validation": self._validate_positive_int
                }
            }
        }

    def validate_configuration(self, config: Dict[str, Any]) -> ConfigValidationResult:
        """Validate the complete configuration.

        Args:
            config: Configuration dictionary to validate

        Returns:
            Validation result with errors, warnings, and validated config
        """
        errors = []
        warnings = []
        validated_config = {}

        # Validate each section
        for section_name, section_rules in self.validation_rules.items():
            section_config = config.get(section_name, {})
            section_result = self._validate_section(section_name, section_config, section_rules)

            errors.extend(section_result["errors"])
            warnings.extend(section_result["warnings"])
            validated_config[section_name] = section_result["validated_config"]

        # Check for critical configuration issues
        critical_errors = self._check_critical_configuration(validated_config)
        errors.extend(critical_errors)

        is_valid = len([e for e in errors if e.get("severity") in ["critical", "error"]]) == 0

        return ConfigValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            validated_config=validated_config
        )

    def _validate_section(self, section_name: str, section_config: Dict[str, Any],
                         section_rules: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a configuration section.

        Args:
            section_name: Name of the configuration section
            section_config: Configuration for this section
            section_rules: Validation rules for this section

        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []
        validated_config = {}

        for field_name, field_rules in section_rules.items():
            field_value = section_config.get(field_name)

            # Check environment variable if specified
            if field_value is None and "env_var" in field_rules:
                field_value = os.getenv(field_rules["env_var"])

            # Use default value if not provided
            if field_value is None and "default" in field_rules:
                field_value = field_rules["default"]

            # Check if required field is missing
            if field_value is None and field_rules.get("required", False):
                errors.append({
                    "section": section_name,
                    "field": field_name,
                    "severity": ConfigErrorSeverity.ERROR.value,
                    "message": f"Required field '{field_name}' is missing",
                    "description": field_rules.get("description", "")
                })
                continue

            # Skip validation if field is optional and not provided
            if field_value is None:
                continue

            # Validate type
            expected_type = field_rules.get("type")
            if expected_type and not isinstance(field_value, expected_type):
                errors.append({
                    "section": section_name,
                    "field": field_name,
                    "severity": ConfigErrorSeverity.ERROR.value,
                    "message": f"Field '{field_name}' should be type {expected_type.__name__}, got {type(field_value).__name__}",
                    "description": field_rules.get("description", "")
                })
                continue

            # Run custom validation if specified
            validation_func = field_rules.get("validation")
            if validation_func:
                try:
                    validation_result = validation_func(field_value, field_name, section_name)
                    if validation_result:
                        if validation_result.get("severity") == ConfigErrorSeverity.ERROR.value:
                            errors.append({
                                "section": section_name,
                                "field": field_name,
                                "severity": ConfigErrorSeverity.ERROR.value,
                                "message": validation_result["message"],
                                "description": field_rules.get("description", "")
                            })
                        elif validation_result.get("severity") == ConfigErrorSeverity.WARNING.value:
                            warnings.append({
                                "section": section_name,
                                "field": field_name,
                                "severity": ConfigErrorSeverity.WARNING.value,
                                "message": validation_result["message"],
                                "description": field_rules.get("description", "")
                            })
                except Exception as e:
                    errors.append({
                        "section": section_name,
                        "field": field_name,
                        "severity": ConfigErrorSeverity.ERROR.value,
                        "message": f"Validation failed for field '{field_name}': {str(e)}",
                        "description": field_rules.get("description", "")
                    })

            # Add validated field to result
            validated_config[field_name] = field_value

        return {
            "errors": errors,
            "warnings": warnings,
            "validated_config": validated_config
        }

    def _check_critical_configuration(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for critical configuration issues.

        Args:
            config: Validated configuration

        Returns:
            List of critical errors
        """
        critical_errors = []

        # Check if LLM configuration is complete
        llm_config = config.get("llm", {})
        if not llm_config.get("api_key"):
            critical_errors.append({
                "section": "llm",
                "field": "api_key",
                "severity": ConfigErrorSeverity.CRITICAL.value,
                "message": "LLM API key is required for GTPlanner to function",
                "description": "Set LLM_API_KEY environment variable or configure in settings.toml"
            })

        if not llm_config.get("base_url"):
            critical_errors.append({
                "section": "llm",
                "field": "base_url",
                "severity": ConfigErrorSeverity.CRITICAL.value,
                "message": "LLM base URL is required for GTPlanner to function",
                "description": "Set LLM_BASE_URL environment variable or configure in settings.toml"
            })

        # Check multilingual configuration consistency
        multilingual_config = config.get("multilingual", {})
        default_language = multilingual_config.get("default_language", "en")
        supported_languages = multilingual_config.get("supported_languages", [])

        if default_language not in supported_languages:
            critical_errors.append({
                "section": "multilingual",
                "field": "default_language",
                "severity": ConfigErrorSeverity.ERROR.value,
                "message": f"Default language '{default_language}' is not in supported languages list",
                "description": "Add the default language to supported_languages or change the default"
            })

        return critical_errors

    # Validation helper methods
    def _validate_api_key(self, value: str, field_name: str, section_name: str) -> Optional[Dict[str, Any]]:
        """Validate API key format."""
        if not value or not isinstance(value, str):
            return {
                "severity": ConfigErrorSeverity.ERROR.value,
                "message": "API key must be a non-empty string"
            }

        # Basic API key validation (starts with sk- for OpenAI, etc.)
        if value.startswith("sk-") and len(value) < 20:
            return {
                "severity": ConfigErrorSeverity.WARNING.value,
                "message": "API key appears to be too short"
            }

        # For testing purposes, allow shorter keys
        if len(value) < 5:
            return {
                "severity": ConfigErrorSeverity.WARNING.value,
                "message": "API key appears to be too short"
            }

        return None

    def _validate_url(self, value: str, field_name: str, section_name: str) -> Optional[Dict[str, Any]]:
        """Validate URL format."""
        if not value or not isinstance(value, str):
            return {
                "severity": ConfigErrorSeverity.ERROR.value,
                "message": "URL must be a non-empty string"
            }

        # Basic URL validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        if not url_pattern.match(value):
            return {
                "severity": ConfigErrorSeverity.WARNING.value,
                "message": "URL format appears to be invalid"
            }

        return None

    def _validate_model_name(self, value: str, field_name: str, section_name: str) -> Optional[Dict[str, Any]]:
        """Validate model name format."""
        if not value or not isinstance(value, str):
            return {
                "severity": ConfigErrorSeverity.ERROR.value,
                "message": "Model name must be a non-empty string"
            }

        # Check for common model name patterns
        if len(value) < 2:
            return {
                "severity": ConfigErrorSeverity.WARNING.value,
                "message": "Model name appears to be too short"
            }

        return None

    def _validate_language_code(self, value: str, field_name: str, section_name: str) -> Optional[Dict[str, Any]]:
        """Validate language code format."""
        if not value or not isinstance(value, str):
            return {
                "severity": ConfigErrorSeverity.ERROR.value,
                "message": "Language code must be a non-empty string"
            }

        # Standard language codes are 2-3 characters
        if len(value) not in [2, 3]:
            return {
                "severity": ConfigErrorSeverity.WARNING.value,
                "message": "Language code should typically be 2-3 characters"
            }

        # Check if it's a known language code
        supported_languages = ["en", "zh", "es", "fr", "ja", "de", "ru", "ko"]
        if value.lower() not in supported_languages:
            return {
                "severity": ConfigErrorSeverity.WARNING.value,
                "message": f"Language code '{value}' is not in the common supported languages list"
            }

        return None

    def _validate_language_list(self, value: List[str], field_name: str, section_name: str) -> Optional[Dict[str, Any]]:
        """Validate list of language codes."""
        if not isinstance(value, list):
            return {
                "severity": ConfigErrorSeverity.ERROR.value,
                "message": "Supported languages must be a list"
            }

        if not value:
            return {
                "severity": ConfigErrorSeverity.ERROR.value,
                "message": "Supported languages list cannot be empty"
            }

        # Validate each language code
        for lang in value:
            lang_result = self._validate_language_code(lang, field_name, section_name)
            if lang_result and lang_result.get("severity") == ConfigErrorSeverity.ERROR.value:
                return lang_result

        return None

    def _validate_log_level(self, value: str, field_name: str, section_name: str) -> Optional[Dict[str, Any]]:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        if value.upper() not in valid_levels:
            return {
                "severity": ConfigErrorSeverity.ERROR.value,
                "message": f"Log level must be one of: {', '.join(valid_levels)}"
            }

        return None

    def _validate_positive_int(self, value: int, field_name: str, section_name: str) -> Optional[Dict[str, Any]]:
        """Validate positive integer."""
        if not isinstance(value, int) or value <= 0:
            return {
                "severity": ConfigErrorSeverity.ERROR.value,
                "message": f"{field_name} must be a positive integer"
            }

        return None


def validate_and_get_config(config: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str], List[str]]:
    """Convenience function to validate configuration and get results.

    Args:
        config: Configuration dictionary to validate

    Returns:
        Tuple of (validated_config, error_messages, warning_messages)
    """
    validator = ConfigValidator()
    result = validator.validate_configuration(config)

    error_messages = [
        f"[{error['section']}.{error['field']}] {error['message']}"
        for error in result.errors
    ]

    warning_messages = [
        f"[{warning['section']}.{warning['field']}] {warning['message']}"
        for warning in result.warnings
    ]

    return result.validated_config, error_messages, warning_messages