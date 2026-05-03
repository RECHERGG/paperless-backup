"""
SFTP storage implementation.
"""

import paramiko
from base import Storage

class SFTPStorage(Storage):
    def __init__(self, config: dict):
        self.host = config["host"]
        self.port = int(config.get("port"))
        self.username = config["username"]
        self.password = config.get("password")
        self.remote_path = config.get("remote_path")
    
    def upload(self, local_path: str, remote_path: str):
        transport = paramiko.Transport((self.host, self.port))
        transport.connect(username=self.username, password=self.password)

        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.put(local_path, f"{self.remote_path}/{remote_path}")

        sftp.close()
        transport.close()