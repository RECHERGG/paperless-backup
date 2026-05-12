"""
Checksum computation for backup archives.
 
This module is intentionally narrow: it knows about bytes and files,
nothing about storage backends or network I/O.
 
Responsibilities:
    - Compute SHA-256 of a local file (streaming, memory-safe)
    - Compute SHA-256 of raw bytes (for verifying downloaded content)
    - Write a .sha256 sidecar file in sha256sum-compatible format
    - Parse a .sha256 sidecar file back to a digest string
 
What does NOT belong here:
    - Anything that touches a network or remote filesystem
    - Comparing local vs remote (that is the upload layer's job)
 
Sidecar format (compatible with `sha256sum` / `shasum -a 256`):
    <hex_digest>  <filename>\\n
 
Example:
    a3f1...c9  2026-05-07_12-00-00.tar.gz
"""

import hashlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1024 * 1024  # 1 MB
SIDECAR_EXTENSION = ".sha256"


def compute_sha256_file(path: Path) -> str:
    """
    Compute the SHA-256 hex digest of a file.
 
    Reads in 1 MB chunks — safe for archives of any size.
 
    Args:
        path: Path to the file.
 
    Returns:
        Lowercase 64-character hex digest.
 
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Cannot checksum missing file: {path}")
 
    hasher = hashlib.sha256()
 
    with path.open("rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            hasher.update(chunk)
 
    digest = hasher.hexdigest()
    logger.debug("SHA-256(%s) = %s", path.name, digest)
    return digest


def compute_sha256_bytes(data: bytes) -> str:
    """
    Compute the SHA-256 hex digest of a bytes object.
 
    Used to verify content that was downloaded into memory from
    a remote storage backend.
 
    Args:
        data: Raw bytes to hash.
 
    Returns:
        Lowercase 64-character hex digest.
    """
    return hashlib.sha256(data).hexdigest()
 
 
def write_sidecar(archive_path: Path) -> Path:
    """
    Compute SHA-256 of an archive and write a .sha256 sidecar next to it.
 
    Args:
        archive_path: Path to the archive file.
 
    Returns:
        Path to the created sidecar file.
    """
    digest = compute_sha256_file(archive_path)
    sidecar_path = archive_path.with_suffix(archive_path.suffix + SIDECAR_EXTENSION)
    sidecar_path.write_text(f"{digest}  {archive_path.name}\n", encoding="utf-8")
 
    logger.debug("Sidecar written: %s", sidecar_path.name)
    return sidecar_path
 
 
def read_sidecar(sidecar_path: Path) -> str:
    """
    Parse a .sha256 sidecar file and return the digest.
 
    Args:
        sidecar_path: Path to the .sha256 file.
 
    Returns:
        The hex digest string.
 
    Raises:
        FileNotFoundError: If the sidecar file does not exist.
        ValueError: If the file is malformed or empty.
    """
    if not sidecar_path.exists():
        raise FileNotFoundError(f"Sidecar not found: {sidecar_path}")
 
    parts = sidecar_path.read_text(encoding="utf-8").strip().split()
 
    if not parts:
        raise ValueError(f"Sidecar file is empty: {sidecar_path}")
 
    return parts[0]