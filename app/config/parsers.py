"""
Primitive type parsers for configuration values.

These helpers convert string-based environment values into
proper Python types. This is required because environment
variables are always strings.
"""


def parse_int(value: str, default: int | None = None) -> int:
    """
    Convert a string to int.

    Args:
        value (str): Input string from config/env
        default (int | None): Fallback if value is None

    Returns:
        int | None: Parsed integer or default
    """
    if value is None:
        return default
    return int(value)

def parse_bool(value: str, default: bool | None = None) -> bool:
    """
    Convert a string to boolean.

    Accepted true values:
    - "1", "true", "yes", "y", "on"

    Anything else is treated as False.

    Args:
        value (str): Input string
        default (bool | None): Fallback if value is None

    Returns:
        bool | None: Parsed boolean or default
    """
    if value is None:
        return default
    
    return str(value).strip().lower() in {
        "1", "true", "yes", "y", "on"
    }

def parse_str(value: str, default: str | None = None) -> str:
    """
    Return string value or default.

    Args:
        value (str): Input value
        default (str | None): Fallback

    Returns:
        str | None
    """
    return value if value is not None else default