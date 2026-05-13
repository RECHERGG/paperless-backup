"""
Tests for all retention policies.

freeze_time() pins datetime.now() to a fixed point so tests are
deterministic without threading reference_time through the policies themselves.
The frozen timestamp is declared once per test — no hidden magic variables.
"""

import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time

from app.retention.policy.gfs import GFSRetentionPolicy
from app.retention.policy.simple import SimpleRetentionPolicy
from app.retention.policy.time_based import TimeBasedRetentionPolicy
from app.retention.policy.daily import DailyRetentionPolicy
from app.retention.policy.none import NoRetentionPolicy

from factories import make_backup_file, make_backup_files_range

FROZEN = "2026-05-07 12:00:00"


def paths(files) -> set[str]:
    return {f.path for f in files}


# ---------------------------------------------------------------------------
# NoRetentionPolicy — no time dependency, no freeze needed
# ---------------------------------------------------------------------------

class TestNoRetentionPolicy:
    def test_keeps_everything(self):
        files = make_backup_files_range(datetime(2026, 5, 7, 12), count=100, step=timedelta(hours=1))
        assert NoRetentionPolicy().select_files_to_keep(files) == paths(files)

    def test_empty_input(self):
        assert NoRetentionPolicy().select_files_to_keep([]) == set()

    def test_deletes_nothing(self):
        files = make_backup_files_range(datetime(2026, 5, 7, 12), count=5, step=timedelta(hours=1))
        assert NoRetentionPolicy().select_files_to_delete(files) == []


# ---------------------------------------------------------------------------
# SimpleRetentionPolicy — no time dependency, no freeze needed
# ---------------------------------------------------------------------------

class TestSimpleRetentionPolicy:
    def test_keeps_last_n(self):
        files = make_backup_files_range(datetime(2026, 5, 7, 12), count=20, step=timedelta(hours=1))
        assert len(SimpleRetentionPolicy(keep_last=5).select_files_to_keep(files)) == 5

    def test_keeps_newest(self):
        files = make_backup_files_range(datetime(2026, 5, 7, 12), count=10, step=timedelta(hours=1))
        keep = SimpleRetentionPolicy(keep_last=3).select_files_to_keep(files)
        assert keep == paths(sorted(files, reverse=True)[:3])

    def test_fewer_files_than_keep_last(self):
        files = make_backup_files_range(datetime(2026, 5, 7, 12), count=3, step=timedelta(hours=1))
        assert len(SimpleRetentionPolicy(keep_last=10).select_files_to_keep(files)) == 3

    def test_empty_input(self):
        assert SimpleRetentionPolicy().select_files_to_keep([]) == set()

    def test_single_file(self):
        files = [make_backup_file(datetime(2026, 5, 7, 12))]
        assert SimpleRetentionPolicy(keep_last=1).select_files_to_keep(files) == paths(files)

    def test_keep_last_zero_raises(self):
        with pytest.raises(ValueError):
            SimpleRetentionPolicy(keep_last=0)

    def test_delete_count_correct(self):
        files = make_backup_files_range(datetime(2026, 5, 7, 12), count=10, step=timedelta(hours=1))
        assert len(SimpleRetentionPolicy(keep_last=3).select_files_to_delete(files)) == 7


# ---------------------------------------------------------------------------
# TimeBasedRetentionPolicy
# ---------------------------------------------------------------------------

@freeze_time(FROZEN)
class TestTimeBasedRetentionPolicy:
    def test_deletes_old_files(self):
        now = datetime(2026, 5, 7, 12)
        recent = make_backup_files_range(now, count=5, step=timedelta(days=1))
        old = make_backup_file(now - timedelta(days=60))
        policy = TimeBasedRetentionPolicy(max_age_days=30, minimum_keep=0)
        assert old.path not in policy.select_files_to_keep(recent + [old])

    def test_keeps_recent_files(self):
        now = datetime(2026, 5, 7, 12)
        files = make_backup_files_range(now, count=5, step=timedelta(days=1))
        policy = TimeBasedRetentionPolicy(max_age_days=30, minimum_keep=0)
        assert policy.select_files_to_keep(files) == paths(files)

    def test_minimum_keep_prevents_empty(self):
        old = make_backup_file(datetime(2026, 5, 7, 12) - timedelta(days=365))
        policy = TimeBasedRetentionPolicy(max_age_days=30, minimum_keep=1)
        assert len(policy.select_files_to_keep([old])) == 1

    def test_minimum_keep_zero_allows_full_deletion(self):
        old = make_backup_file(datetime(2026, 5, 7, 12) - timedelta(days=365))
        policy = TimeBasedRetentionPolicy(max_age_days=30, minimum_keep=0)
        assert policy.select_files_to_keep([old]) == set()

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

