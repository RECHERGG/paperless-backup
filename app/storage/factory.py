"""
Storage factory for selecting the correct backend.
"""

from app.config.typed import AppConfig
from app.storage.base import Storage
from app.storage.sftp.storage import SFTPStorage


def get_storage(config: AppConfig) -> Storage:
    """
    Instantiate the correct Storage backend from configuration.

    Raises:
        ValueError: If no valid storage configuration is found.
    """
    if config.storage_sftp:
        return SFTPStorage(config.storage_sftp)

    raise ValueError("No valid storage configuration found")
