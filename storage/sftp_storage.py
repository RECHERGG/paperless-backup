"""
High-level storage abstraction for SFTP backups.

Responsible ONLY for:
- Orchestrating SSH + SFTP clients
- Defining backup upload flow
"""

import logging
from pathlib import Path

from storage.base import Storage
from storage.ssh_client import SSHClient
from storage.sftp_client import SFTPClient

logger = logging.getLogger(__name__)


class SFTPStorage(Storage):
    """
    SFTP storage backend supporting:
    - SSH key authentication (preferred)
    - password authentication (fallback)
    """

    def __init__(self, config: dict):
        """
        Args:
            config: storage configuration dictionary
        """
        self.host = config["host"]
        self.port = int(config.get("port"))
        self.username = config["username"]

        self.password = config.get("password")
        self.key = config.get("key")

        self.remote_path = config.get("remote_path").strip("/")

        self.ssh = SSHClient(
            self.host,
            self.port,
            self.username,
            key=self.key,
            password=self.password,
        )

        self.sftp = None

    def _connect(self):
        transport = self.ssh.connect()
        self.sftp = SFTPClient(transport)

    def upload(self, local_path: str, remote_filename: str):
        """
        Upload backup archive to remote storage.

        Args:
            local_path: path to local file
            remote_filename: filename on remote storage
        """
        try:
            self._connect()

            remote_dir = self.remote_path
            self.sftp.mkdir_p(remote_dir)

            remote_full_path = f"{remote_dir}/{Path(remote_filename).name}"

            self.sftp.upload_file(local_path, remote_full_path)
            logger.info("Upload successful: %s", remote_full_path)

        finally:
            if self.sftp:
                self.sftp.close()
            self.ssh.close()