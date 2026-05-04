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


def build_remote_dir(base: str, ts: datetime) -> str:
    """
    Build remote directory path (YYYY/MM)

    Example:
        paperless-backups/2026/05
    """
    base = str(PurePosixPath(base))

    return f"{base.rstrip('/')}/{ts.strftime('%Y/%m')}"

def generate_filename(format_str: str, ts: datetime) -> str:
    """
    Generate a filename using a timestamp format.

    Args:
        format_str (str): Format string with placeholders (e.g. "{timestamp}.tar.gz")
    
    Returns:
        str: Generated filename.
    """
    timestamp = ts.strftime("%Y-%m-%d_%H-%M-%S")
    return format_str.format(timestamp=timestamp)

def run(config: AppConfig):
    """
    Execute the backup process using provided configuration.

    Args:
        config (dict): Application configuration.
    """
    logger.info("Starting backup process...")

    now = datetime.now()
    remote_path = config.storage_sftp.remote_path

    remote_dir = build_remote_dir(
        remote_path,
        now,
    )

    filename = generate_filename(
        config.backup.filename_template,
        now,
    )

    remote_file = str(PurePosixPath(f"{remote_dir}/{filename}"))

    run_backup(
        config=config,
        filename=filename,
        remote_file=remote_file,
        latest_path=f"{remote_path}/latest.tar.gz"
    )

    logger.info("Backup process finished.")