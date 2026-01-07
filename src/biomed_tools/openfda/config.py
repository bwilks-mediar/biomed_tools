"""Configuration constants for OpenFDA module."""

import sys
from pathlib import Path
from loguru import logger

# --- Core Settings ---
DB_URL = "sqlite:///db/openfda.db"
LOG_FILE = Path("logs") / "openfda.log"

# --- OpenFDA API Settings ---
API_BASE_URL = "https://api.fda.gov/drug"
# Default limit per request. Can be increased to 1000 if using an API key.
CHUNK_SIZE = 100  
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0

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
