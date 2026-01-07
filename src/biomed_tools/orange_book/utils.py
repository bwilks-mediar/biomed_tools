"""Utility functions for Orange Book Miner."""

import time
import requests
import zipfile
import io
from pathlib import Path
from loguru import logger
from . import config

def is_data_stale() -> bool:
    """Check if data is missing or older than max_age_days."""
    products_path = config.DATA_DIR / 'products.txt'
    if not products_path.exists():
        return True
        
    try:
        mtime = products_path.stat().st_mtime
        age_seconds = time.time() - mtime
        age_days = age_seconds / (24 * 3600)
        return age_days > config.MAX_AGE_DAYS
    except OSError:
        return True

def download_data() -> None:
    """Downloads and extracts the Orange Book data."""
    config.DATA_DIR.mkdir(exist_ok=True, parents=True)
    logger.info(f"Downloading Orange Book data from {config.DATA_URL}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(config.DATA_URL, headers=headers)
        response.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            z.extractall(config.DATA_DIR)
        logger.info("Download complete.")
    except Exception as e:
        logger.error(f"Failed to download data: {e}")
        raise
