"""
Configuration loader for Paperless Backup.

This module loads a TOML configuration file, resolves environment
variables, and returns a fully expanded Python dictionary that can
be safely used by the application.

Supported environment syntax:
- ${VAR}            -> required environment variable
- ${VAR:default}    -> optional with fallback value
"""

import tomllib
import os
import re
from copy import deepcopy

ENV_PATTERN = re.compile(r"\$\{([^}:]+)(?::([\s\S]*))?\}")

def resolve_env(values: str) -> str:
    """
    Resolve environment variables inside a string.

    Supports:
    - ${VAR}: replaces with environment variable value
    - ${VAR:default}: uses default if variable is not set

    Args:
        value (str): Input string containing environment placeholders

    Returns:
        str: Resolved string with environment variables substituted
    """
    def replacer(match):
        key = match.group(1)
        default = match.group(2)
        return os.getenv(key, default if default is not None else "")

    return ENV_PATTERN.sub(replacer, values)

def resolve_config(obj):
    """
    Recursively resolve environment variables in a nested configuration.

    This function walks through dictionaries, lists, and strings,
    replacing all environment placeholders with actual values.

    Args:
        obj (Any): Configuration object (dict, list, str, or primitive)
    
    Returns:
        Any: Fully resolved configuration object
    """
    if isinstance(obj, dict):
        return {k: resolve_config(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [resolve_config(item) for item in obj]

    if isinstance(obj, str):
        return resolve_env(obj)

    return obj

def load_config(path: str ="config.toml") -> dict:
    """
    Load and resolve the application configuration.

    Steps:
    1. Read TOML file
    2. Deep copy raw data
    3. Resolve all environment variables
    4. Return final configuration dictionary

    Args:
        path (str): Path to the TOML configuration file

    Returns:
        dict: Fully resolved configuration
    """
    with open(path, "rb") as f:
        raw = tomllib.load(f)

    return resolve_config(deepcopy(raw))