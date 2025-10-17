"""
Type safety enhancements for GTPlanner.

This module provides enhanced type annotations, runtime type checking,
and validation utilities to improve code reliability and developer experience.
"""

import inspect
import functools
from typing import (
    Any, Dict, List, Optional, Union, Type, TypeVar, Callable,
    get_type_hints, get_origin, get_args
)
from enum import Enum
from dataclasses import is_dataclass
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class TypeSafetyError(Exception):
    """Exception raised for type safety violations."""
    pass


class TypeValidator:
    """Enhanced type validator with runtime type checking."""

    @staticmethod
    def validate_type(value: Any, expected_type: Type, field_name: str = "") -> None:
        """Validate that a value matches the expected type.

        Args:
            value: The value to validate
            expected_type: The expected type
            field_name: Name of the field for error messages

        Raises:
            TypeSafetyError: If the value doesn't match the expected type
        """
        if not TypeValidator._is_valid_type(value, expected_type):
            field_info = f" for field '{field_name}'" if field_name else ""
            raise TypeSafetyError(
                f"Type validation failed{field_info}: "
                f"expected {expected_type}, got {type(value)}"
            )

    @staticmethod
    def _is_valid_type(value: Any, expected_type: Type) -> bool:
        """Check if a value matches the expected type.

        Args:
            value: The value to check
            expected_type: The expected type

        Returns:
            True if the value matches the expected type
        """
        # Handle special types
        if expected_type is Any:
            return True

        # Handle Union types
        origin = get_origin(expected_type)
        if origin is Union:
            args = get_args(expected_type)
            return any(TypeValidator._is_valid_type(value, arg) for arg in args)

        # Handle Optional types
        if origin is Optional or (origin is Union and type(None) in get_args(expected_type)):
            if value is None:
                return True
            # Check non-None types
            non_none_args = [arg for arg in get_args(expected_type) if arg is not type(None)]
            if non_none_args:
                return any(TypeValidator._is_valid_type(value, arg) for arg in non_none_args)

        # Handle List types
        if origin is list:
            if not isinstance(value, list):
                return False
            args = get_args(expected_type)
            if args:
                return all(TypeValidator._is_valid_type(item, args[0]) for item in value)
            return True

        # Handle Dict types
        if origin is dict:
            if not isinstance(value, dict):
                return False
            args = get_args(expected_type)
            if len(args) == 2:
                key_type, value_type = args
                return all(
                    TypeValidator._is_valid_type(k, key_type) and
                    TypeValidator._is_valid_type(v, value_type)
                    for k, v in value.items()
                )
            return True

        # Handle Enum types
        if inspect.isclass(expected_type) and issubclass(expected_type, Enum):
            return value in expected_type

        # Handle dataclass types
        if inspect.isclass(expected_type) and is_dataclass(expected_type):
            return isinstance(value, expected_type)

        # Handle basic types
        return isinstance(value, expected_type)

    @staticmethod
    def validate_dict_structure(data: Dict[str, Any], schema: Dict[str, Type]) -> None:
        """Validate the structure of a dictionary against a schema.

        Args:
            data: Dictionary to validate
            schema: Schema defining expected types for each key

        Raises:
            TypeSafetyError: If the dictionary doesn't match the schema
        """
        for key, expected_type in schema.items():
            if key not in data:
                raise TypeSafetyError(f"Missing required key: '{key}'")
            TypeValidator.validate_type(data[key], expected_type, key)


