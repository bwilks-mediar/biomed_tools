"""Utility functions for PubMed Miner."""

import re
from datetime import datetime
from typing import Optional

from loguru import logger


def normalize_query(query: str) -> str:
    """Strips, lowercases, and removes extra whitespace from a query string."""
    return re.sub(r"\s+", " ", query.strip().lower())


def parse_pub_date(date_str: str) -> Optional[datetime.date]:
    """Parses publication date strings from MEDLINE records into date objects."""
    if not date_str:
        return None
    match = re.search(r"(\d{4})(?: (\w{3}))?(?: (\d{1,2}))?", date_str)
    if not match:
        return None
    try:
        year, month, day = match.groups()
        month_map = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
            "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
        }
        month_num = month_map.get(month.lower(), 1) if month else 1
        day_num = int(day) if day else 1
        return datetime(int(year), month_num, day_num).date()
    except (ValueError, TypeError):
        logger.warning(f"Could not parse date string: {date_str}")
        return None
