"""
Atomic upload with integrity verification.
 
This module contains one function that every Storage backend can call.
It depends only on:
    - StorageClient (the I/O interface)   → app/storage/base.py
    - checksum.py (pure hashing)          → app/storage/checksum.py
 
It has zero knowledge of SFTP, S3, or any concrete backend.
 
The atomic upload pattern:
    Upload to <remote>.tmp
        → if the connection drops, the real path is never touched.
    Download the .tmp content and verify SHA-256 matches local.
        → catches corruption in transit.
    Rename .tmp → <remote>
        → the file appears at its final path only once it is verified.
    On any failure, delete the .tmp file (best-effort cleanup).
"""

import logging
from pathlib import Path
 
from app.storage.base import StorageClient
from app.storage.checksum import compute_sha256_file, compute_sha256_bytes
 
logger = logging.getLogger(__name__)
 
TMP_SUFFIX = ".tmp"
 
 
def atomic_upload(
    client: StorageClient,
    local_path: Path,
    remote_path: str,
    verify: bool = True,
) -> None:
    """
    Upload a file atomically: stage as .tmp, verify, then rename.
 
    Args:
        client:      A StorageClient implementation (SFTP, S3, local, …).
        local_path:  The local file to upload.
        remote_path: The final remote destination path.
        verify:      Download and verify checksum after upload.
                     Set to False only in tests or when the network is trusted
                     end-to-end (e.g. local filesystem backend).
 
    Raises:
        ValueError:  If the remote checksum does not match the local file.
        OSError:     On unrecoverable I/O errors.
    """
    tmp_path = remote_path + TMP_SUFFIX
 
    logger.debug("Uploading '%s' → staging '%s'", local_path.name, tmp_path)
 
    try:
        client.upload_file(local_path, tmp_path)
 
        if verify:
            _verify(client, local_path, tmp_path)

        # ensure target does not exist (SFTP-safe overwrite behavior)
        try:
            client.delete(remote_path)
        except Exception:
            # file may not exist → ignore
            pass
 
        client.rename(tmp_path, remote_path)
        logger.info("Upload committed: %s", remote_path)
 
    except Exception:
        _cleanup(client, tmp_path)
        raise
 
 
def _verify(client: StorageClient, local_path: Path, remote_tmp_path: str) -> None:
    """
    Download the staged file and compare its SHA-256 against the local source.
 
    Args:
        client:          StorageClient to download from.
        local_path:      Local file (source of truth).
        remote_tmp_path: Staged remote path to verify.
 
    Raises:
        ValueError: On digest mismatch.
    """
    expected = compute_sha256_file(local_path)
    remote_bytes = client.download_bytes(remote_tmp_path)
    actual = compute_sha256_bytes(remote_bytes)
 
    if actual != expected:
        raise ValueError(
            f"Integrity check failed for '{local_path.name}':\n"
            f"  local:  {expected}\n"
            f"  remote: {actual}"
        )
 
    logger.debug("Integrity OK (%s…)", expected[:12])
 
 
def _cleanup(client: StorageClient, tmp_path: str) -> None:
    """Best-effort removal of a staging file. Never raises."""
    try:
        client.delete(tmp_path)
        logger.debug("Staging file removed: %s", tmp_path)
    except Exception:
        logger.warning(
            "Could not remove staging file '%s' — manual cleanup may be needed",
            tmp_path,
        )