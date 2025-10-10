# Testing and Configuration Validation Guide

This document describes the testing infrastructure and configuration validation features added to GTPlanner.

## Overview

This PR adds comprehensive testing coverage and configuration validation capabilities to improve code quality and developer experience.

## New Features

### 1. Configuration Validation and Health Checking

Enhanced `utils/config_manager.py` with:

- **API Key Validation**: Validates format and detects placeholder values
- **URL Validation**: Ensures LLM and vector service URLs are properly formatted
- **Health Status API**: Provides comprehensive system health information
- **Component-level Validation**: Checks each component (LLM, Jina, Vector Service, etc.)

#### Usage Example

```python
from utils.config_manager import MultilingualConfig

config = MultilingualConfig()

# Validate configuration
warnings = config.validate_config()
if warnings:
    for warning in warnings:
        print(f"Warning: {warning}")

# Get health status
health = config.get_health_status()
print(f"System healthy: {health['healthy']}")
print(f"Components: {health['components']}")
```

### 2. Configuration Validation CLI Tool

A new command-line tool `check_config.py` helps users quickly diagnose configuration issues.

#### Features

- ✅ Check required environment variables
- ✅ Validate configuration files
- ✅ Test API key formats
- ✅ Verify URL validity
- ✅ Display component health status
- ✅ Provide actionable recommendations

#### Usage

```bash
# Basic validation
python check_config.py

# Detailed output with values (be careful with sensitive data)
python check_config.py --verbose

# JSON output for automation
python check_config.py --json

# Show configuration help
python check_config.py --help-config
```

#### Output Example

```
============================================================
GTPlanner Configuration Validation
============================================================

1. Checking Environment Variables...
✓ LLM_API_KEY is set
✓ LLM_BASE_URL is set
✓ LLM_MODEL is set
⚠ JINA_API_KEY is not set (optional)

2. Checking Configuration Files...
✓ settings.toml found
✓ pyproject.toml found
  .env not found (optional)

3. Validating Configuration...
✓ No configuration warnings

4. Checking System Health...
✓ Multilingual component: OK
✓ Llm component: OK
  Jina component: Info
  Vector_service component: Info

============================================================
Summary
============================================================
✓ Configuration is valid and healthy!
```

### 3. Comprehensive Unit Tests

Added extensive test coverage for critical modules:

#### `tests/test_language_detection.py`

Tests for `utils/language_detection.py`:
- Language detection for all supported languages (EN, ZH, JA, ES, FR)
- User preference override
- Chinese vs Japanese disambiguation
- Edge cases (empty text, mixed languages, code snippets)
- Helper functions and global instances

**Test Coverage**: 100+ test cases covering all functionality

#### `tests/test_config_manager.py`

Tests for `utils/config_manager.py`:
- Configuration loading from environment and files
- Validation functions
- API key format validation
- URL validation
- Health status checking
- Global convenience functions
- Edge cases and error handling

**Test Coverage**: 80+ test cases covering all functionality

## Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Or using uv
uv sync --group dev
```

### Run All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_language_detection.py
pytest tests/test_config_manager.py

# Run with coverage report
pytest --cov=utils --cov-report=html
```

### Test Organization

```
tests/
├── test_basic.py              # Existing basic tests
├── test_retry_handler.py      # Existing retry handler tests
├── test_language_detection.py # NEW: Language detection tests
└── test_config_manager.py     # NEW: Configuration manager tests
```

## Implementation Details

### Enhanced Config Manager Methods

#### `_validate_llm_config()`
Validates LLM configuration including:
- API key presence and format
- Base URL validity
- Model name configuration

#### `_validate_api_keys()`
Validates API keys including:
- Format checking
- Placeholder detection

#### `_validate_vector_service_config()`
Validates vector service configuration:
- URL format validation

#### `_is_valid_api_key()`
Static method to check API key format:
- Minimum length requirement (20 characters)
- Placeholder pattern detection
- Common invalid patterns

#### `_is_valid_url()`
Static method to validate URLs:
- Scheme and netloc presence
- Proper URL parsing

#### `get_health_status()`
Returns comprehensive health information:
```python
{
    "healthy": bool,
    "warnings": [],
    "errors": [],
    "components": {
        "multilingual": {...},
        "llm": {...},
        "jina": {...},
        "vector_service": {...}
    }
}
```

## Benefits

### For Users
- **Quick Configuration Diagnosis**: Identify configuration issues before running the application
- **Clear Error Messages**: Actionable feedback on what needs to be fixed
- **Reduced Debugging Time**: Catch configuration errors early

### For Developers
- **Increased Confidence**: Comprehensive test coverage ensures code quality
- **Easier Maintenance**: Well-tested code is easier to refactor
- **Better Documentation**: Tests serve as usage examples
- **Regression Prevention**: Tests catch breaking changes early

## Best Practices

### When Adding New Configuration Options

1. Add validation in `config_manager.py`
2. Update `check_config.py` to check the new option
3. Add tests in `test_config_manager.py`
4. Document in README or relevant docs

### When Modifying Language Detection

1. Update `language_detection.py`
2. Add/update tests in `test_language_detection.py`
3. Ensure all edge cases are covered
4. Test with real-world examples

## Future Improvements

Potential enhancements for future PRs:

1. **Integration Tests**: Test full application workflows
2. **Performance Tests**: Benchmark language detection speed
3. **Mock LLM Tests**: Test without actual API calls
4. **CI/CD Integration**: Automated testing on pull requests
5. **Test Coverage Reporting**: Automated coverage reports
6. **Configuration Schema Validation**: JSON Schema for settings

## Contributing

When contributing to GTPlanner:

1. **Write Tests First**: Follow TDD principles when possible
2. **Maintain Coverage**: Ensure new code has test coverage
3. **Test Edge Cases**: Think about boundary conditions
4. **Document Tests**: Add docstrings explaining test purposes
5. **Run Tests Locally**: Ensure all tests pass before submitting PR

## Related Files

- `utils/config_manager.py` - Enhanced configuration management
- `utils/language_detection.py` - Language detection utilities
- `check_config.py` - Configuration validation CLI tool
- `tests/test_config_manager.py` - Config manager tests
- `tests/test_language_detection.py` - Language detection tests

## Questions?

For questions or issues related to testing or configuration:

1. Check existing tests for examples
2. Run `python check_config.py --help-config` for configuration help
3. Refer to the main README.md for general setup
4. Open an issue on GitHub for bug reports or feature requests

---

**Note**: This testing infrastructure was added as part of a comprehensive effort to improve code quality and developer experience. The tests are designed to be maintainable and serve as living documentation for the codebase.
