"""API client for OpenFDA."""

import time
from typing import Any, Dict, Optional

import requests
from loguru import logger

from . import config

class OpenFDAAPI:
    BASE_URL = config.API_BASE_URL

    def __init__(self):
        self.session = requests.Session()

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.BASE_URL}/{endpoint}"
        for attempt in range(config.MAX_RETRIES):
            try:
                response = self.session.get(url, params=params)
                if response.status_code == 404:
                    # OpenFDA returns 404 for no matches
                    logger.info(f"No results found for query.")
                    return None
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{config.MAX_RETRIES}): {e}")
                if attempt < config.MAX_RETRIES - 1:
                    time.sleep(config.RETRY_BACKOFF**attempt)
                else:
                    logger.error(f"Failed to fetch data from {url} after {config.MAX_RETRIES} attempts.")
                    return None

    def search(self, endpoint: str, query: str, limit: int = 100, skip: int = 0) -> Optional[Dict[str, Any]]:
        """
        Generic search method for OpenFDA endpoints.
        
        :param endpoint: The API endpoint (e.g., 'event.json', 'label.json', 'ndc.json', 'enforcement.json', 'drugsfda.json')
        :param query: The search query string (Lucene syntax).
        :param limit: Number of records to return.
        :param skip: Number of records to skip.
        """
        params = {
            "search": query,
            "limit": limit,
            "skip": skip
        }
        return self._make_request(endpoint, params)

    def search_events(self, query: str, limit: int = 100, skip: int = 0) -> Optional[Dict[str, Any]]:
        return self.search("event.json", query, limit, skip)
    
    def search_labels(self, query: str, limit: int = 100, skip: int = 0) -> Optional[Dict[str, Any]]:
        return self.search("label.json", query, limit, skip)

    def search_ndc(self, query: str, limit: int = 100, skip: int = 0) -> Optional[Dict[str, Any]]:
        return self.search("ndc.json", query, limit, skip)

    def search_enforcement(self, query: str, limit: int = 100, skip: int = 0) -> Optional[Dict[str, Any]]:
        return self.search("enforcement.json", query, limit, skip)

    def search_drugsfda(self, query: str, limit: int = 100, skip: int = 0) -> Optional[Dict[str, Any]]:
        return self.search("drugsfda.json", query, limit, skip)
