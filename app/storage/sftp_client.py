"""
Low-level SFTP operations.

Responsible ONLY for:
- File upload/download
- Remote directory management
"""

import logging
from pathlib import Path
import paramiko

logger = logging.getLogger(__name__)


class SFTPClient:
    def __init__(self, transport):
        """
        Args:
            transport: active SSH transport
        """
        self.sftp = paramiko.SFTPClient.from_transport(transport)

    def mkdir_p(self, remote_path: str):
        """Create remote directory recursively if missing."""
        remote_path = remote_path.strip("/")
        parts = remote_path.split("/")

        current = ""

        for part in parts:
            current = f"{current}/{part}".lstrip("/")

            try:
                self.sftp.stat(current)
            except FileNotFoundError:
                logger.debug("Creating remote dir: %s", current)
                self.sftp.mkdir(current)

    def upload_file(self, local_path: str, remote_path: str):
        """Upload a file to remote path."""
        logger.info("Uploading '%s' -> '%s'", local_path, remote_path)
        self.sftp.put(local_path, remote_path)
    
    def close(self):
        """Close SFTP session."""
        self.sftp.close()
        logger.info("SFTP session closed")