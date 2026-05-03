"""
Backup engine entrypoint.
"""

from datetime import datetime
from runner import run_backup

def generate_filename(format_str: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return format_str.replace("{timestamp}", timestamp)

def run(config: dict):
    filename = generate_filename(config["backup"]["filename_format"])
    run_backup(config, filename)