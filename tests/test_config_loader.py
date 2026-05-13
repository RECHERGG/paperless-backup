"""
Tests for app/config/loader.py

Tests env-var resolution without touching the filesystem for most cases.
"""

import os
from unittest.mock import patch

from app.config.loader import resolve_env, resolve_config


class TestResolveEnv:
    def test_replaces_set_variable(self):
        with patch.dict(os.environ, {"MY_VAR": "hello"}):
            assert resolve_env("${MY_VAR}") == "hello"

    def test_uses_default_when_unset(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("MISSING_VAR", None)
            result = resolve_env("${MISSING_VAR:fallback}")
        assert result == "fallback"

    def test_empty_string_when_unset_no_default(self):
        env = {k: v for k, v in os.environ.items() if k != "MISSING_VAR"}
        with patch.dict(os.environ, env, clear=True):
            result = resolve_env("${MISSING_VAR}")
        assert result == ""

    def test_multiple_vars_in_one_string(self):
        with patch.dict(os.environ, {"HOST": "myhost", "PORT": "22"}):
            result = resolve_env("${HOST}:${PORT}")
        assert result == "myhost:22"

    def test_no_placeholder_passthrough(self):
        assert resolve_env("plain string") == "plain string"

    def test_variable_overrides_default(self):
        with patch.dict(os.environ, {"MY_PORT": "2222"}):
            result = resolve_env("${MY_PORT:22}")
        assert result == "2222"


class TestResolveConfig:
    def test_resolves_nested_dict(self):
        with patch.dict(os.environ, {"HOST": "sftp.example.com"}):
            config = resolve_config({"storage": {"host": "${HOST}"}})
        assert config["storage"]["host"] == "sftp.example.com"

    def test_resolves_list_items(self):
        with patch.dict(os.environ, {"VAL": "resolved"}):
            result = resolve_config(["${VAL}", "static"])
        assert result == ["resolved", "static"]

    def test_non_string_primitives_passthrough(self):
        result = resolve_config({"count": 42, "flag": True})
        assert result == {"count": 42, "flag": True}

    def test_deeply_nested(self):
        with patch.dict(os.environ, {"DEEP": "value"}):
            result = resolve_config({"a": {"b": {"c": "${DEEP}"}}})
        assert result["a"]["b"]["c"] == "value"
