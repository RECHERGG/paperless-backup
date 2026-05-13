"""
Tests for app/retention/parser.py

Covers timestamp extraction from filenames.
"""

from datetime import datetime
from app.retention.parser import parse_timestamp_from_filename


class TestParseTimestampFromFilename:
    def test_standard_filename(self):
        result = parse_timestamp_from_filename("2026-05-07_14-30-00.tar.gz")
        assert result == datetime(2026, 5, 7, 14, 30, 0)

    def test_full_remote_path(self):
        result = parse_timestamp_from_filename(
            "paperless-backups/2026/05/2026-05-07_14-30-00.tar.gz"
        )
        assert result == datetime(2026, 5, 7, 14, 30, 0)

    def test_no_timestamp_returns_none(self):
        result = parse_timestamp_from_filename("backup-no-timestamp.tar.gz")
        assert result is None

    def test_empty_string_returns_none(self):
        result = parse_timestamp_from_filename("")
        assert result is None

    def test_partial_timestamp_returns_none(self):
        # Only a date, no time portion
        result = parse_timestamp_from_filename("2026-05-07.tar.gz")
        assert result is None

    def test_midnight(self):
        result = parse_timestamp_from_filename("2026-01-01_00-00-00.tar.gz")
        assert result == datetime(2026, 1, 1, 0, 0, 0)

    def test_end_of_year(self):
        result = parse_timestamp_from_filename("2025-12-31_23-59-59.tar.gz")
        assert result == datetime(2025, 12, 31, 23, 59, 59)
