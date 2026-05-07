"""
Tests for app/retention/factory.py

Verifies that get_policy() returns the correct type for each strategy
and that unknown strategies raise cleanly.
"""

import pytest

from app.retention.factory import get_policy
from app.retention.policy.gfs import GFSRetentionPolicy
from app.retention.policy.simple import SimpleRetentionPolicy
from app.retention.policy.time_based import TimeBasedRetentionPolicy
from app.retention.policy.daily import DailyRetentionPolicy
from app.retention.policy.none import NoRetentionPolicy
from app.config.typed import RetentionConfig


def make_retention_config(**overrides) -> RetentionConfig:
    defaults = dict(
        strategy="gfs",
        hourly=24,
        daily=7,
        weekly=4,
        monthly=12,
        keep_last=10,
        max_age_days=30,
        keep_days=7,
        minimum_keep=1,
    )
    defaults.update(overrides)
    return RetentionConfig(**defaults)


class TestGetPolicy:
    def test_gfs_strategy(self):
        config = make_retention_config(strategy="gfs")
        assert isinstance(get_policy(config), GFSRetentionPolicy)

    def test_simple_strategy(self):
        config = make_retention_config(strategy="simple")
        assert isinstance(get_policy(config), SimpleRetentionPolicy)

    def test_time_strategy(self):
        config = make_retention_config(strategy="time")
        assert isinstance(get_policy(config), TimeBasedRetentionPolicy)

    def test_daily_strategy(self):
        config = make_retention_config(strategy="daily")
        assert isinstance(get_policy(config), DailyRetentionPolicy)

    def test_none_strategy(self):
        config = make_retention_config(strategy="none")
        assert isinstance(get_policy(config), NoRetentionPolicy)

    def test_unknown_strategy_raises(self):
        config = make_retention_config(strategy="magic")
        with pytest.raises(ValueError, match="Unknown retention strategy"):
            get_policy(config)

    def test_strategy_case_insensitive(self):
        config = make_retention_config(strategy="GFS")
        assert isinstance(get_policy(config), GFSRetentionPolicy)

    def test_gfs_config_values_passed_through(self):
        config = make_retention_config(strategy="gfs", hourly=5, daily=3, weekly=2, monthly=6)
        policy = get_policy(config)
        assert isinstance(policy, GFSRetentionPolicy)
        assert policy.hourly == 5
        assert policy.daily == 3
        assert policy.weekly == 2
        assert policy.monthly == 6

    def test_simple_keep_last_passed_through(self):
        config = make_retention_config(strategy="simple", keep_last=42)
        policy = get_policy(config)
        assert policy.keep_last == 42

    def test_time_max_age_passed_through(self):
        config = make_retention_config(strategy="time", max_age_days=90, minimum_keep=2)
        policy = get_policy(config)
        assert policy.max_age_days == 90
        assert policy.minimum_keep == 2