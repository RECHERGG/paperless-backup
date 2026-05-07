"""
Storage factory for selecting the correct backend.
"""

from app.config.typed import AppConfig
from app.storage.sftp.sftp_storage import SFTPStorage


def get_storage(config: AppConfig):
    """
    Create a storage instance based on configuration.

    Args:
        config (AppConfig): Full application configuration.
    
    Returns:
        Storage: Concrete storage implementation.

    Raises:
        ValueError: If no valid storage config found.
    """ 
    if config.storage_sftp:
        return SFTPStorage(config.storage_sftp)
    
    raise ValueError("No valid storage configuration found")
