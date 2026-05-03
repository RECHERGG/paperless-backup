"""
Storage factory for selecting the correct backend.
"""

from sftp import SFTPStorage

def get_storage(config: dict):
    """
    Create a storage instance based on configuration.

    Args:
        config (dict): Full application configuration.
    
    Returns:
        Storage: Concrete storage implementation
    """
    storage_config = config["storage"]
    if "sftp" in storage_config:
        return SFTPStorage(storage_config["sftp"])
    
    raise ValueError("No valid storage configuration found")
