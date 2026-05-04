"""
Backup engine entrypoint.

Responsible for preparing runtime parameters and triggering the backup flow.
"""

import logging
from datetime import datetime

from app.backup.runner import run_backup

logger = logging.getLogger(__name__)


def generate_filename(format_str: str) -> str:
    """
    Generate a filename using a timestamp format.

    Args:
        format_str (str): Format string with placeholders (e.g. "{timestamp}.tar.gz")
    
    Returns:
        str: Generated filename.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = format_str.format(timestamp=timestamp)

    logger.debug("Generated backup filename: %s", filename)
    return filename

def run(config: dict):
    """
    Execute the backup process using provided configuration.

    Args:
        config (dict): Application configuration.
    """
    logger.info("Starting backup process...")

    filename = generate_filename(config["backup"]["filename_format"])
    run_backup(config, filename)

    logger.info("Backup process finished.")