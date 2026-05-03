import logging

from pathlib import Path
from dotenv import load_dotenv

from app.config.loader import load_config
from app.backup.engine import run

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

def main():
    setup_logging()

    BASE_DIR = Path(__file__).resolve().parent
    load_dotenv(BASE_DIR / ".env")

    config = load_config()
    run(config)

if __name__ == "__main__":
    main()