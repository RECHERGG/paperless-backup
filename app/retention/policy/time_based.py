"""
Time-based retention policy.

Deletes backups older than a configurable maximum age.
Simple to reason about: "I want everything from the last 30 days."

Optionally enforces a minimum number of backups to always retain,
regardless of age - so you are never left with zero backups.
"""

import logging
from datetime import datetime, timedelta

from app.retention.base import BackupFile, RetentionPolicy

logger = logging.getLogger(__name__)


class TimeBasedRetentionPolicy(RetentionPolicy):
    """
    Retains all backups younger than `max_age_days`.

    Attributes:
        max_age_days: Delete backups older than this many days.
        minimum_keep: Always keep at least this many recent backups,
                      even if they are older than max_age_days.
                      Prevents accidental full deletion during long outages.
                      Defaults to 1.
    """

    def __init__(self, max_age_days: int = 30, minimum_keep: int = 1):
        if max_age_days < 1:
            raise ValueError("max_age_days must be at least 1")
        if minimum_keep < 0:
            raise ValueError("minimum_keep must be >= 0")

        self.max_age_days = max_age_days
        self.minimum_keep = minimum_keep

    def select_files_to_keep(self, files: list[BackupFile]) -> set[str]:
        if not files:
            return set()

        cutoff = datetime.now() - timedelta(days=self.max_age_days)
        sorted_files = sorted(files, reverse=True)

        keep: set[str] = set()

        for f in sorted_files:
            if f.timestamp >= cutoff:
                keep.add(f.path)

        # Safety net: always retain at least minimum_keep recent backups
        for f in sorted_files[: self.minimum_keep]:
            keep.add(f.path)

        logger.debug(
            "[TimeBased] keeping %d of %d backups (cutoff: %s)",
            len(keep),
            len(files),
            cutoff.strftime("%Y-%m-%d"),
        )
        return keep
