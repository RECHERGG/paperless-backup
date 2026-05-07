"""
Tests for app/backup/engine.py

Pure functions — no mocking needed.
"""

import pytest
from datetime import datetime

from app.backup.engine import build_remote_dir, generate_filename


class TestBuildRemoteDir:
    def test_standard_path(self):
        ts = datetime(2026, 5, 7)
        result = build_remote_dir("paperless-backups", ts)
        assert result == "paperless-backups/2026/05"

    def test_trailing_slash_stripped(self):
        ts = datetime(2026, 5, 7)
        result = build_remote_dir("paperless-backups/", ts)
        assert result == "paperless-backups/2026/05"

    def test_nested_base_path(self):
        ts = datetime(2026, 1, 15)
        result = build_remote_dir("my/nested/path", ts)
        assert result == "my/nested/path/2026/01"

    def test_different_months(self):
        for month in range(1, 13):
            ts = datetime(2026, month, 1)
            result = build_remote_dir("backups", ts)
            assert result == f"backups/2026/{month:02d}"


class TestGenerateFilename:
    def test_default_template(self):
        ts = datetime(2026, 5, 7, 14, 30, 0)
        result = generate_filename("{timestamp}.tar.gz", ts)
        assert result == "2026-05-07_14-30-00.tar.gz"

    def test_custom_template(self):
        ts = datetime(2026, 5, 7, 9, 5, 3)
        result = generate_filename("backup_{timestamp}.zip", ts)
        assert result == "backup_2026-05-07_09-05-03.zip"

    def test_timestamp_zero_padded(self):
        ts = datetime(2026, 1, 1, 0, 0, 0)
        result = generate_filename("{timestamp}.tar.gz", ts)
        assert result == "2026-01-01_00-00-00.tar.gz"

    def test_template_without_placeholder(self):
        ts = datetime(2026, 5, 7, 12, 0, 0)
        result = generate_filename("static-name.tar.gz", ts)
        assert result == "static-name.tar.gz"