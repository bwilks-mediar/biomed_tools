from typing import Optional, Dict, Any, List, Union
import time
import requests
from loguru import logger
from . import config

class ChemblAPI:
    BASE_URL = config.API_BASE_URL

    def __init__(self):
        self.session = requests.Session()

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.BASE_URL}/{endpoint}"
        if params is None:
            params = {}
        if "format" not in params:
            params["format"] = "json"

        for attempt in range(config.MAX_RETRIES):
            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{config.MAX_RETRIES}): {e}")
                if attempt < config.MAX_RETRIES - 1:
                    time.sleep(config.RETRY_BACKOFF**attempt)
                else:
                    logger.error(f"Failed to fetch data from {url} after {config.MAX_RETRIES} attempts.")
                    return None

    def search_molecules(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Search for molecules using a text query.
        endpoint: molecule/search
        """
        if params is None:
            params = {}
        params["q"] = query
        return self._make_request("molecule/search", params)

    def list_molecules(self, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        List molecules with filters (e.g. pagination).
        endpoint: molecule
        """
        return self._make_request("molecule", params)

    def fetch_molecule(self, chembl_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a single molecule.
        endpoint: molecule/{chembl_id}
        """
        return self._make_request(f"molecule/{chembl_id}")
    
    def molecule_mechanisms(self, chembl_id: str) -> Optional[Dict[str, Any]]:
        """
        Get mechanisms for a molecule.
        endpoint: mechanism
        """
        return self._make_request("mechanism", {"molecule_chembl_id": chembl_id})
