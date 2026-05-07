"""
No-op retention policy.

Keeps all backups indefinitely. Useful during testing or when
external tooling manages cleanup separately.

This is intentionally explicit - using it is a consciuous choice,
not a silent default.
"""

import logging

from app.retention.base import BackupFile, RetentionPolicy

logger = logging.getLogger(__name__)


class NoRetentionPolicy(RetentionPolicy):
    """
    Retains every backup. Nothing is ever deleted.
    """

    def select_files_to_keep(self, files: list[BackupFile]) -> set[str]:
        logger.debug("[None] retention disabled - keeping all %d backups", len(files))
        return {f.path for f in files}