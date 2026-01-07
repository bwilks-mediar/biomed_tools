from typing import Optional, Dict, Any, List, Union
import time
import requests
from loguru import logger
from . import config

class UniprotAPI:
    BASE_URL = config.API_BASE_URL

    def __init__(self):
        self.session = requests.Session()

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        Makes a request to the given endpoint.
        Returns the raw response object to allow access to headers (for pagination).
        """
        if endpoint.startswith("http"):
            url = endpoint
        else:
            url = f"{self.BASE_URL}/{endpoint}"
            
        for attempt in range(config.MAX_RETRIES):
            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{config.MAX_RETRIES}): {e}")
                if attempt < config.MAX_RETRIES - 1:
                    time.sleep(config.RETRY_BACKOFF**attempt)
                else:
                    logger.error(f"Failed to fetch data from {url} after {config.MAX_RETRIES} attempts.")
                    return None

    def search_proteins(self, query: str, size: int = 500) -> Optional[Dict[str, Any]]:
        """
        Searches for proteins matching the query.
        
        :param query: UniProt query string (e.g., 'gene:brca1').
        :param size: Number of results per page.
        :return: JSON response from the API, including results and pagination info (if handled by caller).
        """
        params = {
            "query": query,
            "size": size,
            "format": "json"
        }
        response = self._make_request("search", params)
        if response:
            return response.json(), response.headers.get("Link")
        return None, None

    def fetch_protein(self, accession: str) -> Optional[Dict[str, Any]]:
        """
        Fetches a single protein by accession.
        
        :param accession: UniProt accession (e.g., 'P12345').
        :return: JSON response from the API.
        """
        response = self._make_request(f"{accession}")
        if response:
            return response.json()
        return None
