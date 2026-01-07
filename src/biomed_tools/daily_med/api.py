from typing import Optional, Dict, Any
import requests
from loguru import logger
from .config import API_BASE_URL

class DailyMedApi:
    """A wrapper class for the DailyMed REST API (v2)."""

    def __init__(self):
        self.session = requests.Session()
        self.base_url = API_BASE_URL

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None, return_json: bool = True) -> Any:
        url = f"{self.base_url}/{endpoint}"
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            if return_json:
                return response.json()
            return response.content
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data from {url}: {e}")
            return None

    def search_drug_name(self, drug_name: str) -> Optional[Dict[str, Any]]:
        """
        Search for a drug by name (returns list of names).

        :param drug_name: Name of the drug.
        :return: Search results or None if not found.
        """
        return self._make_request("drugnames.json", params={"drug_name": drug_name})

    def search_spls(self, drug_name: str, page: int = 1, page_size: int = 100) -> Optional[Dict[str, Any]]:
        """
        Search for SPLs (labels) containing the drug name.
        Returns Set IDs and other metadata.

        :param drug_name: Name of the drug.
        :param page: Page number.
        :param page_size: Results per page.
        :return: Search results with Set IDs.
        """
        return self._make_request("spls.json", params={
            "drug_name": drug_name,
            "page": page,
            "pagesize": page_size
        })

    def get_drug_label(self, set_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the drug label information for a given set ID.

        :param set_id: Set ID of the drug.
        :return: Drug label information or None if not found.
        """
        return self._make_request(f"label/{set_id}.json")

    def get_drug_by_ndc(self, ndc: str) -> Optional[Dict[str, Any]]:
        """
        Get the drug information for a given NDC (National Drug Code).

        :param ndc: National Drug Code.
        :return: Drug information or None if not found.
        """
        return self._make_request(f"ndc/{ndc}.json")

    def get_drug_spls(self, setid: str) -> Optional[bytes]:
        """
        Download the SPL (Structured Product Labeling) XML file.
        
        :param setid: Set ID of the drug.
        :return: XML content in bytes or None if not found.
        """
        return self._make_request(f"spls/{setid}.xml", return_json=False)
