"""
Grandfather-Father-Son (GFS) retention policy.

Keeps a tiered set of backups across time horizons:
- Hourly:  the N most recent backups (one per hour slot)
- Daily:   one backup per day for the last N days
- Weekly:  one backup per week for the last N weeks
- Monthly: one backup per month for the last N months

Each tier is evaluated independently. A file is kept if it
qualifies in ANY tier.
"""

import logging
from datetime import datetime, timedelta

from app.retention.base import BackupFile, RetentionPolicy

logger = logging.getLogger(__name__)


def _week_key(dt: datetime) -> tuple[int, int]:
    """ISO year + week number."""
    iso = dt.isocalendar()
    return (iso.year, iso.week)


def _month_key(dt: datetime) -> tuple[int, int]:
    return (dt.year, dt.month)


class GFSRetentionPolicy(RetentionPolicy):
    """
    Grandfather-Father-Son retention strategy.

    Attributes:
        hourly: Number of most-recent backups to retrain (hourly bucket).
        daily: Number of past days past to retain one backup per day.
        weekly: Number of past weeks to retain one backup per week.
        monthly: Number of past months to retain one backup per month.
    """

    def __init__(
        self,
        hourly: int = 24,
        daily: int = 7,
        weekly: int = 4,
        monthly: int = 12
    ):
        self.hourly = hourly
        self.daily = daily
        self.weekly = weekly
        self.monthly = monthly

    def select_files_to_keep(self, files: list[BackupFile])  -> set[str]:
        if not files:
            return set()
        
        keep: set[str] = set()
        now = datetime.now()

        sorted_files = sorted(files, key=lambda f: f.timestamp, reverse=True)

        # Hourly: keep the N most recent backups
        for f in sorted_files[: self.hourly]:
            logger.debug("[GFS] hourly keep: %s", f.path)
            keep.add(f.path)

        seen_days: dict[tuple, str] = {}

        for f in sorted_files:
            day_key = (f.timestamp.year, f.timestamp.month, f.timestamp.day)

            if day_key not in seen_days:
                seen_days[day_key] = f.path
            
        for path in list(seen_days.values())[: self.daily]:
            keep.add(path)
        
        # Weekly: one newest backup per ISO week for the last N weeks
        weekly_cutoff = now - timedelta(weeks=self.weekly)
        seen_weeks: dict[tuple, str] = {}

        for f in sorted_files:
            wk = _week_key(f.timestamp)

            if wk not in seen_weeks:
                seen_weeks[wk] = f.path

        for path in list(seen_weeks.values())[: self.weekly]:
            keep.add(path)

        # Monthly: one newest backup per month for the last N months
        monthly_cutoff = now - timedelta(days=self.monthly * 30)
        seen_months: dict[tuple, str] = {}

        for f in sorted_files:
            mk = _month_key(f.timestamp)

            if mk not in seen_months:
                seen_months[mk] = f.path

        for path in list(seen_months.values())[: self.monthly]:
            keep.add(path)

        return keep