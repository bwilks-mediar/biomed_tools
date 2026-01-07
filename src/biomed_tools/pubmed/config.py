"""Configuration constants for PubMed Miner."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

# --- Global Config Variables ---
ENTREZ_EMAIL = None
API_KEY = None
DB_URL = "sqlite:///db/pubmed.db"
LOG_FILE = Path("logs") / "pubmed.log"
CHUNK_SIZE = 200
MAX_RETRIES = 5
RETRY_BACKOFF = 5.0
REQUEST_DELAY = 0.34
LOG_LEVEL = "DEBUG"
LOG_ROTATION = "10 MB"
LOG_COMPRESSION = "zip"

def load_config():
    """Loads configuration from .env file and sets global variables."""
    global ENTREZ_EMAIL, API_KEY, REQUEST_DELAY, TOOL_NAME
    
    load_dotenv()
    
    ENTREZ_EMAIL = os.getenv("ENTREZ_EMAIL")
    if not ENTREZ_EMAIL:
        raise ValueError("Please set the ENTREZ_EMAIL environment variable in your .env file.")
        
    API_KEY = os.getenv("API_KEY")
    TOOL_NAME = os.getenv("TOOL_NAME")

    # Recalculate delay based on loaded API_KEY
    REQUEST_DELAY = 0.1 if API_KEY else 0.34

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

# Load the configuration when the module is imported
load_config()
