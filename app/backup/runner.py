"""
Backup execution pipeline.

Handles:
- export
- archive
- upload
- retention
- cleanup
"""

import logging
from pathlib import Path
import tempfile

from app.backup.exporter import export_data
from app.backup.archive import create_archive
from app.backup.utils import cleanup_workspace
from app.config.typed import AppConfig
from app.retention import get_policy
from app.retention.executor import apply_retention
from app.storage.factory import get_storage

logger = logging.getLogger(__name__)


def run_backup(
    config: AppConfig,
    filename: str,
    remote_file: str,
    remote_sidecar: str,
    latest_path: str,
) -> None:
    """
    Execute the full backup pipeline:
    export → archive → upload → retention.
 
    Args:
        config:          Full application configuration.
        filename:        Target filename for archive.
        remote_file:     Full remote path for the archive.
        remote_sidecar:  Full remote path for the .sha256 sidecar.
        latest_path:     Remote path for the rolling latest.tar.gz.
    """
    container = config.paperless.container_name
    delete = config.backup.delete_local_after_upload
    keep_failed = config.backup.keep_failed_backups

    work_dir = Path(tempfile.mkdtemp())
    export_path = work_dir / "export"
    archive_base = work_dir / filename.replace(".tar.gz", "")

    success = False
    logger.debug("Working directory: %s", work_dir)

    try:
        logger.info("Step 1/4: Exporting data...")
        export_data(container, export_path)

        logger.info("Step 2/4: Creating archive...")
        archive_file = create_archive(export_path, str(archive_base))

        logger.info("Step 3/4: Uploading archive...")
        storage = get_storage(config)

        # Upload main backup
        storage.upload(archive_file, remote_file, remote_sidecar)

        # Upload latest backup
        storage.upload(archive_file, latest_path, sidecar_path=None)

        logger.info("Backup successfully uploaded.")

        logger.info("Step 4/4: Applying retention policy...")
        policy = get_policy(config.retention)
        apply_retention(storage, policy)

        success = True

    except Exception:
        logger.exception("Backup process failed.")
        raise

    finally:
        if success and delete:
            cleanup_workspace(work_dir)
            logger.debug("Workspace cleaned: %s", work_dir)

        elif not success and not keep_failed:
            cleanup_workspace(work_dir)
            logger.debug("Failed workspace cleaned: %s", work_dir)

        else:
            logger.warning("Keeping workspace: %s", work_dir)