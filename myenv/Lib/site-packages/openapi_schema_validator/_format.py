import binascii
from base64 import b64decode
from base64 import b64encode
from numbers import Number
from typing import Any
from typing import Union

from jsonschema._format import FormatChecker


def is_int32(instance: Any) -> bool:
    # bool inherits from int, so ensure bools aren't reported as ints
    if isinstance(instance, bool):
        return True
    if not isinstance(instance, int):
        return True
    return ~(1 << 31) < instance < 1 << 31


def is_int64(instance: Any) -> bool:
    # bool inherits from int, so ensure bools aren't reported as ints
    if isinstance(instance, bool):
        return True
    if not isinstance(instance, int):
        return True
    return ~(1 << 63) < instance < 1 << 63


def is_float(instance: Any) -> bool:
    # bool inherits from int
    if isinstance(instance, int):
        return True
    if not isinstance(instance, Number):
        return True
    return isinstance(instance, float)


def is_double(instance: Any) -> bool:
    # bool inherits from int
    if isinstance(instance, int):
        return True
    if not isinstance(instance, Number):
        return True
    # float has double precision in Python
    # It's double in CPython and Jython
    return isinstance(instance, float)


def is_binary(instance: Any) -> bool:
    if not isinstance(instance, (str, bytes)):
        return True
    if isinstance(instance, str):
        return False
    return True


def is_byte(instance: Union[str, bytes]) -> bool:
    if not isinstance(instance, (str, bytes)):
        return True
    if isinstance(instance, str):
        instance = instance.encode()

    encoded = b64encode(b64decode(instance))
    return encoded == instance


def is_password(instance: Any) -> bool:
    # A hint to UIs to obscure input
    return True


oas30_format_checker = FormatChecker()
oas30_format_checker.checks("int32")(is_int32)
oas30_format_checker.checks("int64")(is_int64)
oas30_format_checker.checks("float")(is_float)
oas30_format_checker.checks("double")(is_double)
oas30_format_checker.checks("binary")(is_binary)
oas30_format_checker.checks("byte", (binascii.Error, TypeError))(is_byte)
oas30_format_checker.checks("password")(is_password)

oas31_format_checker = FormatChecker()
oas31_format_checker.checks("int32")(is_int32)
oas31_format_checker.checks("int64")(is_int64)
oas31_format_checker.checks("float")(is_float)
oas31_format_checker.checks("double")(is_double)
oas31_format_checker.checks("password")(is_password)
