"""Configuration constants for Orange Book Miner."""

from pathlib import Path
from loguru import logger

# --- Core Settings ---
DB_URL = "sqlite:///db/orange_book.db"
LOG_FILE = Path("logs") / "orange_book.log"
DATA_DIR = Path("orange_book_data")

# --- Orange Book Settings ---
DATA_URL = "https://www.fda.gov/media/76860/download?attachment"
MAX_AGE_DAYS = 30

# --- Logging Configuration ---
LOG_LEVEL = "INFO"
LOG_ROTATION = "10 MB"
LOG_COMPRESSION = "zip"

def get_db_path() -> Path:
    """Returns the path to the database file."""
    return Path(DB_URL.replace("sqlite:///", ""))

def ensure_dir_exists():
    """Ensures the data and logs directory for the database and logs exists."""
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

_logging_configured = False

def configure_logging():
    """Configures the logger to write to a file."""
    global _logging_configured
    if _logging_configured:
        return

    ensure_dir_exists()
    logger.add(
        LOG_FILE,
        rotation=LOG_ROTATION,
        compression=LOG_COMPRESSION,
        level=LOG_LEVEL,
    )
    _logging_configured = True
