"""Utility functions for ChEMBL Miner."""

def normalize_query(query: str) -> str:
    """
    Normalizes a search query by lowercasing and removing extra whitespace.
    """
    return " ".join(query.lower().split())
