"""
Parses timestamps from backup filenames.

Supports the default template `{timestamp}.tar.gz` where timestamp
follows the format `YYYY-MM-DD_HH-MM-SS`.

Custom patterns can be registered for non-standard filename formats.
"""

import re
import logging
from datetime import datetime
from pathlib import PurePosixPath

logger = logging.getLogger(__name__)

# Matches: 2026-05-07_14-30-00
_DEFAULT_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})")
_DEFAULT_FORMAT = "%Y-%m-%d_%H-%M-%S"

def parse_timestamp_from_filename(filename: str) -> datetime | None:
    """
    Extract and parse a timestamp from a backup filename.

    Tries the default pattern first. Returns None if no match found
    (caller decides whether to skip or raise).

    Args:
        filename: Bare filename or full remote path.

    Returns:
        Parsed datetime, or None if unparseable.
    """
    name = PurePosixPath(filename).name

    match = _DEFAULT_PATTERN.search(name)
    if not match:
        logger.warning("Could not parse timestamp from filename: %s", filename)
        return None

    try:
        return datetime.strptime(match.group(1), _DEFAULT_FORMAT)
    except ValueError:
        logger.warning("Timestamp fortmat mismatch in filename: %s", filename)
        return None
