"""Utility functions for UniProt Miner."""

import re
import time
from typing import Any, Callable

import requests
from loguru import logger

from ..uniprot import config


def safe_request(url: str, params: dict) -> requests.Response:
    """
    Makes a request to the given URL with the given parameters, with retries.
    """
    for attempt in range(config.MAX_RETRIES):
        try:
            resp = requests.get(url, params=params)
            resp.raise_for_status()
            return resp
        except requests.exceptions.RequestException as e:
            logger.warning(
                f"Request failed (attempt {attempt + 1}/{config.MAX_RETRIES}): {e}"
            )
            if attempt < config.MAX_RETRIES - 1:
                time.sleep(config.RETRY_BACKOFF**attempt)
            else:
                raise


def normalize_query(query: str) -> str:
    """
    Normalizes a search query by lowercasing and removing extra whitespace.
    """
    return " ".join(query.lower().split())
