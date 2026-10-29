import re
from decimal import Decimal, InvalidOperation


def validate_email(email):
    if not email or not isinstance(email, str):
        return False
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return bool(re.match(pattern, email.strip()))


def to_decimal(value, default=None):
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return default


def to_int(value, default=None):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def money(value):
    return Decimal(str(value)).quantize(Decimal("0.01"))


def non_negative_decimal(value):
    d = to_decimal(value)
    if d is None or d < 0:
        return None
    return d


def positive_int(value):
    i = to_int(value)
    if i is None or i <= 0:
        return None
    return i
