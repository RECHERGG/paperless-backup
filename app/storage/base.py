"""
Storage abstractions.

Two levels of abstraction live here:

StorageClient (Protocol)
    Low-level I/O primitives — one per operation.
    Each storage backend (SFTP, S3, local) implements this.
    It knows nothing about backups, checksums, or retention.

    Methods every backend must provide:
        upload_file(local_path, remote_path)
        download_bytes(remote_path) -> bytes
        rename(src, dst)
        delete(remote_path)
        list_files(remote_dir) -> list[str]
        mkdir(remote_path)

Storage (ABC)
    High-level backup interface consumed by the rest of the application.
    Implementations orchestrate StorageClient + cross-cutting concerns
    (atomic upload, checksum sidecars, protected-file guards).

    Methods the application calls:
        upload(local_path, remote_path)
        list_backups() -> list[str]
        delete(remote_path)

Why two layers?
    StorageClient  → swappable I/O backend (SFTP / S3 / local / mock)
    Storage        → stable interface the application depends on

    The upload.py mixin sits between them: it takes a StorageClient and
    implements the atomic-upload + checksum logic once, so every backend
    gets it for free without duplicating a single line.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class StorageClient(Protocol):
    """
    Low-level I/O primitives for a remote storage backend.

    Implementations must be stateless with respect to connection
    lifecycle — callers manage connect/disconnect externally.
    """

    def upload_file(self, local_path: Path, remote_path: str) -> None:
        """Upload a local file to a remote path."""
        ...

    def download_bytes(self, remote_path: str) -> bytes:
        """Download a remote file and return its raw contents."""
        ...

    def rename(self, src: str, dst: str) -> None:
        """Rename (move) a remote file."""
        ...

    def delete(self, remote_path: str) -> None:
        """Delete a remote file."""
        ...

    def list_files(self, remote_dir: str) -> list[str]:
        """
        Recursively list all files under a remote directory.

        Returns full paths, files only (no directories).
        """
        ...

    def mkdir(self, remote_path: str) -> None:
        """Create a remote directory, including any missing parents."""
        ...


class Storage(ABC):
    """
    High-level backup storage interface.

    This is the only storage type the rest of the application imports.
    Concrete subclasses wire a StorageClient into the atomic-upload
    + checksum flow defined in upload.py.
    """

    @abstractmethod
    def upload(
        self, local_path: str, remote_path: str, sidecar_path: str | None = None
    ) -> None:
        """
        Upload a backup archive to remote storage.

        Implementations are expected to:
        - Use atomic upload (.tmp → rename)
        - Verify integrity via checksum after upload
        - Write a .sha256 sidecar alongside the archive

        Args:
            local_path:  Path to the local archive file.
            remote_path: Final remote destination path.
        """
        ...

    @abstractmethod
    def list_backups(self) -> list[str]:
        """
        Return all backup archive paths eligible for retention.

        Excludes sidecar files, in-progress uploads, and protected files.
        """
        ...

    @abstractmethod
    def delete(self, remote_path: str) -> None:
        """
        Delete a backup archive and any associated sidecar files.

        Args:
            remote_path: Full remote path to the archive.
        """
        ...
