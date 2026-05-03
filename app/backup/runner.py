"""
High-level backup flow orchestration.
"""

import logging
from pathlib import Path

from exporter import export_data
from archive import create_archive
from storage.factory import get_storage

logger = logging.getLogger(__name__)

def run_backup(config: dict, filename: str) -> None:
    """
    Run the backup process end-to-end.

    Args:
        config (dict): Full application configuration.
        filename (str): Base name for the backup archive.
    """
    container = config["paperless"]["container_name"]

    work_dir = Path("tmp")
    export_path = work_dir / "export"
    archive_base = work_dir / filename.replace(".tar.gz", "")

    work_dir.mkdir(exist_ok=True)

    logger.info("Exporting data from container...")
    export_data(container, export_path)

    logger.info("Creating archive...")
    archive_file = create_archive(export_path, str(archive_base))

    logger.info("Uploading archive to storage...")
    storage = get_storage(config)
    storage.upload(archive_file, filename)

    logger.info("Backup completed successfully.")