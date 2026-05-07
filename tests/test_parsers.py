"""
Tests for app/config/parsers.py

These are pure functions — no mocking needed.
Equivalent to a simple JUnit test class.
"""

import pytest
from app.config.parsers import parse_int, parse_bool, parse_str


class TestParseInt:
    def test_valid_integer(self):
        assert parse_int("42") == 42

    def test_none_returns_default(self):
        assert parse_int(None, default=99) == 99

    def test_none_without_default_returns_none(self):
        assert parse_int(None) is None

    def test_invalid_string_raises(self):
        with pytest.raises(ValueError):
            parse_int("not-a-number")

    def test_zero(self):
        assert parse_int("0") == 0

    def test_negative(self):
        assert parse_int("-5") == -5


class TestParseBool:
    @pytest.mark.parametrize("value", ["1", "true", "True", "TRUE", "yes", "y", "on"])
    def test_truthy_values(self, value):
        assert parse_bool(value) is True

    @pytest.mark.parametrize("value", ["0", "false", "False", "no", "off", "anything"])
    def test_falsy_values(self, value):
        assert parse_bool(value) is False

    def test_none_returns_default_true(self):
        assert parse_bool(None, default=True) is True

    def test_none_returns_default_false(self):
        assert parse_bool(None, default=False) is False

    def test_none_without_default_returns_none(self):
        assert parse_bool(None) is None

    def test_strips_whitespace(self):
        assert parse_bool("  true  ") is True


class TestParseStr:
    def test_returns_value(self):
        assert parse_str("hello") == "hello"

    def test_none_returns_default(self):
        assert parse_str(None, default="fallback") == "fallback"

    def test_none_without_default_returns_none(self):
        assert parse_str(None) is None

    def test_empty_string_is_valid(self):
        assert parse_str("") == ""