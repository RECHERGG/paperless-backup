"""
Backup engine entrypoint.

Responsible for:
- generationg filenames
- building remote paths
- orchestrating the backup execution
"""

import logging
from pathlib import PurePosixPath
from datetime import datetime

from app.backup.runner import run_backup
from app.config.typed import AppConfig

logger = logging.getLogger(__name__)


def build_backup_dir(base: str, ts: datetime) -> str:
    """
    Build the remote directory path for a backup archive.
 
    Structure: <base>/backups/YYYY/MM/DD
 
    Args:
        base: Configured remote root (e.g. "paperless").
        ts:   Timestamp of the backup.
 
    Returns:
        e.g. "paperless/backups/2026/05/07"
    """
    root = str(PurePosixPath(base)).rstrip("/")
    return f"{root}/backups/{ts.strftime('%Y/%m/%d')}"

def build_metadata_dir(base: str, ts: datetime) -> str:
    """
    Build the remote directory path for metadata files (e.g. .sha256 sidecars).
 
    Structure: <base>/metadata/YYYY/MM/DD
 
    Keeping metadata in a separate tree makes manual browsing and
    restore scripts cleaner — no sidecar files mixed in with archives.
 
    Args:
        base: Configured remote root (e.g. "paperless").
        ts:   Timestamp of the backup.
 
    Returns:
        e.g. "paperless/metadata/2026/05/07"
    """
    root = str(PurePosixPath(base)).rstrip("/")
    return f"{root}/metadata/{ts.strftime('%Y/%m/%d')}"

def generate_filename(format_str: str, ts: datetime) -> str:
    """
    Generate a filename from a timestamp format string.
 
    Args:
        format_str: Template with {timestamp} placeholder
                    (e.g. "{timestamp}.tar.gz").
        ts:         Timestamp to embed.
 
    Returns:
        e.g. "2026-05-07_12-00-00.tar.gz"
    """
    return format_str.format(timestamp=ts.strftime("%Y-%m-%d_%H-%M-%S"))

def run(config: AppConfig) -> None:
    """
    Execute the backup process using the provided configuration.

    Args:
        config (dict): Application configuration.
    """
    logger.info("Starting backup process...")

    now = datetime.now()
    base = config.storage_sftp.remote_path
    filename = generate_filename(config.backup.filename_template, now)

    backup_dir = build_backup_dir(base, now)
    metadata_dir = build_metadata_dir(base, now)

    remote_file = str(PurePosixPath(f"{backup_dir}/{filename}"))
    remote_sidecar = str(PurePosixPath(f"{metadata_dir}/{filename}.sha256"))
    latest_path = str(PurePosixPath(f"{base}/latest.tar.gz"))

    run_backup(
        config=config,
        filename=filename,
        remote_file=remote_file,
        remote_sidecar=remote_sidecar,
        latest_path=latest_path,
    )

    logger.info("Backup process finished.")