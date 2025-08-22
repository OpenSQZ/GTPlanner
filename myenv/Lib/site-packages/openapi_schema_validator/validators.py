import warnings
from typing import Any
from typing import Type

from jsonschema import _keywords
from jsonschema import _legacy_keywords
from jsonschema.validators import Draft202012Validator
from jsonschema.validators import create
from jsonschema.validators import extend
from jsonschema_specifications import REGISTRY as SPECIFICATIONS

from openapi_schema_validator import _format as oas_format
from openapi_schema_validator import _keywords as oas_keywords
from openapi_schema_validator import _types as oas_types
from openapi_schema_validator._types import oas31_type_checker

OAS30Validator = create(
    meta_schema=SPECIFICATIONS.contents(
        "http://json-schema.org/draft-04/schema#",
    ),
    validators={
        "multipleOf": _keywords.multipleOf,
        # exclusiveMaximum supported inside maximum_draft3_draft4
        "maximum": _legacy_keywords.maximum_draft3_draft4,
        # exclusiveMinimum supported inside minimum_draft3_draft4
        "minimum": _legacy_keywords.minimum_draft3_draft4,
        "maxLength": _keywords.maxLength,
        "minLength": _keywords.minLength,
        "pattern": _keywords.pattern,
        "maxItems": _keywords.maxItems,
        "minItems": _keywords.minItems,
        "uniqueItems": _keywords.uniqueItems,
        "maxProperties": _keywords.maxProperties,
        "minProperties": _keywords.minProperties,
        "enum": _keywords.enum,
        # adjusted to OAS
        "type": oas_keywords.type,
        "allOf": oas_keywords.allOf,
        "oneOf": oas_keywords.oneOf,
        "anyOf": oas_keywords.anyOf,
        "not": _keywords.not_,
        "items": oas_keywords.items,
        "properties": _keywords.properties,
        "required": oas_keywords.required,
        "additionalProperties": oas_keywords.additionalProperties,
        # TODO: adjust description
        "format": oas_keywords.format,
        # TODO: adjust default
        "$ref": _keywords.ref,
        # fixed OAS fields
        "discriminator": oas_keywords.not_implemented,
        "readOnly": oas_keywords.not_implemented,
        "writeOnly": oas_keywords.not_implemented,
        "xml": oas_keywords.not_implemented,
        "externalDocs": oas_keywords.not_implemented,
        "example": oas_keywords.not_implemented,
        "deprecated": oas_keywords.not_implemented,
    },
    type_checker=oas_types.oas30_type_checker,
    format_checker=oas_format.oas30_format_checker,
    # NOTE: version causes conflict with global jsonschema validator
    # See https://github.com/python-openapi/openapi-schema-validator/pull/12
    # version="oas30",
    id_of=lambda schema: schema.get("id", ""),
)

OAS30ReadValidator = extend(
    OAS30Validator,
    validators={
        "required": oas_keywords.read_required,
        "writeOnly": oas_keywords.read_writeOnly,
    },
)
OAS30WriteValidator = extend(
    OAS30Validator,
    validators={
        "required": oas_keywords.write_required,
        "readOnly": oas_keywords.write_readOnly,
    },
)

OAS31Validator = extend(
    Draft202012Validator,
    {
        # adjusted to OAS
        "allOf": oas_keywords.allOf,
        "oneOf": oas_keywords.oneOf,
        "anyOf": oas_keywords.anyOf,
        "description": oas_keywords.not_implemented,
        # fixed OAS fields
        "discriminator": oas_keywords.not_implemented,
        "xml": oas_keywords.not_implemented,
        "externalDocs": oas_keywords.not_implemented,
        "example": oas_keywords.not_implemented,
    },
    type_checker=oas31_type_checker,
    format_checker=oas_format.oas31_format_checker,
)
