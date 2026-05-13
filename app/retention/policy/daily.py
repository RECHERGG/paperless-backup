"""
Daily-only retention policy.

Keeps exaclty one backup per calendar day (the most recent one),
for the last N days. Simpler than GFS when sub-daily granularity
is not needed.
"""

import logging
from datetime import datetime, timedelta

from app.retention.base import BackupFile, RetentionPolicy

logger = logging.getLogger(__name__)


class DailyRetentionPolicy(RetentionPolicy):
    """
    Retains one backup per day for the last `keep_days` days.

    Attributes:
        keep_days: Number of daily snapshots to retain.
        minimum_keep: Safety floor - always retain at least this many
                      recent backups regardless of age.
    """

    def __init__(self, keep_days: int = 7, minimum_keep: int = 1):
        if keep_days < 1:
            raise ValueError("keep_days must be at least 1")

        self.keep_days = keep_days
        self.minimum_keep = minimum_keep

    def select_files_to_keep(self, files: list[BackupFile]) -> set[str]:
        if not files:
            return set()

        cutoff = datetime.now() - timedelta(days=self.keep_days)
        sorted_files = sorted(files, reverse=True)

        seen_days: dict[tuple, str] = {}

        for f in sorted_files:
            if f.timestamp < cutoff:
                break
            day_key = (f.timestamp.year, f.timestamp.month, f.timestamp.day)
            if day_key not in seen_days:
                seen_days[day_key] = f.path

        keep = set(seen_days.values())

        for f in sorted_files[: self.minimum_keep]:
            keep.add(f.path)

        logger.debug("[Daily] keeping %d of %d backups", len(keep), len(files))
        return keep
