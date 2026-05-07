"""
High-level storage abstraction for SFTP backups.

Responsible ONLY for:
- Orchestrating SSH + SFTP clients
- Defining backup upload flow
- Listing and deleting remote backup files
"""

import logging

from app.config.typed import SFTPConfig
from app.storage.base import Storage
from app.storage.ssh_client import SSHClient
from app.storage.sftp.sftp_client import SFTPClient

logger = logging.getLogger(__name__)

# Files that are never subject retention cleanup.
_PROTECTED_FILENAMES = {"latest.tar.gz"}


class SFTPStorage(Storage):
    """
    SFTP storage backend supporting:
    - SSH key authentication (preferred)
    - password authentication (fallback)
    """

    def __init__(self, config: SFTPConfig):
        """
        Args:
            config: storage configuration dictionary
        """
        self.host = config.host
        self.port = int(config.port)
        self.username = config.username

        self.password = config.password
        self.key = config.key

        self.remote_path = config.remote_path.strip("/")

        self.ssh = SSHClient(
            self.host,
            self.port,
            self.username,
            key=self.key,
            password=self.password,
        )

        self.sftp: SFTPClient | None = None

    def _connect(self):
        transport = self.ssh.connect()
        self.sftp = SFTPClient(transport)

    def _disconnect(self):
        if self.sftp:
            self.sftp.close()
            self.sftp = None
        self.ssh.close()

    def upload(self, local_path: str, remote_path: str):
        """
        Upload backup archive to remote storage.

        Args:
            local_path: path to local file
            remote_path: Full remote path (including directories + filename)
        """
        try:
            self._connect()

            remote_path = remote_path.replace("\\", "/")
            remote_dir = remote_path.rsplit("/", 1)[0]

            if remote_dir:
                self.sftp.mkdir_p(remote_dir)
                
            self.sftp.upload_file(local_path, remote_path)
            logger.info("Upload successful: %s", remote_path)

        finally:
            self._disconnect()
        
    def list_backups(self) -> list[str]:
        """
        List all backup files under the configured remote path,
        excluding protected files (e.g. latest.tar.gz).

        Returns:
            List of full remote file paths eligible for retention.
        """

        try:
            self._connect
            all_files = self.sftp.list_files(self.remote_path)
        finally:
            self._disconnect()

        eligible = [
            f for f in all_files
            if f.rsplit("/", 1)[-1] not in _PROTECTED_FILENAMES
        ]

        logger.debug(
            "Found %d remote backup(s) (%d protected skipped)",
            len(eligible),
            len(all_files) - len(eligible),
        )

        return eligible
    
    def delete(self, remote_path: str):
        """
        Delete a single remote backup file.

        Args:
            remote_path: Full remote path to the file.
        """
        filename = remote_path.rsplit("/", 1)[-1]
        if filename in _PROTECTED_FILENAMES:
            logger.warning("Refusing to delete protected file: %s", remote_path)
            return
        
        try:
            self._connect()
            self.sftp.delete_file(remote_path)
        finally:
            self._disconnect()