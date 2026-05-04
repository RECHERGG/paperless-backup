"""
Storage factory for selecting the correct backend.
"""

from storage.sftp_storage import SFTPStorage


def get_storage(config: dict):
    """
    Create a storage instance based on configuration.

    Args:
        config (dict): Full application configuration.
    
    Returns:
        Storage: Concrete storage implementation.

    Raises:
        ValueError: If no valid storage config found.
    """
    storage_config = config["storage"]
    
    if "sftp" in storage_config:
        return SFTPStorage(storage_config["sftp"])
    
    raise ValueError("No valid storage configuration found")
