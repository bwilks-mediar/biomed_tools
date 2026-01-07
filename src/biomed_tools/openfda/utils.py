"""Utility functions for OpenFDA module."""

import re

def normalize_query(query: str) -> str:
    """
    Normalizes a search query for consistent storage and retrieval.
    Removes extra whitespace and lowercases the string.
    """
    if not query:
        return ""
    # Replace multiple spaces with single space
    query = re.sub(r'\s+', ' ', query)
    return query.strip().lower()
