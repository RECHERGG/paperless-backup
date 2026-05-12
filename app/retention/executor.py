"""
Retention executor.
 
Bridges the gap between the retention policy (pure logic) and
the storage backend (side effects). This is the only module that
performs actual deletions.
 
Separation of concerns:
- Policy:   decides WHAT to delete (no I/O)
- Executor: performs the deletion (I/O only, no business logic)
"""
 
import logging
 
from app.retention.base import BackupFile, RetentionPolicy
from app.retention.parser import parse_timestamp_from_filename
from app.storage.base import Storage
 
logger = logging.getLogger(__name__)
 
 
def apply_retention(storage: Storage, policy: RetentionPolicy, dry_run: bool = False) -> int:
    """
    List remote backups, apply the retention policy, and delete expired files.
 
    Args:
        storage:  Connected storage backend.
        policy:   Configured retention policy instance.
        dry_run:  If True, log deletions but do not execute them.
 
    Returns:
        Number of files deleted (or that would be deleted in dry_run mode).
    """
    logger.info("Starting retention run (dry_run=%s)...", dry_run)
 
    remote_files = storage.list_backups()
 
    if not remote_files:
        logger.info("No remote backups found — nothing to do.")
        return 0
 
    backup_files = _parse_backup_files(remote_files)
 
    if not backup_files:
        logger.warning("No parseable backup files found — skipping retention.")
        return 0
 
    to_delete = policy.select_files_to_delete(backup_files)
 
    if not to_delete:
        logger.info("Retention policy: all %d backup(s) qualify for retention.", len(backup_files))
        return 0
 
    logger.info(
        "Retention policy: keeping %d, deleting %d of %d total backup(s).",
        len(backup_files) - len(to_delete),
        len(to_delete),
        len(backup_files),
    )
 
    deleted = 0
 
    for f in sorted(to_delete):
        if dry_run:
            logger.info("[DRY RUN] Would delete: %s", f.path)
        else:
            try:
                storage.delete(f.path)
                deleted += 1
            except Exception:
                logger.exception("Failed to delete: %s", f.path)
 
    logger.info("Retention complete. Deleted: %d file(s).", deleted)
    return deleted
 
 
def _parse_backup_files(remote_paths: list[str]) -> list[BackupFile]:
    """
    Convert raw remote paths into BackupFile objects.
 
    Skips files whose timestamps cannot be parsed.
    """
    result = []
 
    for path in remote_paths:
        ts = parse_timestamp_from_filename(path)
        if ts is None:
            logger.warning("Skipping unparseable file: %s", path)
            continue
        result.append(BackupFile(path=path, timestamp=ts))
 
    return result