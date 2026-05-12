"""
SFTP implementation of Storage.

Responsibilities:
    - Manage the SSH/SFTP connection lifecycle
    - Implement Storage.upload using atomic_upload + checksum sidecar
    - Implement Storage.list_backups and Storage.delete

The business logic for atomic upload lives in upload.py.
The checksum logic lives in checksum.py.
This class wires them together with a real SFTP connection.
"""

import logging
from pathlib import Path

from app.config.typed import SFTPConfig
from app.storage.base import Storage
from app.storage.checksum import write_sidecar, SIDECAR_EXTENSION
from app.storage.upload import atomic_upload
from app.storage.sftp.client import SFTPClient
from app.storage.sftp.ssh import SSHClient

logger = logging.getLogger(__name__)

_PROTECTED = {"latest.tar.gz"}
_SKIP_EXTENSIONS = {SIDECAR_EXTENSION, ".tmp"}


class SFTPStorage(Storage):
    """
    Storage backend that writes backups to an SFTP server.

    Supports:
        - SSH key authentication (preferred)
        - Password authentication (fallback)
    """

    def __init__(self, config: SFTPConfig) -> None:
        self._remote_base = config.remote_path.strip("/")
        self._ssh = SSHClient(
            host=config.host,
            port=int(config.port),
            username=config.username,
            key=config.key,
            password=config.password,
        )

    def upload(self, local_path: str, remote_path: str, sidecar_path: str | None = None) -> None:
        """
        Upload a backup archive atomically with SHA-256 verification.

        Steps (all in one connection):
            1. Ensure remote directory exists
            2. Compute local SHA-256 and write .sha256 sidecar
            3. Upload archive via .tmp → verify → rename
            4. Upload .sha256 sidecar (plain — it is tiny and text-only)
        """
        local = Path(local_path)
        remote_path = remote_path.replace("\\", "/")
        remote_dir = remote_path.rsplit("/", 1)[0]

        with self._session() as client:
            client.mkdir(remote_dir)
            atomic_upload(client, local, remote_path)
 
            if sidecar_path:
                sidecar_local = write_sidecar(local)
                sidecar_remote_dir = sidecar_path.rsplit("/", 1)[0]
                client.mkdir(sidecar_remote_dir)
                client.upload_file(sidecar_local, sidecar_path)
                logger.debug("Sidecar uploaded: %s", sidecar_path)
 
        logger.info("Upload complete: %s", remote_path)

    def list_backups(self) -> list[str]:
        """
        List all backup archive paths under the configured remote base.

        Excludes .sha256 sidecars, .tmp staging files, and protected files
        so that only complete, real archives are returned to the retention
        executor.
        """
        with self._session() as client:
            all_files = client.list_files(self._remote_base)

        eligible = [
            f for f in all_files
            if f.rsplit("/", 1)[-1] not in _PROTECTED
            and not any(f.endswith(ext) for ext in _SKIP_EXTENSIONS)
        ]

        logger.debug(
            "%d eligible backup(s) of %d total remote files",
            len(eligible),
            len(all_files),
        )

        return eligible

    def delete(self, remote_path: str) -> None:
        """
        Delete a backup archive and its .sha256 sidecar.

        Protected files are never deleted, even if explicitly requested.
        A missing sidecar is not an error — older backups may not have one.
        """
        if remote_path.rsplit("/", 1)[-1] in _PROTECTED:
            logger.warning("Refusing to delete protected file: %s", remote_path)
            return
        
        sidecar_path = _backup_path_to_sidecar_path(remote_path)

        with self._session() as client:
            client.delete(remote_path)
            logger.debug("Deleted archive: %s", remote_path)
 
            if sidecar_path:
                try:
                    client.delete(sidecar_path)
                    logger.debug("Deleted sidecar: %s", sidecar_path)
                except FileNotFoundError:
                    pass

    def _session(self) -> "_SFTPSession":
        return _SFTPSession(self._ssh)

def _backup_path_to_sidecar_path(backup_path: str) -> str | None:
    """
    Derive the metadata sidecar path from a backup archive path.
 
    Replaces the /backups/ segment with /metadata/ and appends .sha256.
 
    Example:
        paperless/backups/2026/05/07/2026-05-07_12-00-00.tar.gz
        → paperless/metadata/2026/05/07/2026-05-07_12-00-00.tar.gz.sha256
 
    Returns None if the path does not contain /backups/ (unexpected layout).
    """
    if "/backups/" not in backup_path:
        logger.debug("Cannot derive sidecar path — no /backups/ segment: %s", backup_path)
        return None
 
    return backup_path.replace("/backups/", "/metadata/", 1) + SIDECAR_EXTENSION


class _SFTPSession:
    """
    Context manager that opens an SSH+SFTP session and closes it on exit.

    Usage:
        with self._session() as client:
            client.upload_file(...)

    Keeps connection lifetime as short as possible — one operation per session.
    """

    def __init__(self, ssh: SSHClient) -> None:
        self._ssh = ssh
        self._client: SFTPClient | None = None

    def __enter__(self) -> SFTPClient:
        transport = self._ssh.connect()
        self._client = SFTPClient(transport)
        return self._client

    def __exit__(self, *_) -> None:
        if self._client:
            self._client.close()
        self._ssh.close()