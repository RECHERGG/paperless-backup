"""
Tests for app/storage/upload.py

The key insight: atomic_upload depends only on StorageClient (a Protocol).
We can test it completely with a simple in-memory fake — no SFTP, no mocking
framework needed.

The fake implements the same interface as SFTPClient but stores everything
in a dict. This is called a "test double" or "fake object" — it is simpler
and more readable than a MagicMock because its behaviour is explicit.
"""

import pytest
from pathlib import Path

from app.storage.upload import atomic_upload, TMP_SUFFIX


# ---------------------------------------------------------------------------
# In-memory StorageClient fake
# ---------------------------------------------------------------------------

class FakeStorageClient:
    """
    In-memory StorageClient for testing upload logic without any I/O.

    State is stored in self.files: dict[remote_path, bytes]
    Tracks all delete calls for assertion.
    """

    def __init__(self, corrupt_on_upload: bool = False):
        self.files: dict[str, bytes] = {}
        self.deleted: list[str] = []
        self._corrupt = corrupt_on_upload

    def upload_file(self, local_path: Path, remote_path: str) -> None:
        data = local_path.read_bytes()
        if self._corrupt:
            data = b"corrupted"
        self.files[remote_path] = data

    def download_bytes(self, remote_path: str) -> bytes:
        if remote_path not in self.files:
            raise FileNotFoundError(f"Not found: {remote_path}")
        return self.files[remote_path]

    def rename(self, src: str, dst: str) -> None:
        if src not in self.files:
            raise FileNotFoundError(f"Cannot rename missing file: {src}")
        self.files[dst] = self.files.pop(src)

    def delete(self, remote_path: str) -> None:
        self.files.pop(remote_path, None)
        self.deleted.append(remote_path)

    def list_files(self, remote_dir: str) -> list[str]:
        return [p for p in self.files if p.startswith(remote_dir)]

    def mkdir(self, remote_path: str) -> None:
        pass  # no-op for in-memory


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestAtomicUpload:
    def test_file_exists_at_final_path_after_upload(self, tmp_path):
        archive = tmp_path / "backup.tar.gz"
        archive.write_bytes(b"backup content")
        client = FakeStorageClient()

        atomic_upload(client, archive, "backups/backup.tar.gz")

        assert "backups/backup.tar.gz" in client.files

    def test_tmp_file_is_gone_after_successful_upload(self, tmp_path):
        archive = tmp_path / "backup.tar.gz"
        archive.write_bytes(b"content")
        client = FakeStorageClient()

        atomic_upload(client, archive, "backups/backup.tar.gz")

        assert "backups/backup.tar.gz" + TMP_SUFFIX not in client.files

    def test_final_content_matches_local(self, tmp_path):
        data = b"real backup data"
        archive = tmp_path / "backup.tar.gz"
        archive.write_bytes(data)
        client = FakeStorageClient()

        atomic_upload(client, archive, "backups/backup.tar.gz")

        assert client.files["backups/backup.tar.gz"] == data

    def test_checksum_mismatch_raises_and_cleans_up(self, tmp_path):
        archive = tmp_path / "backup.tar.gz"
        archive.write_bytes(b"original")
        client = FakeStorageClient(corrupt_on_upload=True)

        with pytest.raises(ValueError, match="Integrity check failed"):
            atomic_upload(client, archive, "backups/backup.tar.gz")

        # .tmp must be cleaned up
        tmp = "backups/backup.tar.gz" + TMP_SUFFIX
        assert tmp not in client.files
        assert tmp in client.deleted

    def test_checksum_mismatch_does_not_commit_final_file(self, tmp_path):
        archive = tmp_path / "backup.tar.gz"
        archive.write_bytes(b"original")
        client = FakeStorageClient(corrupt_on_upload=True)

        with pytest.raises(ValueError):
            atomic_upload(client, archive, "backups/backup.tar.gz")

        assert "backups/backup.tar.gz" not in client.files

    def test_verify_false_skips_download(self, tmp_path):
        archive = tmp_path / "backup.tar.gz"
        archive.write_bytes(b"content")
        # Even a corrupt client passes when verify=False
        client = FakeStorageClient(corrupt_on_upload=True)

        atomic_upload(client, archive, "backups/backup.tar.gz", verify=False)

        assert "backups/backup.tar.gz" in client.files

    def test_upload_failure_does_not_leave_tmp(self, tmp_path):
        archive = tmp_path / "backup.tar.gz"
        archive.write_bytes(b"content")

        class FailingClient(FakeStorageClient):
            def upload_file(self, local_path, remote_path):
                raise OSError("disk full")

        client = FailingClient()

        with pytest.raises(OSError):
            atomic_upload(client, archive, "backups/backup.tar.gz")

        assert not any(".tmp" in p for p in client.files)