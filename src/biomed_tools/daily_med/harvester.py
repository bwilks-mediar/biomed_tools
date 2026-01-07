"""Core logic for fetching and processing DailyMed data."""

from loguru import logger
from sqlalchemy.orm import Session
from tqdm import tqdm

from . import config
from .api import DailyMedApi
from .models import (
    Drug,
    SearchTerm,
    create_tables,
    get_session,
)
from .utils import normalize_query

# Configure logging when module is imported
config.configure_logging()

def process_and_store_drug(session: Session, drug_data: dict):
    """
    Processes a single drug entry and stores it into the database.
    """
    set_id = drug_data.get("setid")
    # 'title' seems to be the name in spls.json response
    drug_name = drug_data.get("title") or drug_data.get("drug_name")
    
    if not set_id:
        return

    drug = Drug(
        set_id=set_id,
        drug_name=drug_name,
        spl_version=drug_data.get("spl_version"),
        published_date=drug_data.get("published_date"),
    )
    session.merge(drug)

def fetch_all_spls(api: DailyMedApi, query: str, page_size: int = 100) -> list:
    """
    Fetch all SPLs matching the query by paginating.
    """
    all_spls = []
    page = 1
    total_pages = 1
    
    with tqdm(desc="Fetching pages", unit="page") as pbar:
        while page <= total_pages:
            result = api.search_spls(query, page=page, page_size=page_size)
            if not result or "data" not in result:
                break
            
            data = result["data"]
            all_spls.extend(data)
            
            metadata = result.get("metadata", {})
            total_pages = metadata.get("total_pages", 0)
            
            # Update pbar total if it's the first page
            if page == 1:
                pbar.total = total_pages
            
            pbar.update(1)
            page += 1
            
    return all_spls

def run_daily_med_query(query: str) -> int:
    """
    Main function to run a DailyMed query, fetch data, and store it.
    Returns the number of drugs found/updated.
    """
    create_tables()
    session = get_session()
    api = DailyMedApi()

    try:
        norm_query = normalize_query(query)
        search_term = session.query(SearchTerm).filter_by(term=norm_query).first()
        if not search_term:
            logger.info(f"Creating new search entry for query: '{query}'")
            search_term = SearchTerm(term=norm_query)
            session.add(search_term)
            session.commit()
        else:
            logger.info(f"Using existing search entry for query: '{query}'")

        logger.info(f"Searching DailyMed SPLs for query: '{query}'...")
        
        # Use fetch_all_spls to get all results
        drugs = fetch_all_spls(api, query)
        
        count = len(drugs)
        if count == 0:
            logger.info("No drugs found for this query.")
            return 0

        logger.info(f"Found {count} drugs/SPLs for this query.")

        for drug_data in tqdm(drugs, desc="Storing Drugs"):
            process_and_store_drug(session, drug_data)

        session.commit()
        logger.info("✅ Download and processing complete.")
        return count

    except Exception as e:
        logger.exception(f"An unexpected error occurred during the process: {e}")
        session.rollback()
        return 0
    finally:
        session.close()
        logger.info("Database session closed.")
