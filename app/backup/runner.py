"""
High-level backup flow orchestration.
"""

import logging
from pathlib import Path
import tempfile

from app.backup.exporter import export_data
from app.backup.archive import create_archive
from app.backup.utils import cleanup_workspace
from storage.factory import get_storage

logger = logging.getLogger(__name__)


def run_backup(config: dict, filename: str) -> None:
    """
    Execute the full backup pipeline:
    export -> archive -> upload.

    Args:
        config (dict): Full application configuration.
        filename (str): Target filename for archive.
    """
    container = config["paperless"]["container_name"]
    delete = config["backup"]["delete_local_after_upload"]
    keep_failed = config["backup"]["keep_failed_backups"]

    work_dir = Path(tempfile.mkdtemp())
    export_path = work_dir / "export"
    archive_base = work_dir / filename.replace(".tar.gz", "")

    logger.debug("Working directory: %s", work_dir)

    success = False
    archive_file: Path | None = None

    try:
        logger.info("Step 1/3: Exporting data...")
        export_data(container, export_path)

        logger.info("Step 2/3: Creating archive...")
        archive_file = Path(create_archive(export_path, str(archive_base)))

        logger.info("Step 3/3: Uploading archive...")
        storage = get_storage(config)
        storage.upload(str(archive_file), filename)

        success = True

    except Exception:
        logger.exception("Backup process failed.")
        raise

    finally:
        if success and delete:
            cleanup_workspace(str(work_dir))
        else:
            logger.warning("Keeping workspace: %s", work_dir)