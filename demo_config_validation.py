#!/usr/bin/env python3
"""
Demo script for GTPlanner configuration validation and type safety enhancements.

This script demonstrates the new configuration validation, type safety,
and enhanced configuration management features.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.config_validator import ConfigValidator
from utils.config_manager import validate_configuration, get_config_validation_report
from utils.config_enhancer import ConfigEnhancer, generate_config_report
from utils.type_safety import TypeValidator, validate_config


def demo_config_validation():
    """Demonstrate configuration validation."""
    print("🔧 GTPlanner Configuration Validation Demo")
    print("=" * 50)

    # Example configurations
    valid_config = {
        "llm": {
            "api_key": "sk-test12345678901234567890",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4"
        },
        "multilingual": {
            "default_language": "en",
            "auto_detect": True,
            "fallback_enabled": True,
            "supported_languages": ["en", "zh", "es"]
        }
    }

    invalid_config = {
        "llm": {
            "api_key": "",  # Empty API key
            "base_url": "not-a-url",  # Invalid URL
            "model": 123  # Wrong type
        },
        "multilingual": {
            "default_language": "invalid-lang",
            "auto_detect": "not-a-boolean",
            "supported_languages": "not-a-list"
        }
    }

    validator = ConfigValidator()

    print("\n✅ Valid Configuration:")
    result = validator.validate_configuration(valid_config)
    print(f"  Status: {'VALID' if result.is_valid else 'INVALID'}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Warnings: {len(result.warnings)}")

    print("\n❌ Invalid Configuration:")
    result = validator.validate_configuration(invalid_config)
    print(f"  Status: {'VALID' if result.is_valid else 'INVALID'}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Warnings: {len(result.warnings)}")

    if result.errors:
        print("\n  Error Details:")
        for error in result.errors[:3]:  # Show first 3 errors
            print(f"    - {error['section']}.{error['field']}: {error['message']}")


def demo_type_safety():
    """Demonstrate type safety features."""
    print("\n\n🔒 Type Safety Demo")
    print("=" * 50)

    # Example schema
    schema = {
        "name": str,
        "age": int,
        "active": bool,
        "tags": list
    }

    valid_data = {
        "name": "GTPlanner",
        "age": 1,
        "active": True,
        "tags": ["ai", "planning", "prd"]
    }

    invalid_data = {
        "name": "GTPlanner",
        "age": "one",  # Should be int
        "active": "yes",  # Should be bool
        "tags": "not-a-list"  # Should be list
    }

    print("\n✅ Valid Data:")
    try:
        validate_config(valid_data, schema)
        print("  ✅ Validation passed")
    except Exception as e:
        print(f"  ❌ Validation failed: {e}")

    print("\n❌ Invalid Data:")
    try:
        validate_config(invalid_data, schema)
        print("  ✅ Validation passed")
    except Exception as e:
        print(f"  ❌ Validation failed: {e}")


def demo_enhanced_config():
    """Demonstrate enhanced configuration management."""
    print("\n\n🚀 Enhanced Configuration Management Demo")
    print("=" * 50)

    enhancer = ConfigEnhancer()

    # Generate configuration report
    print("\n📋 Configuration Report:")
    report = generate_config_report()
    print(report)

    # Show configuration template
    print("\n📝 Configuration Template Preview:")
    template = enhancer.generate_config_template()
    print("\n".join(template.split("\n")[:10]))  # Show first 10 lines
    print("  ... (truncated)")


def demo_integration():
    """Demonstrate integration with existing config manager."""
    print("\n\n🔗 Integration Demo")
    print("=" * 50)

    print("\n📊 Current Configuration Validation:")
    try:
        validation_result = validate_configuration()
        print(f"  Status: {'✅ VALID' if validation_result['is_valid'] else '❌ INVALID'}")
        print(f"  Errors: {len(validation_result['errors'])}")
        print(f"  Warnings: {len(validation_result['warnings'])}")

        if validation_result['warnings']:
            print("\n  Warnings:")
            for warning in validation_result['warnings'][:2]:
                print(f"    - {warning['section']}.{warning['field']}: {warning['message']}")

    except Exception as e:
        print(f"  ❌ Validation failed: {e}")

    print("\n📄 Configuration Validation Report:")
    try:
        report = get_config_validation_report()
        # Show summary section
        lines = report.split("\n")
        for line in lines[:10]:  # Show first 10 lines
            print(f"  {line}")
        print("  ... (truncated)")
    except Exception as e:
        print(f"  ❌ Report generation failed: {e}")


def main():
    """Run all demos."""
    print("🎯 GTPlanner Configuration & Type Safety Enhancements Demo")
    print("=" * 60)

    demo_config_validation()
    demo_type_safety()
    demo_enhanced_config()
    demo_integration()

    print("\n" + "=" * 60)
    print("✅ Demo completed successfully!")
    print("\nKey Features Demonstrated:")
    print("  • Configuration validation with detailed error reporting")
    print("  • Runtime type safety with schema validation")
    print("  • Enhanced configuration management with fallbacks")
    print("  • Integration with existing GTPlanner configuration system")
    print("  • Comprehensive error handling and safe defaults")


if __name__ == "__main__":
    main()