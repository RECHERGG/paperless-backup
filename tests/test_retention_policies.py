"""
Tests for all retention policies.

Policies are pure functions (no I/O) — no mocking needed.
We build BackupFile lists and assert which paths are kept/deleted.
"""

import pytest
from datetime import datetime, timedelta

from app.retention.policy.gfs import GFSRetentionPolicy
from app.retention.policy.simple import SimpleRetentionPolicy
from app.retention.policy.time_based import TimeBasedRetentionPolicy
from app.retention.policy.daily import DailyRetentionPolicy
from app.retention.policy.none import NoRetentionPolicy

from tests.factories import make_backup_file, make_backup_files_range


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NOW = datetime(2026, 5, 7, 12, 0, 0)


def paths(files) -> set[str]:
    return {f.path for f in files}


# ---------------------------------------------------------------------------
# NoRetentionPolicy
# ---------------------------------------------------------------------------

class TestNoRetentionPolicy:
    def test_keeps_everything(self):
        files = make_backup_files_range(NOW, count=100, step=timedelta(hours=1))
        policy = NoRetentionPolicy()
        assert policy.select_files_to_keep(files) == paths(files)

    def test_empty_input(self):
        assert NoRetentionPolicy().select_files_to_keep([]) == set()

    def test_deletes_nothing(self):
        files = make_backup_files_range(NOW, count=5, step=timedelta(hours=1))
        assert NoRetentionPolicy().select_files_to_delete(files) == []


# ---------------------------------------------------------------------------
# SimpleRetentionPolicy
# ---------------------------------------------------------------------------

class TestSimpleRetentionPolicy:
    def test_keeps_last_n(self):
        files = make_backup_files_range(NOW, count=20, step=timedelta(hours=1))
        policy = SimpleRetentionPolicy(keep_last=5)
        keep = policy.select_files_to_keep(files)
        assert len(keep) == 5

    def test_keeps_newest(self):
        files = make_backup_files_range(NOW, count=10, step=timedelta(hours=1))
        policy = SimpleRetentionPolicy(keep_last=3)
        keep = policy.select_files_to_keep(files)
        newest = sorted(files, reverse=True)[:3]
        assert keep == paths(newest)

    def test_fewer_files_than_keep_last(self):
        files = make_backup_files_range(NOW, count=3, step=timedelta(hours=1))
        policy = SimpleRetentionPolicy(keep_last=10)
        assert len(policy.select_files_to_keep(files)) == 3

    def test_empty_input(self):
        assert SimpleRetentionPolicy().select_files_to_keep([]) == set()

    def test_single_file(self):
        files = [make_backup_file(NOW)]
        assert SimpleRetentionPolicy(keep_last=1).select_files_to_keep(files) == paths(files)

    def test_keep_last_zero_raises(self):
        with pytest.raises(ValueError):
            SimpleRetentionPolicy(keep_last=0)

    def test_delete_count_correct(self):
        files = make_backup_files_range(NOW, count=10, step=timedelta(hours=1))
        policy = SimpleRetentionPolicy(keep_last=3)
        to_delete = policy.select_files_to_delete(files)
        assert len(to_delete) == 7


# ---------------------------------------------------------------------------
# TimeBasedRetentionPolicy
# ---------------------------------------------------------------------------

class TestTimeBasedRetentionPolicy:
    def test_deletes_old_files(self):
        recent = make_backup_files_range(NOW, count=5, step=timedelta(days=1))
        old = [make_backup_file(NOW - timedelta(days=60))]
        policy = TimeBasedRetentionPolicy(max_age_days=30, minimum_keep=0)
        keep = policy.select_files_to_keep(recent + old)
        assert make_backup_file(NOW - timedelta(days=60)).path not in keep

    def test_keeps_recent_files(self):
        files = make_backup_files_range(NOW, count=5, step=timedelta(days=1))
        policy = TimeBasedRetentionPolicy(max_age_days=30, minimum_keep=0)
        keep = policy.select_files_to_keep(files)
        assert paths(files) == keep

    def test_minimum_keep_prevents_empty(self):
        # All files are ancient — but minimum_keep=1 saves the newest
        files = [make_backup_file(NOW - timedelta(days=365))]
        policy = TimeBasedRetentionPolicy(max_age_days=30, minimum_keep=1)
        keep = policy.select_files_to_keep(files)
        assert len(keep) == 1

    def test_minimum_keep_zero_allows_full_deletion(self):
        files = [make_backup_file(NOW - timedelta(days=365))]
        policy = TimeBasedRetentionPolicy(max_age_days=30, minimum_keep=0)
        keep = policy.select_files_to_keep(files)
        assert len(keep) == 0

    def test_empty_input(self):
        assert TimeBasedRetentionPolicy().select_files_to_keep([]) == set()

    def test_invalid_max_age_raises(self):
        with pytest.raises(ValueError):
            TimeBasedRetentionPolicy(max_age_days=0)

    def test_invalid_minimum_keep_raises(self):
        with pytest.raises(ValueError):
            TimeBasedRetentionPolicy(minimum_keep=-1)


