"""Harvester for GEOmetadb."""

import gzip
import shutil
import requests
from loguru import logger

from . import config

# Configure logging when module is imported
config.configure_logging()

def download_geometadb():
    """Download the GEOmetadb SQLite file."""
    config.ensure_dir_exists()
    db_path = config.get_db_path()
    
    if db_path.exists():
        logger.info(f"GEOmetadb.sqlite already exists at {db_path}")
        return

    # URL from GEOmetadb R package
    url = "https://gbnci.cancer.gov/geo/GEOmetadb.sqlite.gz"
    gz_path = db_path.with_suffix(".sqlite.gz")
    
    logger.info(f"Downloading GEOmetadb from {url}...")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(gz_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        logger.info("Extracting GEOmetadb.sqlite.gz...")
        with gzip.open(gz_path, 'rb') as f_in:
            with open(db_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Cleanup gz file
        gz_path.unlink()
        logger.info("GEOmetadb.sqlite downloaded and extracted successfully.")
        
    except Exception as e:
        logger.error(f"Failed to download GEOmetadb: {e}")
        if gz_path.exists():
            gz_path.unlink()
        if db_path.exists():
            db_path.unlink()
        raise
