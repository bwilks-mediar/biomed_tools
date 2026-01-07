"""API wrapper for PubMed interactions."""

import random
import time
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

import httpx
from Bio import Entrez
from loguru import logger

from ..pubmed.config import (
    API_KEY,
    ENTREZ_EMAIL,
    MAX_RETRIES,
    REQUEST_DELAY,
    RETRY_BACKOFF,
    TOOL_NAME,
)


def safe_entrez_request(func, *args, **kwargs):
    """
    Wrapper for Entrez calls to handle transient network errors with exponential backoff.
    Includes tool name and API key in requests for better compliance and higher rate limits.
    """
    Entrez.email = ENTREZ_EMAIL
    Entrez.tool = TOOL_NAME
    if API_KEY:
        Entrez.api_key = API_KEY

    for attempt in range(MAX_RETRIES):
        try:
            # Add a delay before each request to respect rate limits
            time.sleep(REQUEST_DELAY)
            return func(*args, **kwargs)
        except Exception as e:
            # For HTTP 429 or 403, use a longer, more specific backoff
            if "429" in str(e) or "403" in str(e):
                wait_time = 20 + random.uniform(0, 5)
                logger.warning(
                    f"Rate limit error ({str(e)[:15]}) (Attempt {attempt + 1}/{MAX_RETRIES}). "
                    f"Retrying in {wait_time:.2f} seconds..."
                )
            else:
                wait_time = RETRY_BACKOFF**attempt + random.uniform(0, 1)
                logger.warning(
                    f"Entrez request failed (Attempt {attempt + 1}/{MAX_RETRIES}): {e}. "
                    f"Retrying in {wait_time:.2f} seconds..."
                )
            time.sleep(wait_time)
    logger.error(f"Entrez request failed definitively after {MAX_RETRIES} attempts.")
    raise RuntimeError(f"Entrez request failed after {MAX_RETRIES} attempts.")


def fetch_full_text(pmcid: str) -> Optional[str]:
    """Fetches and extracts the body text from a PMC article XML."""
    logger.debug(f"Fetching full text for PMCID: {pmcid}")
    try:
        handle = safe_entrez_request(
            Entrez.efetch, db="pmc", id=pmcid, rettype="xml", retmode="xml"
        )
        xml_content = handle.read()
        handle.close()

        if not xml_content:
            logger.warning(f"No XML content returned for PMCID: {pmcid}")
            return None

        root = ET.fromstring(xml_content)
        body_text = "\n".join(p.text for p in root.findall(".//body//p") if p.text)
        return body_text if body_text else None
    except ET.ParseError as e:
        logger.error(f"XML Parse Error for PMCID {pmcid}: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to fetch or parse full text for PMCID {pmcid}: {e}")
        return None


def fetch_publication_details_from_pubmed(pmids: List[str]) -> Dict:
    """
    Fetches publication details from PubMed's E-utilities API.
    See: https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.ESummary
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    data = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "json",
        "tool": "pubmed_miner",
        "email": ENTREZ_EMAIL,
    }
    try:
        # Use POST to handle large number of PMIDs
        response = httpx.post(base_url, data=data)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e}")
        return {}
    except httpx.RequestError as e:
        print(f"An error occurred while requesting from E-utilities: {e}")
        return {}
