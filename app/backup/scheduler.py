import logging
import time
from datetime import datetime, timedelta
from typing import Callable

logger = logging.getLogger(__name__)


def run_scheduler(
    interval_hours: int,
    job: Callable[[], None],
) -> None:
    """
    Run a job forever on aligned hourly boundaries.

    Example:
        interval=6
        -> 00:00, 06:00, 12:00, 18:00
    """
    logger.info(
        "Scheduler started (interval=%sh)",
        interval_hours,
    )

    while True:
        next_backup = _next_run(interval_hours)

        sleep_seconds = (next_backup - datetime.now()).total_seconds()

        logger.info(
            "Next backup scheduled for %s",
            next_backup.isoformat(),
        )

        time.sleep(max(0, sleep_seconds))

        try:
            logger.info("Starting scheduled job...")
            job()
            logger.info("Scheduled job finished successfully.")

        except Exception:
            logger.exception("Scheduled job failed.")


def _next_run(interval_hours: int) -> datetime:
    """
    Calculate next aligned execution time.
    """
    now = datetime.now()

    next_hour = ((now.hour // interval_hours) + 1) * interval_hours

    if next_hour >= 24:
        return now.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        ) + timedelta(days=1)

    return now.replace(
        hour=next_hour,
        minute=0,
        second=0,
        microsecond=0,
    )
