from typing import Optional, List, Dict, Any, Union
import time
import requests
from loguru import logger
from . import config

class RxNavAPI:
    BASE_URL = config.API_BASE_URL

    def __init__(self):
        self.session = requests.Session()

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.BASE_URL}/{endpoint}"
        for attempt in range(config.MAX_RETRIES):
            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()
                # RxNav API can return JSON or XML depending on headers/extension. 
                # The original code used .json endpoints.
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{config.MAX_RETRIES}): {e}")
                if attempt < config.MAX_RETRIES - 1:
                    time.sleep(config.RETRY_BACKOFF**attempt)
                else:
                    logger.error(f"Failed to fetch data from {url} after {config.MAX_RETRIES} attempts.")
                    return None

    def get_rxnorm_id(self, drug_name: str) -> Optional[str]:
        """
        Get the RxNorm ID for a given drug name.
        """
        data = self._make_request("rxcui.json", params={"name": drug_name})
        if data:
            id_group = data.get('idGroup')
            if id_group and 'rxnormId' in id_group:
                return id_group.get('rxnormId')[0]
        return None

    def get_moa(self, rxcui: str) -> Optional[List[str]]:
        """
        Get the mechanism of action (MoA) for a given RxNorm ID (RxCUI).
        """
        params = {"rxcui": rxcui, "relas": "has_MoA"}
        data = self._make_request("rxclass/class/byRxcui.json", params=params)
        if data and 'rxclassDrugInfoList' in data:
            class_info = data['rxclassDrugInfoList']['rxclassDrugInfo']
            return [info['rxclassMinConceptItem']['className'] for info in class_info]
        return None

    def get_class_members(self, class_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get class members for a given class ID.
        """
        params = {"classId": class_id}
        data = self._make_request("rxclass/classMembers.json", params=params)
        if data and 'drugMemberGroup' in data:
            return data['drugMemberGroup']['drugMember']
        return None

    def get_all_classes(self, class_type: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get all classes of a specified type.
        """
        params = {"classTypes": class_type}
        data = self._make_request("rxclass/allClasses.json", params=params)
        if data and 'rxclassMinConceptList' in data:
            return data['rxclassMinConceptList']['rxclassMinConcept']
        return None

    def get_related_classes(self, class_id: str, rela: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get related classes for a given class ID and relationship.
        """
        params = {"classId": class_id, "relaSource": "rxclass", "relas": rela}
        data = self._make_request("rxclass/related.json", params=params)
        if data and 'relatedDrugClass' in data:
            return data['relatedDrugClass']['rxclassMinConceptItem']
        return None

    def get_class_by_rxcui(self, rxcui: str, rela: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get drug classes by RxNorm ID and relationship.
        """
        params = {"rxcui": rxcui, "relas": rela}
        data = self._make_request("rxclass/class/byRxcui.json", params=params)
        if data and 'rxclassDrugInfoList' in data:
            return data['rxclassDrugInfoList']['rxclassDrugInfo']
        return None

    def get_class_by_name(self, class_name: str, class_type: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get drug classes by class name and type.
        """
        params = {"className": class_name, "classTypes": class_type}
        data = self._make_request("rxclass/class/byName.json", params=params)
        if data and 'rxclassMinConceptList' in data:
            return data['rxclassMinConceptList']['rxclassMinConcept']
        return None

    def get_approx_class_members(self, rxcui: str, rela: str = 'all') -> Optional[List[Dict[str, Any]]]:
        """
        Get approximate class members by RxNorm ID and relationship.
        """
        params = {"rxcui": rxcui, "relas": rela}
        data = self._make_request("rxclass/class/approxMembers.json", params=params)
        if data and 'approximateClassGroup' in data:
            return data['approximateClassGroup']['approximateClass']
        return None

    def get_class_contexts(self, class_id: str) -> Optional[Dict[str, Any]]:
        """
        Get class contexts for a given class ID.
        """
        params = {"classId": class_id}
        data = self._make_request("rxclass/classContext.json", params=params)
        return data
