"""
SSH connection handler.

Responsible ONLY for:
- Establishing SSH transport
- Handling authentication (key or password)
- Providing lifecycle management of the connection
"""

import paramiko
import logging
from io import StringIO

logger = logging.getLogger(__name__)


class SSHClient:
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        key: str | None = None,
        password: str | None = None,
    ):
        """
        Args:
            host: SSH host
            port: SSH port
            username: SSH user
            key: private key content (optional)
            password: password fallback (optional)
        """
        self.host = host
        self.port = port
        self.username = username
        self.key = key
        self.password = password

        self._transport = None
        self._sftp = None

    def _load_key(self, key_str: str):
        key = StringIO(key_str)

        try:
            return paramiko.Ed25519Key.from_private_key(key)
        except Exception:
            key.seek(0)
            try:
                return paramiko.RSAKey.from_private_key(key)
            except Exception as e:
                raise RuntimeError("Unsupported SSH key format") from e

    def connect(self):
        """Get or establish SSH transport connection."""

        if self._transport and self._transport.is_active():
            return self._transport

        logger.info("Connecting to SSH %s:%s", self.host, self.port)

        transport = paramiko.Transport((self.host, self.port))

        transport.set_keepalive(30)

        if self.key:
            logger.info("Using SSH key authentication")
            pkey = self._load_key(self.key)
            transport.connect(username=self.username, pkey=pkey)

        elif self.password:
            logger.info("Using password authentication")
            transport.connect(username=self.username, password=self.password)

        else:
            raise ValueError("No authentication method provided for SSH connection")

        self._transport = transport
        return transport

    def close(self):
        """Close SFTP and SSH transport."""

        if self._sftp:
            self._sftp.close()
            self._sftp = None

        if self._transport:
            self._transport.close()
            self._transport = None
        logger.info("SSH connection closed")

    def get_sftp(self):
        """Get or establish persistent SFTP session."""
        transport = self.connect()

        if self._sftp is not None:
            try:
                self._sftp.stat(".")
                return self._sftp
            except Exception:
                logger.warning("SFTP session dead, reopening")

        self._sftp = paramiko.SFTPClient.from_transport(transport)
        return self._sftp
