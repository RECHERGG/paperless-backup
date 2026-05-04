"""
Archive creation utilities.

This module provides functionality to create compressed archives
from exported Paperless data.
"""

import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


def create_archive(source: Path, output_base: str) -> str:
    """
    Create a compressed tar.gz archive from a source directory.

    Args:
        source (Path): Directory to archive.
        output_base (str): Output file path without esxtension.

    Returns:
        str: Full path to created archive file.
    
    Raises:
        FileNotFoundError: If the source directory does not exist.

    """
    if not source.exists():
        raise FileNotFoundError(f"Source directory '{source}' does not exist")

    logger.info("Create archive from '%s'...", source)

    archive_path = shutil.make_archive(
        output_base,
        "gztar",
        root_dir=source.parent,
        base_dir=source.name,
    )

    logger.info("Archive created at '%s'", archive_path)
    return archive_path