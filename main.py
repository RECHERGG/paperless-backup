"""
Application entrypoint for Paperless Backup.
"""

import logging
from pathlib import Path

from dotenv import load_dotenv

from app.backup.engine import run
from app.backup.scheduler import run_scheduler
from app.config.typed import load_typed_config


def setup_logging():
    """
    Configure global logging settings.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def load_environment(base_dir: Path):
    """
    Load environment variables from .env file if present.

    Args:
        base_dir (Path): Base directory of the application.
    """
    env_path = base_dir / ".env"

    if env_path.exists():
        load_dotenv(env_path)
        logging.getLogger(__name__).debug("Loaded .env file from %s", env_path)
    else:
        logging.getLogger(__name__).debug("No .env file found at %s", env_path)


def main() -> int:
    """
    Main application entrypoint.

    Returns:
        int: Exit code (0 = success, 1 = failure).
    """
    setup_logging()
    logger = logging.getLogger(__name__)

    base_dir = Path(__file__).resolve().parent

    try:
        logger.info("Initializing application...")

        load_environment(base_dir)

        logger.info("Loading configuration...")
        config = load_typed_config()

        run_scheduler(
            interval_hours=config.backup.interval_hours,
            job=lambda: run(config),
        )

        return 0

    except KeyboardInterrupt:
        logger.info("Shutdown requested by user.")
        return 0

    except Exception:
        logger.exception("Fatal error during execution.")
        return 1

    finally:
        logger.info("Application stopped.")


if __name__ == "__main__":
    raise SystemExit(main())
