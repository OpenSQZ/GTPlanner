from typing import Any
from typing import Hashable
from typing import Mapping
from typing import Type

from jsonschema.exceptions import best_match
from jsonschema.protocols import Validator

from openapi_schema_validator.validators import OAS31Validator


def validate(
    instance: Any,
    schema: Mapping[Hashable, Any],
    cls: Type[Validator] = OAS31Validator,
    *args: Any,
    **kwargs: Any
) -> None:
    cls.check_schema(schema)
    validator = cls(schema, *args, **kwargs)
    error = best_match(validator.iter_errors(instance))
    if error is not None:
        raise error
