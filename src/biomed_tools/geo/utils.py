"""Utility functions for the GEO miner."""

import sqlite3
import pandas as pd
from loguru import logger

from . import config

def find_gse_by_keyword(keyword: str) -> pd.DataFrame:
    """Find GEO series by keyword."""
    db_path = config.get_db_path()
    if not db_path.exists():
        logger.error(f"Database file not found at {db_path}. Please run 'harvest' first.")
        return pd.DataFrame()

    con = sqlite3.connect(db_path)
    
    query = """
        SELECT gse, title, summary 
        FROM gse 
        WHERE title LIKE ? 
        OR summary LIKE ?
    """
    params = (f'%{keyword}%', f'%{keyword}%')
    
    try:
        df = pd.read_sql_query(query, con, params=params)
    except Exception as e:
        logger.error(f"Error querying database: {e}")
        df = pd.DataFrame()
    finally:
        con.close()
    
    return df