@freeze_time(FROZEN)
class TestDailyRetentionPolicy:
    def test_keeps_one_per_day(self):
        now = datetime(2026, 5, 7, 12)
        files = [
            make_backup_file(now - timedelta(days=day, hours=hour))
            for day in range(5)
            for hour in range(3)
        ]
        policy = DailyRetentionPolicy(keep_days=5, minimum_keep=0)
        assert len(policy.select_files_to_keep(files)) == 5

    def test_keeps_newest_of_each_day(self):
        morning = make_backup_file(datetime(2026, 5, 7, 6))
        evening = make_backup_file(datetime(2026, 5, 7, 20))
        policy = DailyRetentionPolicy(keep_days=1, minimum_keep=0)
        keep = policy.select_files_to_keep([morning, evening])
        assert evening.path in keep
        assert morning.path not in keep

    def test_discards_beyond_keep_days(self):
        now = datetime(2026, 5, 7, 12)
        files = make_backup_files_range(now, count=30, step=timedelta(days=1))
        policy = DailyRetentionPolicy(keep_days=7, minimum_keep=0)
        assert len(policy.select_files_to_keep(files)) <= 8  # 7 days + current day boundary

    def test_minimum_keep_safety_floor(self):
        old = make_backup_file(datetime(2026, 5, 7, 12) - timedelta(days=100))
        policy = DailyRetentionPolicy(keep_days=7, minimum_keep=1)
        assert len(policy.select_files_to_keep([old])) == 1

    def test_empty_input(self):
        assert DailyRetentionPolicy().select_files_to_keep([]) == set()

    def test_invalid_keep_days_raises(self):
        with pytest.raises(ValueError):
            DailyRetentionPolicy(keep_days=0)


# ---------------------------------------------------------------------------
# GFSRetentionPolicy
# ---------------------------------------------------------------------------

@freeze_time(FROZEN)
class TestGFSRetentionPolicy:
    def test_keeps_recent_hourly(self):
        now = datetime(2026, 5, 7, 12)
        files = make_backup_files_range(now, count=48, step=timedelta(hours=1))
        policy = GFSRetentionPolicy(hourly=24, daily=0, weekly=0, monthly=0)
        keep = policy.select_files_to_keep(files)
        for f in sorted(files, reverse=True)[:24]:
            assert f.path in keep

    def test_keeps_one_per_day(self):
        now = datetime(2026, 5, 7, 12)
        files = make_backup_files_range(now, count=14 * 4, step=timedelta(hours=6))
        policy = GFSRetentionPolicy(hourly=0, daily=7, weekly=0, monthly=0)
        assert len(policy.select_files_to_keep(files)) <= 8

    def test_keeps_one_per_week(self):
        now = datetime(2026, 5, 7, 12)
        files = make_backup_files_range(now, count=8 * 7, step=timedelta(days=1))
        policy = GFSRetentionPolicy(hourly=0, daily=0, weekly=4, monthly=0)
        assert 1 <= len(policy.select_files_to_keep(files)) <= 5

    def test_keeps_one_per_month(self):
        now = datetime(2026, 5, 7, 12)
        files = make_backup_files_range(now, count=14 * 30, step=timedelta(days=1))
        policy = GFSRetentionPolicy(hourly=0, daily=0, weekly=0, monthly=12)
        assert 1 <= len(policy.select_files_to_keep(files)) <= 13

    def test_combined_no_double_deletion(self):
        now = datetime(2026, 5, 7, 12)
        files = make_backup_files_range(now, count=200, step=timedelta(hours=6))
        policy = GFSRetentionPolicy(hourly=24, daily=7, weekly=4, monthly=12)
        keep = policy.select_files_to_keep(files)
        to_delete = policy.select_files_to_delete(files)
        assert len(keep) + len(to_delete) == len(files)
        assert keep.isdisjoint(paths(to_delete))

    def test_empty_input(self):
        assert GFSRetentionPolicy().select_files_to_keep([]) == set()

    def test_single_file_always_kept(self):
        files = [make_backup_file(datetime(2026, 5, 7, 12))]
        policy = GFSRetentionPolicy(hourly=1, daily=1, weekly=1, monthly=1)
        assert files[0].path in policy.select_files_to_keep(files)