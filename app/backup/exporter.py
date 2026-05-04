"""
Handles export from Paperless container.
"""

import logging
import shutil
from pathlib import Path

from app.backup.utils import run_command

logger = logging.getLogger(__name__)


def export_data(container: str, export_path: Path):
    """
    Export data from Paperless Docker container.

    Args:
        container (str): Docker container name.
        export_path (Path): Destination path on host.

    Raises:
        RuntimeError: If export fails.
    """
    logger.info("Starting export from container '%s'...", container)

    if export_path.exists():
        logger.debug("Removing existing export directory '%s'", export_path)
        shutil.rmtree(export_path)
    
    run_command([
        "docker", "exec", container, "document_exporter", "/usr/src/paperless/export"
    ])

    run_command([
        "docker", "cp", f"{container}:/usr/src/paperless/export", str(export_path)
    ])

    logger.info("Export completed to '%s'", export_path)