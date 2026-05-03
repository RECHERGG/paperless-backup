"""
Archive creation utilities.
"""

import shutil
from pathlib import Path

def create_archive(source: Path, output_base: str) -> str:
    """
    Create a compressed archive of from export directory.

    Returns:
        str: Path to created archive file.
    """
    archive_path = f"{output_base}.tar.gz"

    shutil.make_archive(
        output_base,
        "gztar",
        root_dir=source.parent,
    )

    return archive_path