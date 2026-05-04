"""
Utility helpers for system operations.
"""

import logging
import subprocess
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


def run_command(cmd: list[str]) -> subprocess.CompletedProcess:
    """
    Execute a system command with logging and error handling.

    Args:
        cmd (list[str]): Command and arguments.
    
    Returns:
        subprocess.CompletedProcess: Result object.
    
    Raises:
        subprocess.CalledProcessError: If command fails.
    """
    logger.info("Running command: %s", " ".join(cmd))

    result = subprocess.run(
        cmd, 
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.error("Command failed with exit code %s", result.returncode)
        logger.error("stderr: %s", result.stderr.strip())

        raise subprocess.CalledProcessError(
            result.returncode, 
            cmd, 
            output=result.stdout, 
            stderr=result.stderr
        )

    if result.stdout:
        logger.debug("stdout: %s", result.stdout.strip())

    return result

def cleanup_workspace(workdir: str):
    path = Path(workdir)

    try:
        if path.exists():
            shutil.rmtree(path)
            logger.info("Deleted workspace directory: %s", path)
        else:
            logger.warning("Workspace not found: %s", path)

    except Exception:
        logger.exception("Failed to delete workspace: %s", path)
