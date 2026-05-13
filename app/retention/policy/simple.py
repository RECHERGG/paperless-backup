"""
Simple retention policy: keep only the last N backups.

Useful for low-traffic setups or when storage is limited
and a simple rolling window is sufficient.
"""

import logging

from app.retention.base import BackupFile, RetentionPolicy

logger = logging.getLogger(__name__)


class SimpleRetentionPolicy(RetentionPolicy):
    """
    Keeps the N most recent backups. Deletes everything else.

    Attributes:
        keep_last: Number of most recent backups to retain.
    """

    def __init__(self, keep_last: int = 10):
        if keep_last < 1:
            raise ValueError("keep_last must be at least 1")
        self.keep_last = keep_last

    def select_files_to_keep(self, files: list[BackupFile]) -> set[str]:
        if not files:
            return set()

        sorted_files = sorted(files, reverse=True)
        keep = {f.path for f in sorted_files[: self.keep_last]}

        logger.debug("[Simple] keeping %d of %d backups", len(keep), len(files))
        return keep
