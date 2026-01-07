from typing import Optional, Dict, Any, List, Union
import time
import requests
from loguru import logger
from . import config

class ClinicalTrialsAPI:
    BASE_URL = config.API_BASE_URL

    def __init__(self):
        self.session = requests.Session()

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.BASE_URL}/{endpoint}"
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

    def list_studies(self, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Returns data of studies matching query and filter parameters.

        :param params: Dictionary of query parameters. Available parameters:
            - format (optional): Format of the response. Can be "csv" or "json". Default is "json".
            - markupFormat (optional): Format of markup fields. Can be "markdown" or "legacy". Default is "markdown".
            - query.cond (optional): Conditions or disease query.
            - query.term (optional): Other terms query.
            - query.locn (optional): Location terms query.
            - query.titles (optional): Title or acronym query.
            - query.intr (optional): Intervention or treatment query.
            - query.outc (optional): Outcome measure query.
            - query.spons (optional): Sponsor or collaborator query.
            - query.lead (optional): Lead sponsor name query.
            - query.id (optional): Study IDs query.
            - query.patient (optional): Patient search query.
            - filter.overallStatus (optional): Filter by list of statuses.
            - filter.geo (optional): Filter by geo-function.
            - filter.ids (optional): Filter by list of NCT IDs.
            - filter.advanced (optional): Filter by advanced query.
            - filter.synonyms (optional): Filter by list of synonyms.
            - postFilter.overallStatus (optional): Post filter by list of statuses.
            - postFilter.geo (optional): Post filter by geo-function.
            - postFilter.ids (optional): Post filter by list of NCT IDs.
            - postFilter.advanced (optional): Post filter by advanced query.
            - postFilter.synonyms (optional): Post filter by list of synonyms.
            - aggFilters (optional): Apply aggregation filters.
            - geoDecay (optional): Set proximity factor.
            - fields (optional): List of fields to return.
            - sort (optional): List of sorting options.
            - countTotal (optional): Count total number of studies.
            - pageSize (optional): Page size of the response. Default is 10.
            - pageToken (optional): Token to get the next page.
        
        :return: JSON response from the API.

        Example usage:
        api = ClinicalTrialsAPI()
        params = {
            "format": "json",
            "query.cond": "lung cancer"
        }
        studies = api.list_studies(params=params)
        print(studies)
        """
        return self._make_request("studies", params)

    def list_studies_paginated(self, params: Optional[Dict[str, Any]] = None, max_pages: Optional[int] = 10) -> List[Dict[str, Any]]:
        """
        Returns all studies matching the query and filter parameters, iterating through up to max_pages.

        :param params: Dictionary of query parameters.
        :param max_pages: Maximum number of pages to fetch. Default is 10. If None, fetches all pages.
        :return: List of all studies across pages.
        """
        if params is None:
            params = {}
        
        # Avoid modifying the original params dictionary
        current_params = params.copy()
        
        all_studies = []
        next_page_token = None
        page_count = 0

        while max_pages is None or page_count < max_pages:
            # Add the page token to the parameters if it exists
            if next_page_token:
                current_params["pageToken"] = next_page_token

            # Pass a copy to avoid mutation side-effects if the caller inspects history
            data = self._make_request("studies", current_params.copy())
            if not data:
                break
            
            # Collect studies from the current page
            if "studies" in data:
                all_studies.extend(data["studies"])
            
            # Check for the next page token
            next_page_token = data.get("nextPageToken")
            if not next_page_token:
                break  # Exit the loop when there are no more pages
            
            page_count += 1  # Increment the page count

        return all_studies


    def fetch_study(self, nctId: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Returns data of a single study.

        :param nctId: NCT Number of a study. Required.
        :param params: Dictionary of query parameters. Available parameters:
            - format (optional): Format of the response. Can be "csv", "json", "json.zip", "fhir.json", or "ris". Default is "json".
            - markupFormat (optional): Format of markup fields. Can be "markdown" or "legacy". Default is "markdown".
            - fields (optional): List of fields to return.
        
        :return: JSON response from the API.

        Example usage:
        api = ClinicalTrialsAPI()
        study = api.fetch_study("NCT03540771")
        print(study)
        """
        return self._make_request(f"studies/{nctId}", params)

    def studies_metadata(self, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Returns study data model fields.

        :param params: Dictionary of query parameters. Available parameters:
            - includeIndexedOnly (optional): Include indexed-only fields.
            - includeHistoricOnly (optional): Include fields available only in historic data.
        
        :return: JSON response from the API.

        Example usage:
        api = ClinicalTrialsAPI()
        metadata = api.studies_metadata()
        print(metadata)
        """
        return self._make_request("studies/metadata", params)

    def search_areas(self) -> Optional[Dict[str, Any]]:
        """
        Search Docs and their Search Areas.

        :return: JSON response from the API.

        Example usage:
        api = ClinicalTrialsAPI()
        search_areas = api.search_areas()
        print(search_areas)
        """
        return self._make_request("studies/search-areas")

    def enums(self) -> Optional[Dict[str, Any]]:
        """
        Returns enumeration types and their values.

        :return: JSON response from the API.

        Example usage:
        api = ClinicalTrialsAPI()
        enums = api.enums()
        print(enums)
        """
        return self._make_request("studies/enums")

    def size_stats(self) -> Optional[Dict[str, Any]]:
        """
        Statistics of study JSON sizes.

        :return: JSON response from the API.

        Example usage:
        api = ClinicalTrialsAPI()
        stats = api.size_stats()
        print(stats)
        """
        return self._make_request("stats/size")

    def field_values_stats(self, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Value statistics of the study leaf fields.

        :param params: Dictionary of query parameters. Available parameters:
            - types (optional): Filter by field types.
            - fields (optional): Filter by piece names or field paths of leaf fields.
        
        :return: JSON response from the API.

        Example usage:
        api = ClinicalTrialsAPI()
        params = {
            "types": ["ENUM", "BOOLEAN"]
        }
        stats = api.field_values_stats(params=params)
        print(stats)
        """
        return self._make_request("stats/field/values", params)

    def list_field_sizes_stats(self, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Sizes of list/array fields.

        :param params: Dictionary of query parameters. Available parameters:
            - fields (optional): Filter by piece names or field paths of leaf fields.
        
        :return: JSON response from the API.

        Example usage:
        api = ClinicalTrialsAPI()
        params = {
            "fields": ["Phase", "Condition"]
        }
        stats = api.list_field_sizes_stats(params=params)
        print(stats)
        """
        return self._make_request("stats/field/sizes", params)

    def version(self) -> Optional[Dict[str, Any]]:
        """
        API and data versions.

        :return: JSON response from the API.

        Example usage:
        api = ClinicalTrialsAPI()
        version_info = api.version()
        print(version_info)
        """
        return self._make_request("version")

    def list_endpoints(self) -> Dict[str, str]:
        """
        Lists all available endpoints for each method.

        :return: Dictionary with method names as keys and endpoint URLs as values.

        Example usage:
        api = ClinicalTrialsAPI()
        endpoints = api.list_endpoints()
        for method, endpoint in endpoints.items():
            print(f"{method}: {endpoint}")
        """
        endpoints = {
            "list_studies": f"{self.BASE_URL}/studies",
            "fetch_study": f"{self.BASE_URL}/studies/{{nctId}}",
            "studies_metadata": f"{self.BASE_URL}/studies/metadata",
            "search_areas": f"{self.BASE_URL}/studies/search-areas",
            "enums": f"{self.BASE_URL}/studies/enums",
            "size_stats": f"{self.BASE_URL}/stats/size",
            "field_values_stats": f"{self.BASE_URL}/stats/field/values",
            "list_field_sizes_stats": f"{self.BASE_URL}/stats/field/sizes",
            "version": f"{self.BASE_URL}/version",
        }
        return endpoints

    def list_parameters(self) -> Dict[str, List[Dict[str, Union[str, bool]]]]:
        """
        Lists all available parameters for each method, indicating whether they are optional or required.

        :return: Dictionary with method names as keys and list of parameters as values.

        Example usage:
        api = ClinicalTrialsAPI()
        parameters = api.list_parameters()
        for method, params in parameters.items():
            print(f"{method}: {params}")
        """
        parameters = {
            "list_studies": [
                {"name": "format", "required": False},
                {"name": "markupFormat", "required": False},
                {"name": "query.cond", "required": False},
                {"name": "query.term", "required": False},
                {"name": "query.locn", "required": False},
                {"name": "query.titles", "required": False},
                {"name": "query.intr", "required": False},
                {"name": "query.outc", "required": False},
                {"name": "query.spons", "required": False},
                {"name": "query.lead", "required": False},
                {"name": "query.id", "required": False},
                {"name": "query.patient", "required": False},
                {"name": "filter.overallStatus", "required": False},
                {"name": "filter.geo", "required": False},
                {"name": "filter.ids", "required": False},
                {"name": "filter.advanced", "required": False},
                {"name": "filter.synonyms", "required": False},
                {"name": "postFilter.overallStatus", "required": False},
                {"name": "postFilter.geo", "required": False},
                {"name": "postFilter.ids", "required": False},
                {"name": "postFilter.advanced", "required": False},
                {"name": "postFilter.synonyms", "required": False},
                {"name": "aggFilters", "required": False},
                {"name": "geoDecay", "required": False},
                {"name": "fields", "required": False},
                {"name": "sort", "required": False},
                {"name": "countTotal", "required": False},
                {"name": "pageSize", "required": False},
                {"name": "pageToken", "required": False}
            ],
            "fetch_study": [
                {"name": "nctId", "required": True},
                {"name": "format", "required": False},
                {"name": "markupFormat", "required": False},
                {"name": "fields", "required": False}
            ],
            "studies_metadata": [
                {"name": "includeIndexedOnly", "required": False},
                {"name": "includeHistoricOnly", "required": False}
            ],
            "field_values_stats": [
                {"name": "types", "required": False},
                {"name": "fields", "required": False}
            ],
            "list_field_sizes_stats": [
                {"name": "fields", "required": False}
            ],
            "version": []
        }
        return parameters
    
    def print_dict_recursively(self, d, indent=0):
        """
        Recursively print a dictionary with each key-value pair on a new line.
        
        :param d: The dictionary to print.
        :param indent: The current level of indentation (used for nested dictionaries).
        """
        for key, value in d.items():
            print(' ' * indent + f"{key}: ", end='')
            if isinstance(value, dict):
                print()  # Move to a new line for nested dictionaries
                self.print_dict_recursively(value, indent + 4)
            elif isinstance(value, list):
                print("[")
                for item in value:
                    if isinstance(item, dict):
                        print(' ' * (indent + 4) + "{")
                        self.print_dict_recursively(item, indent + 8)
                        print(' ' * (indent + 4) + "},")
                    else:
                        print(' ' * (indent + 4) + f"{item},")
                print(' ' * indent + "]")
            else:
                print(value)
