"""
Handles export from Paperless container.
"""

import subprocess
import shutil
from pathlib import Path

def export_data(container: str, export_path: Path):
    """
    Export data from Paperless container.

    Args:
        container (str): Docker container name
        export_path (Path): Destination path on host
    """
    if export_path.exists():
        shutil.rmtree(export_path)
    
    subprocess.run(
        ["docker", "exec", container, "document_exporter", "/tmp/export"],
        check=True,
    )

    subprocess.run(
        ["docker", "cp", f"{container}:/tmp/export", str(export_path)],
        check=True,
    )    