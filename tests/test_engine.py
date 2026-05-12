"""
Tests for app/backup/engine.py
"""

import pytest
from datetime import datetime

from app.backup.engine import build_backup_dir, build_metadata_dir, generate_filename


class TestBuildBackupDir:
    def test_standard_path(self):
        ts = datetime(2026, 5, 7)
        assert build_backup_dir("paperless", ts) == "paperless/backups/2026/05/07"

    def test_trailing_slash_stripped(self):
        ts = datetime(2026, 5, 7)
        assert build_backup_dir("paperless/", ts) == "paperless/backups/2026/05/07"

    def test_nested_base_path(self):
        ts = datetime(2026, 1, 15)
        assert build_backup_dir("my/root", ts) == "my/root/backups/2026/01/15"

    def test_day_is_zero_padded(self):
        ts = datetime(2026, 3, 4)
        assert build_backup_dir("root", ts) == "root/backups/2026/03/04"

    def test_different_days(self):
        for day in range(1, 29):
            ts = datetime(2026, 1, day)
            result = build_backup_dir("root", ts)
            assert result == f"root/backups/2026/01/{day:02d}"


class TestBuildMetadataDir:
    def test_standard_path(self):
        ts = datetime(2026, 5, 7)
        assert build_metadata_dir("paperless", ts) == "paperless/metadata/2026/05/07"

    def test_trailing_slash_stripped(self):
        ts = datetime(2026, 5, 7)
        assert build_metadata_dir("paperless/", ts) == "paperless/metadata/2026/05/07"

    def test_mirrors_backup_dir_structure(self):
        """metadata and backup dirs must share the same date path."""
        ts = datetime(2026, 11, 3)
        backup = build_backup_dir("root", ts)
        metadata = build_metadata_dir("root", ts)
        assert backup.replace("/backups/", "/metadata/") == metadata


class TestGenerateFilename:
    def test_default_template(self):
        ts = datetime(2026, 5, 7, 14, 30, 0)
        assert generate_filename("{timestamp}.tar.gz", ts) == "2026-05-07_14-30-00.tar.gz"

    def test_custom_template(self):
        ts = datetime(2026, 5, 7, 9, 5, 3)
        assert generate_filename("backup_{timestamp}.zip", ts) == "backup_2026-05-07_09-05-03.zip"

    def test_timestamp_zero_padded(self):
        ts = datetime(2026, 1, 1, 0, 0, 0)
        assert generate_filename("{timestamp}.tar.gz", ts) == "2026-01-01_00-00-00.tar.gz"

    def test_template_without_placeholder(self):
        ts = datetime(2026, 5, 7, 12, 0, 0)
        assert generate_filename("static-name.tar.gz", ts) == "static-name.tar.gz"