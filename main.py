from pathlib import Path
from dotenv import load_dotenv
from app.config.loader import load_config

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

config = load_config()

print(config)