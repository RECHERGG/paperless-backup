"""
Tests for app/storage/checksum.py

Pure functions — only the filesystem is touched (via pytest's tmp_path).
No mocking, no network.
"""

import hashlib
import pytest

from app.storage.checksum import (
    compute_sha256_file,
    compute_sha256_bytes,
    write_sidecar,
    read_sidecar,
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# compute_sha256_file
# ---------------------------------------------------------------------------


class TestComputeSha256File:
    def test_known_content(self, tmp_path):
        data = b"hello world"
        f = tmp_path / "f.bin"
        f.write_bytes(data)
        assert compute_sha256_file(f) == sha256(data)

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.bin"
        f.write_bytes(b"")
        assert compute_sha256_file(f) == sha256(b"")

    def test_large_file_chunked(self, tmp_path):
        data = b"x" * (3 * 1024 * 1024)  # 3 MB → exercises chunked read
        f = tmp_path / "large.bin"
        f.write_bytes(data)
        assert compute_sha256_file(f) == sha256(data)

    def test_returns_lowercase_hex_of_length_64(self, tmp_path):
        f = tmp_path / "f.bin"
        f.write_bytes(b"data")
        digest = compute_sha256_file(f)
        assert len(digest) == 64
        assert digest == digest.lower()

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            compute_sha256_file(tmp_path / "ghost.bin")

    def test_two_different_files_differ(self, tmp_path):
        a = tmp_path / "a.bin"
        b = tmp_path / "b.bin"
        a.write_bytes(b"aaa")
        b.write_bytes(b"bbb")
        assert compute_sha256_file(a) != compute_sha256_file(b)


# ---------------------------------------------------------------------------
# compute_sha256_bytes
# ---------------------------------------------------------------------------


class TestComputeSha256Bytes:
    def test_matches_file_digest(self, tmp_path):
        data = b"some backup content"
        f = tmp_path / "archive.tar.gz"
        f.write_bytes(data)
        assert compute_sha256_bytes(data) == compute_sha256_file(f)

    def test_empty_bytes(self):
        assert compute_sha256_bytes(b"") == sha256(b"")

    def test_returns_lowercase_hex_of_length_64(self):
        digest = compute_sha256_bytes(b"x")
        assert len(digest) == 64
        assert digest == digest.lower()


# ---------------------------------------------------------------------------
# write_sidecar / read_sidecar
# ---------------------------------------------------------------------------


class TestWriteSidecar:
    def test_creates_file_next_to_archive(self, tmp_path):
        archive = tmp_path / "backup.tar.gz"
        archive.write_bytes(b"content")
        sidecar = write_sidecar(archive)
        assert sidecar == tmp_path / "backup.tar.gz.sha256"
        assert sidecar.exists()

    def test_sidecar_contains_correct_digest(self, tmp_path):
        data = b"backup data"
        archive = tmp_path / "backup.tar.gz"
        archive.write_bytes(data)
        sidecar = write_sidecar(archive)
        assert sha256(data) in sidecar.read_text()

    def test_sidecar_format_is_sha256sum_compatible(self, tmp_path):
        archive = tmp_path / "backup.tar.gz"
        archive.write_bytes(b"data")
        sidecar = write_sidecar(archive)
        parts = sidecar.read_text().strip().split()
        assert len(parts) == 2
        assert len(parts[0]) == 64  # digest
        assert parts[1] == "backup.tar.gz"

    def test_overwrites_stale_sidecar(self, tmp_path):
        archive = tmp_path / "backup.tar.gz"
        archive.write_bytes(b"v1")
        write_sidecar(archive)
        archive.write_bytes(b"v2")
        sidecar = write_sidecar(archive)
        assert read_sidecar(sidecar) == sha256(b"v2")


class TestReadSidecar:
    def test_round_trip(self, tmp_path):
        data = b"hello"
        archive = tmp_path / "backup.tar.gz"
        archive.write_bytes(data)
        sidecar = write_sidecar(archive)
        assert read_sidecar(sidecar) == sha256(data)

    def test_missing_sidecar_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            read_sidecar(tmp_path / "missing.sha256")

    def test_empty_sidecar_raises(self, tmp_path):
        sidecar = tmp_path / "bad.sha256"
        sidecar.write_text("")
        with pytest.raises(ValueError, match="empty"):
            read_sidecar(sidecar)
