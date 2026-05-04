"""
Base storage interface.
"""

from abc import ABC, abstractmethod

class Storage:
    """
    Abstract storage interface for backup destinations.
    """

    @abstractmethod
    def upload(self, local_path: str, remote_path: str):
        """
        Upload a file to remote storage.

        Args:
            local_path (str): Path to local file.
            remote_path (str): Target filename/path on remote storage.
        """
        pass
    
    def test_connection(self):
        """
        Optional: test connection to storage.
        """
        raise NotImplementedError