# ---------------------------------------------------------------------------
# DailyRetentionPolicy
# ---------------------------------------------------------------------------

class TestDailyRetentionPolicy:
    def test_keeps_one_per_day(self):
        # 3 backups per day for 5 days = 15 total, should keep 5
        files = []
        for day in range(5):
            for hour in range(3):
                files.append(make_backup_file(NOW - timedelta(days=day, hours=hour)))
        policy = DailyRetentionPolicy(keep_days=5, minimum_keep=0)
        keep = policy.select_files_to_keep(files)
        assert len(keep) == 5

    def test_keeps_newest_of_each_day(self):
        morning = make_backup_file(NOW.replace(hour=6))
        evening = make_backup_file(NOW.replace(hour=20))
        policy = DailyRetentionPolicy(keep_days=1, minimum_keep=0)
        keep = policy.select_files_to_keep([morning, evening])
        assert evening.path in keep
        assert morning.path not in keep

    def test_discards_beyond_keep_days(self):
        files = make_backup_files_range(NOW, count=30, step=timedelta(days=1))
        policy = DailyRetentionPolicy(keep_days=7, minimum_keep=0)
        keep = policy.select_files_to_keep(files)
        assert len(keep) <= 7

    def test_minimum_keep_safety_floor(self):
        files = [make_backup_file(NOW - timedelta(days=100))]
        policy = DailyRetentionPolicy(keep_days=7, minimum_keep=1)
        keep = policy.select_files_to_keep(files)
        assert len(keep) == 1

    def test_empty_input(self):
        assert DailyRetentionPolicy().select_files_to_keep([]) == set()

    def test_invalid_keep_days_raises(self):
        with pytest.raises(ValueError):
            DailyRetentionPolicy(keep_days=0)


# ---------------------------------------------------------------------------
# GFSRetentionPolicy
# ---------------------------------------------------------------------------

class TestGFSRetentionPolicy:
    def test_keeps_recent_hourly(self):
        files = make_backup_files_range(NOW, count=48, step=timedelta(hours=1))
        policy = GFSRetentionPolicy(hourly=24, daily=0, weekly=0, monthly=0)
        keep = policy.select_files_to_keep(files)
        newest_24 = sorted(files, reverse=True)[:24]
        for f in newest_24:
            assert f.path in keep

    def test_keeps_one_per_day(self):
        # One backup every 6 hours for 14 days
        files = make_backup_files_range(NOW, count=14 * 4, step=timedelta(hours=6))
        policy = GFSRetentionPolicy(hourly=0, daily=7, weekly=0, monthly=0)
        keep = policy.select_files_to_keep(files)
        # Should have at most 7 daily representatives
        # (could be fewer if days overlap with boundary)
        assert len(keep) <= 7

    def test_keeps_one_per_week(self):
        # 8 weeks of daily backups → weekly tier should produce ~4 representatives
        # Use >= 4 because partial current week can add one extra
        files = make_backup_files_range(NOW, count=8 * 7, step=timedelta(days=1))
        policy = GFSRetentionPolicy(hourly=0, daily=0, weekly=4, monthly=0)
        keep = policy.select_files_to_keep(files)
        assert 1 <= len(keep) <= 5  # 4 full weeks + possible partial boundary week

    def test_keeps_one_per_month(self):
        # 14 months of daily backups → monthly tier keeps ~12
        # Allow +1 for partial current month boundary
        files = make_backup_files_range(NOW, count=14 * 30, step=timedelta(days=1))
        policy = GFSRetentionPolicy(hourly=0, daily=0, weekly=0, monthly=12)
        keep = policy.select_files_to_keep(files)
        assert 1 <= len(keep) <= 13  # 12 full months + possible partial month boundary

    def test_combined_gfs_no_double_deletion(self):
        """A file qualifying in multiple tiers must still be kept."""
        files = make_backup_files_range(NOW, count=200, step=timedelta(hours=6))
        policy = GFSRetentionPolicy(hourly=24, daily=7, weekly=4, monthly=12)
        keep = policy.select_files_to_keep(files)
        to_delete = policy.select_files_to_delete(files)
        # Keep ∪ delete == all files, no overlap
        assert len(keep) + len(to_delete) == len(files)
        assert keep.isdisjoint(paths(to_delete))

    def test_empty_input(self):
        assert GFSRetentionPolicy().select_files_to_keep([]) == set()

    def test_single_file_always_kept(self):
        files = [make_backup_file(NOW)]
        policy = GFSRetentionPolicy(hourly=1, daily=1, weekly=1, monthly=1)
        assert files[0].path in policy.select_files_to_keep(files)