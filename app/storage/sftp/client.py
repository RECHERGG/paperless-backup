"""
SFTP implementation of StorageClient.

Responsibilities:
    - Implement every StorageClient primitive via paramiko
    - Nothing else

What does NOT belong here:
    - Checksums, atomic logic, retention, business rules of any kind
    - SSH connection management (that is SSHClient's job)
"""

import io
import logging
import stat
from pathlib import Path

import paramiko

logger = logging.getLogger(__name__)


class SFTPClient:
    """
    StorageClient implementation over an active paramiko SSH transport.

    Each method is a direct, thin wrapper around the paramiko SFTP API.
    No retry logic, no business rules — callers handle that.
    """

    def __init__(self, sftp: paramiko.SFTPClient) -> None:
        self._sftp = sftp

    def upload_file(self, local_path: Path, remote_path: str) -> None:
        """Upload a local file to a remote path."""
        logger.debug("PUT %s → %s", local_path, remote_path)
        self._sftp.put(str(local_path), remote_path)

    def download_bytes(self, remote_path: str) -> bytes:
        """Download a remote file into memory and return raw bytes."""
        logger.debug("GET %s", remote_path)
        buf = io.BytesIO()
        self._sftp.getfo(remote_path, buf)
        return buf.getvalue()

    def rename(self, src: str, dst: str) -> None:
        """Rename (move) a remote file."""
        logger.debug("RENAME %s → %s", src, dst)
        self._sftp.rename(src, dst)

    def delete(self, remote_path: str) -> None:
        """Delete a remote file."""
        logger.debug("DELETE %s", remote_path)
        self._sftp.remove(remote_path)

    def list_files(self, remote_dir: str) -> list[str]:
        """Recursively list all files under a remote directory."""
        results: list[str] = []
        self._walk(remote_dir.rstrip("/"), results)
        return results

    def mkdir(self, remote_path: str) -> None:
        """Create a remote directory, creating any missing parents."""
        remote_path = remote_path.strip("/")
        current = ""

        for part in remote_path.split("/"):
            current = f"{current}/{part}".lstrip("/")
            try:
                self._sftp.stat(current)
            except FileNotFoundError:
                logger.debug("MKDIR %s", current)
                self._sftp.mkdir(current)

    def close(self) -> None:
        self._sftp.close()

    def _walk(self, path: str, accumulator: list[str]) -> None:
        try:
            entries = self._sftp.listdir_attr(path)
        except FileNotFoundError:
            logger.warning("Remote directory not found: %s", path)
            return

        for entry in entries:
            full_path = f"{path}/{entry.filename}"
            if stat.S_ISDIR(entry.st_mode or 0):
                self._walk(full_path, accumulator)
            else:
                accumulator.append(full_path)
