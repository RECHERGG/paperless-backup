"""
Low-level SFTP operations.

Responsible ONLY for:
- File upload/download
- Remote directory management
"""

import logging

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

    def list_files(self, remote_dir: str) -> list[str]:
        """
        Recursively list all files under a remote directory.

        Args:
            remote_dir: Remote base directory to scan.
        
        Returns:
            List of full remote file path (files only, no directories).
        """
        results: list[str] = []
        self._walk(remote_dir.rstrip("/"), results)

        return results
    
    def _walk(self, path: str, accumulator: list[str]):
        """Recursive directory walker."""
        try:
            entries = self.sftp.listdir_attr(path)
        except FileNotFoundError:
            logger.warning("Remote directory not found: %s", path)
            return
        
        for entry in entries:
            full_path = f"{path}/{entry.filename}"
            if self._is_dir(entry):
                self._walk(full_path, accumulator)
            else:
                accumulator.append(full_path)
        
    @staticmethod
    def _is_dir(attr) -> bool:
        """Check if an SFTPAttributes entry is a directory."""
        import stat
        return stat.S_ISDIR(attr.st_mode) if attr.st_mode else False
    
    def delete_file(self, remote_path: str):
        """
        Delete a single remote file.

        Args:
            remote_path: Full path to the remote file.
        """
        logger.info("Deleting remote file: %s", remote_path)
        self.sftp.remove(remote_path)
    
    def close(self):
        """Close SFTP session."""
        self.sftp.close()
        logger.info("SFTP session closed")