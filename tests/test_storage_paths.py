"""
Tests for the sidecar path derivation in sftp/storage.py.

This is pure logic — no SFTP, no mocking needed.
"""

import pytest
from app.storage.sftp.storage import _backup_path_to_sidecar_path


class TestBackupPathToSidecarPath:
    def test_standard_path(self):
        backup = "paperless/backups/2026/05/07/2026-05-07_12-00-00.tar.gz"
        sidecar = _backup_path_to_sidecar_path(backup)
        assert sidecar == "paperless/metadata/2026/05/07/2026-05-07_12-00-00.tar.gz.sha256"

    def test_replaces_only_first_backups_segment(self):
        # Pathological case: 'backups' also appears in the root name
        backup = "backups/backups/2026/05/07/file.tar.gz"
        sidecar = _backup_path_to_sidecar_path(backup)
        assert sidecar == "backups/metadata/2026/05/07/file.tar.gz.sha256"

    def test_appends_sha256_extension(self):
        backup = "root/backups/2026/01/01/file.tar.gz"
        sidecar = _backup_path_to_sidecar_path(backup)
        assert sidecar.endswith(".sha256")

    def test_no_backups_segment_returns_none(self):
        assert _backup_path_to_sidecar_path("root/other/file.tar.gz") is None

    def test_preserves_date_segments(self):
        backup = "root/backups/2025/12/31/file.tar.gz"
        sidecar = _backup_path_to_sidecar_path(backup)
        assert "2025/12/31" in sidecar

    def test_round_trip_structure(self):
        """The sidecar path must sit under /metadata/ at the same date depth."""
        backup = "paperless/backups/2026/05/07/2026-05-07_00-00-00.tar.gz"
        sidecar = _backup_path_to_sidecar_path(backup)
        assert "/metadata/" in sidecar
        assert "/backups/" not in sidecar