class TypeSafeFunction:
    """Decorator for type-safe function execution."""

    def __init__(self, validate_input: bool = True, validate_output: bool = True):
        """Initialize the type-safe function decorator.

        Args:
            validate_input: Whether to validate input parameters
            validate_output: Whether to validate return value
        """
        self.validate_input = validate_input
        self.validate_output = validate_output

    def __call__(self, func: Callable) -> Callable:
        """Apply type validation to a function.

        Args:
            func: Function to decorate

        Returns:
            Decorated function with type validation
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get type hints
            type_hints = get_type_hints(func)

            # Validate input parameters
            if self.validate_input:
                self._validate_arguments(func, args, kwargs, type_hints)

            # Execute function
            result = func(*args, **kwargs)

            # Validate return value
            if self.validate_output and 'return' in type_hints:
                TypeValidator.validate_type(result, type_hints['return'], "return value")

            return result

        return wrapper

    def _validate_arguments(self, func: Callable, args: tuple, kwargs: dict,
                           type_hints: Dict[str, Type]) -> None:
        """Validate function arguments against type hints.

        Args:
            func: The function being called
            args: Positional arguments
            kwargs: Keyword arguments
            type_hints: Type hints for the function

        Raises:
            TypeSafetyError: If any argument doesn't match its type hint
        """
        # Get parameter information
        sig = inspect.signature(func)
        parameters = sig.parameters

        # Check positional arguments
        for i, (param_name, param) in enumerate(parameters.items()):
            if i >= len(args):
                break
            if param_name in type_hints:
                TypeValidator.validate_type(args[i], type_hints[param_name], param_name)

        # Check keyword arguments
        for param_name, value in kwargs.items():
            if param_name in type_hints:
                TypeValidator.validate_type(value, type_hints[param_name], param_name)


# Convenience decorators
def type_safe(validate_input: bool = True, validate_output: bool = True) -> Callable:
    """Decorator for type-safe function execution.

    Args:
        validate_input: Whether to validate input parameters
        validate_output: Whether to validate return value

    Returns:
        Decorator function
    """
    return TypeSafeFunction(validate_input, validate_output)


def validate_config(config: Dict[str, Any], schema: Dict[str, Type]) -> None:
    """Validate configuration dictionary against a schema.

    Args:
        config: Configuration dictionary to validate
        schema: Schema defining expected types

    Raises:
        TypeSafetyError: If configuration doesn't match schema
    """
    TypeValidator.validate_dict_structure(config, schema)


def create_validated_dataclass(dataclass_type: Type[T], data: Dict[str, Any]) -> T:
    """Create a dataclass instance with validated input data.

    Args:
        dataclass_type: The dataclass type to create
        data: Dictionary with field values

    Returns:
        Validated dataclass instance

    Raises:
        TypeSafetyError: If data doesn't match dataclass field types
    """
    if not is_dataclass(dataclass_type):
        raise TypeSafetyError(f"Expected a dataclass type, got {dataclass_type}")

    # Get field types from dataclass
    field_types = {}
    for field_name, field_info in dataclass_type.__dataclass_fields__.items():
        field_types[field_name] = field_info.type

    # Validate input data
    for field_name, field_type in field_types.items():
        if field_name in data:
            TypeValidator.validate_type(data[field_name], field_type, field_name)

    # Create dataclass instance
    return dataclass_type(**data)


# Common type schemas for GTPlanner
GT_PLANNER_CONFIG_SCHEMA = {
    "session_id": str,
    "dialogue_history": list,
    "tool_execution_results": dict,
    "session_metadata": dict,
    "is_compressed": bool
}

LLM_CONFIG_SCHEMA = {
    "api_key": str,
    "base_url": str,
    "model": str
}

MULTILINGUAL_CONFIG_SCHEMA = {
    "default_language": str,
    "auto_detect": bool,
    "fallback_enabled": bool,
    "supported_languages": list
}


class ConfigType:
    """Type-safe configuration class with validation."""

    def __init__(self, config_data: Dict[str, Any], schema: Dict[str, Type]):
        """Initialize with validated configuration data.

        Args:
            config_data: Configuration data
            schema: Validation schema

        Raises:
            TypeSafetyError: If configuration doesn't match schema
        """
        validate_config(config_data, schema)
        self._data = config_data
        self._schema = schema

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with type validation.

        Args:
            key: Configuration key
            default: Default value if key doesn't exist

        Returns:
            Configuration value

        Raises:
            TypeSafetyError: If value doesn't match expected type
        """
        if key not in self._schema:
            raise TypeSafetyError(f"Unknown configuration key: '{key}'")

        value = self._data.get(key, default)
        if value is not None:
            TypeValidator.validate_type(value, self._schema[key], key)

        return value

    def to_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary.

        Returns:
            Configuration dictionary
        """
        return self._data.copy()

    def validate(self) -> bool:
        """Validate the current configuration.

        Returns:
            True if configuration is valid
        """
        try:
            validate_config(self._data, self._schema)
            return True
        except TypeSafetyError:
            return False


# Example usage decorator for GTPlanner functions
def gtplanner_type_safe(func: Callable) -> Callable:
    """Type-safe decorator specifically for GTPlanner functions.

    Args:
        func: Function to decorate

    Returns:
        Decorated function with GTPlanner-specific type validation
    """
    @functools.wraps(func)
    @type_safe(validate_input=True, validate_output=True)
    def wrapper(*args, **kwargs):
        # Additional GTPlanner-specific validation can be added here
        return func(*args, **kwargs)

    return wrapper