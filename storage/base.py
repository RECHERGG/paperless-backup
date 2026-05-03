"""
Base storage interface.
"""

class Storage:
    """
    Abstract storage interface.
    """

    def upload(self, local_path: str, remote_path: str):
        """
        Upload a file to remote storage.

        Args:
            local_path (str): Path to local file
            filename (str): Traget filename on remote
        """
        raise NotImplementedError("Upload method must be implemented by subclass")
    
    def test_connection(self):
        """
        Optional: test connection to storage.
        """
        raise NotImplementedError("Test connection method must be implemented by subclass")