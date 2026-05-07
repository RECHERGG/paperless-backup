"""
Typed configuration layer for Paperless Backup.

This module transforms the raw configuration (strings with resolved
environment variables) into strongly typed Python objects.

Responsibilities:
- Convert raw dict -> typed dataclasses
- Apply defaults (safety layer)
- Ensure correct types (int, bool, str)
- Provide a single source of truth for application config
"""

from dataclasses import dataclass

from app.config.loader import load_config
from app.config.parsers import parse_int, parse_bool, parse_str

@dataclass(frozen=True)
class BackupConfig:
    """
    Configuration related to backup execution.

    Attributes:
        interval_hours: Interval between backups in hours.
        filename_template: Template for archive file names.
        delete_local_after_upload: Whether local files are deleted after upload.
        keep_failed_backups: Whether failed backups are preserved for debugging.
    """
    interval_hours: int
    filename_template: str
    delete_local_after_upload: bool
    keep_failed_backups: bool


@dataclass(frozen=True)
class PaperlessConfig:
    """
    Paperless container configuration.

    Attributes:
        container_name: Docker container name of Paperless instance.
    """
    container_name: str


@dataclass(frozen=True)
class SFTPConfig:
    """
    SFTP storage configuration.

    Attributes:
        host: SFTP host (e.g. Hetzner Storage Box)
        port: SSH/SFTP port (usually 22)
        username: login username
        key: optional SSH private key (string)
        password: optional password fallback
        remote_path: remote backup directory
    """
    host: str
    port: int
    username: str
    key: str | None
    password: str | None
    remote_path: str


@dataclass(frozen=True)
class RetentionConfig:
    """
    Backup retention policy configuration.

    The active strategy is selected via `strategy`. Only the fields
    relevant to the chosen strategy need to be set - others are ignored.

    Shared:
        strategy:       One of : gfs | simple | time | daily | none
        minimum_keep:   Safety floor - always keep at least this many recent
                        backups, regardless of strategy. Used by: time, daily.
    
    GFS (gfs):
        hourly:     Number of most-recent backups to keep (hourly bucket).
        daily:      One backup per day for the last N days.
        weekly:     One backup per week for the last N weeks.
        monthly:    One backup per month for the last N months.

    Simple (simple):
        keep_last: Keep only the N most recent backups.

    Time-based (time):
        max_age_days: Delete backups older than N days.
        minimum_keep: Always retain at least this many recent backups.
    
    Daily-only (daily):"
        keep_days:      Retain one backup per day for the last N days.
        minimum_keep:   Always retain at least this many recent backups.
    
    No-op (none):
        No fields required. Nothing is ever deleted. 
    """
    strategy: str

    # GFS
    hourly: int
    daily: int
    weekly: int
    monthly: int

    # Simple
    keep_last: int

    # Time-based
    max_age_days: int

    # Daily-only
    keep_days: int

    # Shared safety floor (time + daily)
    minimum_keep: int


@dataclass(frozen=True)
class AppConfig:
    """
    Root application configuration object.

    This is the single entry point used by the entire system.
    """
    backup: BackupConfig
    paperless: PaperlessConfig
    storage_sftp: SFTPConfig
    retention: RetentionConfig


def load_typed_config() -> AppConfig:
    """
    Load raw config and convert it into a fully typed AppConfig.

    Returns:
        AppConfig: Fully typed application configuration
    """
    raw = load_config()
    r = raw["retention"]
    rules = r.get("rules", {})

    return AppConfig(
        backup=BackupConfig(
            interval_hours=parse_int(raw["backup"]["interval_hours"], 6),
            filename_template=parse_str(
                raw["backup"]["filename_template"],
                "{timestamp}.tar.gz",
            ),
            delete_local_after_upload=parse_bool(
                raw["backup"]["delete_local_after_upload"], True
            ),
            keep_failed_backups=parse_bool(
                raw["backup"]["keep_failed_backups"], True
            ),
        ),

        paperless=PaperlessConfig(
            container_name=parse_str(
                raw["paperless"]["container_name"],
                "paperless-webserver",
            ),
        ),

        storage_sftp=SFTPConfig(
            host=raw["storage"]["sftp"]["host"],
            port=parse_int(raw["storage"]["sftp"]["port"], 22),
            username=raw["storage"]["sftp"]["username"],
            key=raw["storage"]["sftp"].get("key"),
            password=raw["storage"]["sftp"].get("password"),
            remote_path=parse_str(
                raw["storage"]["sftp"]["remote_path"],
                "paperless-backups",
            ),
        ),


        retention=RetentionConfig(
            strategy=parse_str(r.get("strategy"), "gfs"),
 
            # GFS
            hourly=parse_int(rules.get("hourly"), 24),
            daily=parse_int(rules.get("daily"), 7),
            weekly=parse_int(rules.get("weekly"), 4),
            monthly=parse_int(rules.get("monthly"), 12),
 
            # Simple
            keep_last=parse_int(rules.get("keep_last"), 10),
 
            # Time-based
            max_age_days=parse_int(rules.get("max_age_days"), 30),
 
            # Daily-only
            keep_days=parse_int(rules.get("keep_days"), 7),
 
            # Shared
            minimum_keep=parse_int(rules.get("minimum_keep"), 1),
        ),
    )