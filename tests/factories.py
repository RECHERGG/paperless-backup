"""
Test data factories.

Central place to create BackupFile objects for tests.
Keeps test code clean — no repeated datetime construction everywhere.
"""

from datetime import datetime, timedelta
from app.retention.base import BackupFile


def make_backup_file(ts: datetime, path: str | None = None) -> BackupFile:
    """Create a single BackupFile at a given timestamp."""
    if path is None:
        path = f"paperless-backups/{ts.strftime('%Y/%m')}/{ts.strftime('%Y-%m-%d_%H-%M-%S')}.tar.gz"
    return BackupFile(path=path, timestamp=ts)


def make_backup_files_range(
    base: datetime,
    count: int,
    step: timedelta,
) -> list[BackupFile]:
    """
    Create a list of BackupFiles at regular intervals going BACK in time.

    Example:
        make_backup_files_range(now, count=10, step=timedelta(hours=1))
        → 10 files, newest = now, oldest = now - 9h
    """
    return [make_backup_file(base - step * i) for i in range(count)]
