"""
Tests for app/retention/executor.py

Uses unittest.mock to fake the storage backend.
This is the Python equivalent of Mockito in Java.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, call, patch

from app.retention.executor import apply_retention
from app.retention.policy.simple import SimpleRetentionPolicy
from app.retention.policy.none import NoRetentionPolicy
from tests.factories import make_backup_files_range

def make_storage(remote_files: list[str]) -> MagicMock:
    """Create a mock storage that returns the given file list."""
    storage = MagicMock()
    storage.list_backups.return_value = remote_files
    return storage


def filenames_from(files) -> list[str]:
    return [f.path for f in files]


class TestApplyRetention:
    def test_no_files_does_nothing(self):
        storage = make_storage([])
        apply_retention(storage, SimpleRetentionPolicy(keep_last=5))
        storage.delete.assert_not_called()

    def test_deletes_expected_files(self, now):
        files = make_backup_files_range(now, count=10, step=timedelta(hours=1))
        storage = make_storage(filenames_from(files))
        policy = SimpleRetentionPolicy(keep_last=3)

        apply_retention(storage, policy)

        assert storage.delete.call_count == 7

    def test_does_not_delete_kept_files(self, now):
        files = make_backup_files_range(now, count=5, step=timedelta(hours=1))
        storage = make_storage(filenames_from(files))
        policy = SimpleRetentionPolicy(keep_last=5)

        apply_retention(storage, policy)

        storage.delete.assert_not_called()

    def test_none_policy_deletes_nothing(self, now):
        files = make_backup_files_range(now, count=50, step=timedelta(hours=1))
        storage = make_storage(filenames_from(files))

        apply_retention(storage, NoRetentionPolicy())

        storage.delete.assert_not_called()

    def test_dry_run_does_not_call_delete(self, now):
        files = make_backup_files_range(now, count=10, step=timedelta(hours=1))
        storage = make_storage(filenames_from(files))
        policy = SimpleRetentionPolicy(keep_last=2)

        deleted = apply_retention(storage, policy, dry_run=True)

        storage.delete.assert_not_called()
        assert deleted == 0

    def test_returns_correct_deletion_count(self, now):
        files = make_backup_files_range(now, count=10, step=timedelta(hours=1))
        storage = make_storage(filenames_from(files))
        policy = SimpleRetentionPolicy(keep_last=4)

        count = apply_retention(storage, policy)

        assert count == 6

    def test_unparseable_files_are_skipped(self):
        """Files without a timestamp in their name are skipped (can't parse → can't decide → safe)."""
        storage = make_storage(["paperless-backups/unknown-file.tar.gz"])
        # Even a very aggressive policy should not delete files it can't parse
        policy = SimpleRetentionPolicy(keep_last=1)

        apply_retention(storage, policy)

        storage.delete.assert_not_called()

    def test_storage_delete_failure_is_logged_not_raised(self, now):
        """A single failed deletion must not abort the whole retention run."""
        files = make_backup_files_range(now, count=5, step=timedelta(hours=1))
        storage = make_storage(filenames_from(files))
        storage.delete.side_effect = Exception("SFTP error")
        policy = SimpleRetentionPolicy(keep_last=1)

        # Should not raise
        apply_retention(storage, policy)