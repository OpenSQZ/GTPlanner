"""
Enhanced configuration management for GTPlanner.

This module provides improved configuration handling with better error recovery,
default value management, and configuration migration utilities.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import json

try:
    import toml
except ImportError:
    toml = None

from utils.config_validator import ConfigValidator, ConfigValidationResult
from utils.type_safety import TypeValidator, validate_config

logger = logging.getLogger(__name__)


class ConfigEnhancer:
    """Enhanced configuration manager with improved error handling and defaults."""

    def __init__(self, settings_file: str = "settings.toml", env_prefix: str = "GTPLANNER"):
        """Initialize the enhanced configuration manager.

        Args:
            settings_file: Path to the settings file
            env_prefix: Environment variable prefix
        """
        self.settings_file = settings_file
        self.env_prefix = env_prefix
        self.validator = ConfigValidator(settings_file)
        self._config_cache = None

    def load_config_with_fallback(self) -> Dict[str, Any]:
        """Load configuration with comprehensive fallback strategy.

        Returns:
            Configuration dictionary with defaults applied
        """
        config = {}

        # Try to load from settings file first
        file_config = self._load_from_file()
        if file_config:
            config.update(file_config)

        # Override with environment variables
        env_config = self._load_from_environment()
        config.update(env_config)

        # Apply default values for missing critical settings
        config = self._apply_defaults(config)

        # Validate the configuration
        validation_result = self.validator.validate_configuration(config)

        if not validation_result.is_valid:
            logger.warning("Configuration validation failed. Applying safe defaults.")
            config = self._apply_safe_defaults(config, validation_result)

        self._config_cache = config
        return config

    def _load_from_file(self) -> Dict[str, Any]:
        """Load configuration from settings file.

        Returns:
            Configuration dictionary from file, or empty dict if failed
        """
        if not os.path.exists(self.settings_file):
            logger.warning(f"Settings file not found: {self.settings_file}")
            return {}

        try:
            if toml:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return toml.load(f)
            else:
                logger.warning("TOML library not available, cannot parse settings file")
                return {}
        except Exception as e:
            logger.error(f"Failed to load settings file {self.settings_file}: {e}")
            return {}

    def _load_from_environment(self) -> Dict[str, Any]:
        """Load configuration from environment variables.

        Returns:
            Configuration dictionary from environment variables
        """
        config = {}

        # LLM configuration
        llm_config = {}
        if api_key := os.getenv(f"{self.env_prefix}_LLM_API_KEY") or os.getenv("LLM_API_KEY"):
            llm_config["api_key"] = api_key
        if base_url := os.getenv(f"{self.env_prefix}_LLM_BASE_URL") or os.getenv("LLM_BASE_URL"):
            llm_config["base_url"] = base_url
        if model := os.getenv(f"{self.env_prefix}_LLM_MODEL") or os.getenv("LLM_MODEL"):
            llm_config["model"] = model

        if llm_config:
            config["llm"] = llm_config

        # Multilingual configuration
        multilingual_config = {}
        if default_lang := os.getenv(f"{self.env_prefix}_DEFAULT_LANGUAGE"):
            multilingual_config["default_language"] = default_lang
        if auto_detect := os.getenv(f"{self.env_prefix}_AUTO_DETECT"):
            multilingual_config["auto_detect"] = auto_detect.lower() in ("true", "1", "yes")
        if fallback := os.getenv(f"{self.env_prefix}_FALLBACK_ENABLED"):
            multilingual_config["fallback_enabled"] = fallback.lower() in ("true", "1", "yes")
        if supported_langs := os.getenv(f"{self.env_prefix}_SUPPORTED_LANGUAGES"):
            multilingual_config["supported_languages"] = [
                lang.strip() for lang in supported_langs.split(",")
            ]

        if multilingual_config:
            config["multilingual"] = multilingual_config

        # Jina configuration
        if jina_key := os.getenv(f"{self.env_prefix}_JINA_API_KEY") or os.getenv("JINA_API_KEY"):
            config["jina"] = {"api_key": jina_key}

        # Vector service configuration
        vector_config = {}
        if base_url := os.getenv(f"{self.env_prefix}_VECTOR_SERVICE_BASE_URL") or os.getenv("VECTOR_SERVICE_BASE_URL"):
            vector_config["base_url"] = base_url
        if timeout := os.getenv(f"{self.env_prefix}_VECTOR_SERVICE_TIMEOUT") or os.getenv("VECTOR_SERVICE_TIMEOUT"):
            try:
                vector_config["timeout"] = int(timeout)
            except ValueError:
                logger.warning(f"Invalid VECTOR_SERVICE_TIMEOUT value: {timeout}")

        if vector_config:
            config["vector_service"] = vector_config

        return config

    def _apply_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values for missing configuration.

        Args:
            config: Current configuration

        Returns:
            Configuration with defaults applied
        """
        defaults = {
            "multilingual": {
                "default_language": "en",
                "auto_detect": True,
                "fallback_enabled": True,
                "supported_languages": ["en", "zh", "es", "fr", "ja"]
            },
            "jina": {
                "search_base_url": "https://s.jina.ai/",
                "web_base_url": "https://r.jina.ai/"
            },
            "vector_service": {
                "base_url": "http://localhost:8080",
                "timeout": 30,
                "tools_index_name": "document_gtplanner_tools",
                "vector_field": "combined_text"
            },
            "deep_design_docs": {
                "enable_deep_design_docs": False
            },
            "logging": {
                "level": "INFO",
                "file_enabled": True,
                "console_enabled": False,
                "max_file_size": 10485760,
                "backup_count": 5
            }
        }

        # Apply defaults recursively
        for section, section_defaults in defaults.items():
            if section not in config:
                config[section] = section_defaults
            else:
                for key, value in section_defaults.items():
                    if key not in config[section]:
                        config[section][key] = value

        return config

    def _apply_safe_defaults(self, config: Dict[str, Any],
                           validation_result: ConfigValidationResult) -> Dict[str, Any]:
        """Apply safe defaults when configuration validation fails.

        Args:
            config: Current configuration
            validation_result: Validation result

        Returns:
            Configuration with safe defaults applied
        """
        # For critical errors, use minimal safe defaults
        critical_errors = [
            error for error in validation_result.errors
            if error.get("severity") == "critical"
        ]

        if critical_errors:
            logger.error("Critical configuration errors detected. Using minimal safe defaults.")

            # Ensure at least minimal LLM configuration
            if "llm" not in config or not config["llm"].get("api_key"):
                config["llm"] = {
                    "api_key": "",  # Will be caught by validation
                    "base_url": "https://api.openai.com/v1",
                    "model": "gpt-3.5-turbo"
                }

        return config

    def get_config_value(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation.

        Args:
            key_path: Configuration key path (e.g., "llm.api_key")
            default: Default value if key doesn't exist

        Returns:
            Configuration value
        """
        if self._config_cache is None:
            self._config_cache = self.load_config_with_fallback()

        keys = key_path.split(".")
        value = self._config_cache

        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def validate_and_fix_config(self) -> Dict[str, Any]:
        """Validate configuration and attempt to fix common issues.

        Returns:
            Fixed and validated configuration
        """
        config = self.load_config_with_fallback()
        validation_result = self.validator.validate_configuration(config)

        if validation_result.is_valid:
            logger.info("Configuration is valid")
            return config

        # Attempt to fix common issues
        fixed_config = self._fix_common_issues(config, validation_result)

        # Re-validate after fixes
        fixed_validation = self.validator.validate_configuration(fixed_config)

        if fixed_validation.is_valid:
            logger.info("Configuration issues fixed")
        else:
            logger.warning("Some configuration issues could not be automatically fixed")

        return fixed_config

    def _fix_common_issues(self, config: Dict[str, Any],
                          validation_result: ConfigValidationResult) -> Dict[str, Any]:
        """Fix common configuration issues.

        Args:
            config: Current configuration
            validation_result: Validation result

        Returns:
            Fixed configuration
        """
        fixed_config = config.copy()

        for error in validation_result.errors:
            section = error["section"]
            field = error["field"]
            message = error["message"]

            # Fix missing required fields
            if "required" in message.lower() and "missing" in message.lower():
                if section not in fixed_config:
                    fixed_config[section] = {}

                # Apply safe default based on field type
                if field == "api_key":
                    fixed_config[section][field] = ""  # Will be caught by validation
                elif field in ["base_url", "model"]:
                    if section == "llm":
                        fixed_config[section][field] = "https://api.openai.com/v1" if field == "base_url" else "gpt-3.5-turbo"

            # Fix type mismatches
            elif "should be type" in message.lower():
                # Try to convert to correct type
                current_value = fixed_config.get(section, {}).get(field)
                if current_value is not None:
                    try:
                        if "bool" in message:
                            fixed_config[section][field] = str(current_value).lower() in ("true", "1", "yes")
                        elif "int" in message:
                            fixed_config[section][field] = int(current_value)
                        elif "list" in message and isinstance(current_value, str):
                            fixed_config[section][field] = [item.strip() for item in current_value.split(",")]
                    except (ValueError, TypeError):
                        # If conversion fails, use default
                        pass

        return fixed_config

    def generate_config_template(self) -> str:
        """Generate a configuration template with comments.

        Returns:
            Configuration template as string
        """
        template = """# GTPlanner Configuration Template
# Copy this file to settings.toml and customize as needed

[default]
debug = true

[default.logging]
level = "INFO"
file_enabled = true
console_enabled = false  # Disable console output
max_file_size = 10485760  # 10MB
backup_count = 5

[default.llm]
# Required: Set LLM_API_KEY, LLM_BASE_URL, LLM_MODEL environment variables
# or uncomment and set values below:
# base_url = "https://api.openai.com/v1"
# api_key = "your-api-key-here"
# model = "gpt-4"

[default.jina]
# Optional: Jina AI search service
# api_key = "your-jina-key"
search_base_url = "https://s.jina.ai/"
web_base_url = "https://r.jina.ai/"

[default.multilingual]
# Language settings
default_language = "en"
auto_detect = true
fallback_enabled = true
supported_languages = ["en", "zh", "es", "fr", "ja"]

[default.vector_service]
# Vector service for tool recommendation
base_url = "http://localhost:8080"
timeout = 30
tools_index_name = "document_gtplanner_tools"
vector_field = "combined_text"

[default.deep_design_docs]
# Enable deep design documents feature
enable_deep_design_docs = false
"""
        return template

    def save_config_template(self, filepath: str = "settings.template.toml") -> None:
        """Save configuration template to file.

        Args:
            filepath: Path where to save the template
        """
        template = self.generate_config_template()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(template)
        logger.info(f"Configuration template saved to {filepath}")


def get_enhanced_config(settings_file: str = "settings.toml") -> Dict[str, Any]:
    """Convenience function to get enhanced configuration.

    Args:
        settings_file: Path to settings file

    Returns:
        Enhanced configuration dictionary
    """
    enhancer = ConfigEnhancer(settings_file)
    return enhancer.load_config_with_fallback()


def validate_and_fix_config(settings_file: str = "settings.toml") -> Dict[str, Any]:
    """Convenience function to validate and fix configuration.

    Args:
        settings_file: Path to settings file

    Returns:
        Validated and fixed configuration
    """
    enhancer = ConfigEnhancer(settings_file)
    return enhancer.validate_and_fix_config()


def generate_config_report(settings_file: str = "settings.toml") -> str:
    """Generate a comprehensive configuration report.

    Args:
        settings_file: Path to settings file

    Returns:
        Configuration report as string
    """
    enhancer = ConfigEnhancer(settings_file)
    config = enhancer.load_config_with_fallback()
    validation_result = enhancer.validator.validate_configuration(config)

    report_lines = ["GTPlanner Enhanced Configuration Report", "=" * 50]

    # Configuration source
    report_lines.append("\n📋 CONFIGURATION SOURCES:")
    if os.path.exists(settings_file):
        report_lines.append(f"  ✅ Settings file: {settings_file}")
    else:
        report_lines.append(f"  ❌ Settings file not found: {settings_file}")

    env_vars_found = any(
        os.getenv(var) for var in ["LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL"]
    )
    if env_vars_found:
        report_lines.append("  ✅ Environment variables: Found")
    else:
        report_lines.append("  ❌ Environment variables: Missing required LLM configuration")

    # Validation status
    report_lines.append(f"\n🔍 VALIDATION STATUS: {'✅ VALID' if validation_result.is_valid else '❌ INVALID'}")

    # Critical configuration check
    llm_config = config.get("llm", {})
    has_llm_config = all(llm_config.get(key) for key in ["api_key", "base_url", "model"])
    report_lines.append(f"\n⚙️ CRITICAL CONFIGURATION: {'✅ Complete' if has_llm_config else '❌ Incomplete'}")

    return "\n".join(report_lines)