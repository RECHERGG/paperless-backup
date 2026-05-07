"""
Abstract base for all retention policies.

Each policy receives a list of BackupFile objects and returns
which files should be deleted.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class BackupFile:
    """
    Represents a single remote backup file.

    Attributes:
        path: Full remote path to the file.
        timestamp: Parsed timestamp from filename.
    """
    path: str
    timestamp: datetime

    def __lt__(self, other: "BackupFile") -> bool:
        return self.timestamp < other.timestamp
    

class RetentionPolicy(ABC):
    """
    Abstract base class for all retention strategies.

    Subclasses implement `select_files_to_keep` which returns
    a set of paths that should be preserved. Everything else
    will be deleted.
    """
    
    @abstractmethod
    def select_files_to_keep(self, files: list[BackupFile]) -> set[str]:
        """
        Determine which backup files to retain.

        Args:
            files: All known remote backup files, sorted ascending by timestamp.

        Returns:
            Set of remote paths that should NOT be deleted.
        """
        ...
    
    def select_files_to_delete(self, files: list[BackupFile]) -> list[BackupFile]:
        """
        Invert of select_files_to_keep.

        Returns:
            List of BackupFile objects that should be removed.
        """
        keep = self.select_files_to_keep(files)
        return [f for f in files if f.path not in keep]