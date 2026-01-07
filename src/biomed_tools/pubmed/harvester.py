"""Core logic for fetching and processing PubMed data."""

from typing import Any, Dict, Optional

from Bio import Entrez, Medline
from loguru import logger
from tqdm import tqdm

from ..pubmed import config
from ..pubmed.models import (
    Publication,
    SearchTerm,
    SearchToPublication,
    create_tables,
    get_session,
)
from ..pubmed.api import fetch_full_text, safe_entrez_request
from ..pubmed.utils import normalize_query, parse_pub_date

# Configure logging when module is imported
config.configure_logging()


def process_medline_record(
    record: Dict[str, Any], fetch_text: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Parses a Bio.Medline record into a structured dictionary for our DB model.
    Extracts additional fields like DOI.
    """
    pmid = record.get("PMID")
    if not pmid:
        logger.warning("Skipping record with no PMID.")
        return None

    # Extract PMCID and DOI from the 'AID' field
    pmcid = record.get("PMC")
    doi = None
    if "AID" in record:
        for aid in record["AID"]:
            if "[pmcid]" in aid and not pmcid:
                pmcid = aid.split(" ")[0]
            elif "[doi]" in aid:
                doi = aid.split(" ")[0]

    publication_data = {
        "pmid": pmid,
        "pmcid": pmcid,
        "doi": doi,
        "title": record.get("TI", "No Title Available"),
        "abstract": record.get("AB"),
        "authors": record.get("AU"),
        "affiliations": record.get("AD"),
        "journal": record.get("JT"),
        "pub_date": parse_pub_date(record.get("DP", "")),
        "publication_type": record.get("PT"),
        "language": record.get("LA"),
        "copyright_information": (
            " ".join(record.get("CI")) if isinstance(record.get("CI"), list) else record.get("CI")
        ),
        "mesh_terms": record.get("MH"),
        "keywords": record.get("OT"),
    }

    if fetch_text and pmcid:
        publication_data["full_text"] = fetch_full_text(pmcid)

    return publication_data


def run_pubmed_query(
    query: str,
    max_records: int = 10000,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fetch_text: bool = False,
    esearch_rettype: str = "uilist",
    esearch_retmode: str = "xml",
    sort: str = "relevance",
    field: Optional[str] = None,
    idtype: Optional[str] = None,
    datetype: str = "pdat",
    reldate: Optional[int] = None,
    mindate: Optional[str] = None,
    maxdate: Optional[str] = None,
    efetch_rettype: str = "medline",
    efetch_retmode: str = "text",
    strand: Optional[str] = None,
    seq_start: Optional[int] = None,
    seq_stop: Optional[int] = None,
    complexity: Optional[int] = None,
) -> int:
    """
    Main function to run a PubMed query, fetch data, and store it in the database.
    Returns the number of new articles downloaded.
    """
    create_tables()
    session = get_session()

    try:
        norm_query = normalize_query(query)
        search_term = session.query(SearchTerm).filter_by(term=norm_query).first()
        if not search_term:
            logger.info(f"Creating new search entry for query: '{query}'")
            search_term = SearchTerm(term=norm_query)
            session.add(search_term)
            session.commit()
        else:
            logger.info(f"✔️ Using existing search entry for query: '{query}'")

        search_term_suffix = ""
        if start_date and end_date:
            search_term_suffix = f" AND ({start_date}[Date - Publication] : {end_date}[Date - Publication])"
        full_query = query + search_term_suffix

        logger.info(f"Searching PubMed for query: '{full_query}'...")
        # ESearch to get total count and history server details
        esearch_params = {
            "db": "pubmed",
            "term": full_query,
            "usehistory": "y",
            "retmax": max_records,
            "rettype": esearch_rettype,
            "retmode": esearch_retmode,
            "sort": sort,
            "datetype": datetype,
        }
        if field:
            esearch_params["field"] = field
        if idtype:
            esearch_params["idtype"] = idtype
        if reldate:
            esearch_params["reldate"] = reldate
        if mindate and maxdate:
            esearch_params["mindate"] = mindate
            esearch_params["maxdate"] = maxdate

        search_handle = safe_entrez_request(Entrez.esearch, **esearch_params)
        search_results = Entrez.read(search_handle)
        search_handle.close()

        count = int(search_results["Count"])
        if count == 0:
            logger.info("No new articles found for this query.")
            return 0

        logger.info(f"Found {count} articles for this query.")
        # Respect the max_records limit and PubMed's limit of 9999
        if count > 9999:
            logger.warning(
                f"Query returned {count} results, but PubMed only allows fetching the first 9999. "
                "Consider using a more specific query or date ranges to retrieve all results."
            )
            count = 9999
        elif count > max_records:
            logger.warning(
                f"Query returned {count} results, but only fetching the first {max_records} as requested."
            )
            count = max_records

        # Fetch all PMIDs using the history server
        pmid_list = search_results["IdList"]
        webenv = search_results["WebEnv"]
        query_key = search_results["QueryKey"]

        # Fetch remaining PMIDs if necessary
        if len(pmid_list) < count:
            for start in range(len(pmid_list), count, config.CHUNK_SIZE):
                handle = safe_entrez_request(
                    Entrez.esearch,
                    db="pubmed",
                    term=full_query,
                    retstart=start,
                    retmax=config.CHUNK_SIZE,
                    webenv=webenv,
                    query_key=query_key,
                )
                record = Entrez.read(handle)
                handle.close()
                pmid_list.extend(record["IdList"])

        existing_pmids = {
            res[0]
            for res in session.query(Publication.pmid)
            .filter(Publication.pmid.in_(pmid_list))
            .all()
        }
        logger.info(f"Found {len(existing_pmids)} articles already in the database by PMID.")

        new_pmids = [pmid for pmid in pmid_list if pmid not in existing_pmids]
        logger.info(f"🔍 Downloading {len(new_pmids)} new articles...")

        if not new_pmids:
            logger.info("✅ All found articles were already in the database.")
            return 0

        new_articles_count = 0
        with tqdm(total=len(new_pmids), desc="Fetching Articles") as pbar:
            for i in range(0, len(new_pmids), config.CHUNK_SIZE):
                chunk = new_pmids[i : i + config.CHUNK_SIZE]
                handle = safe_entrez_request(
                    Entrez.efetch,
                    db="pubmed",
                    id=chunk,
                    rettype="medline",
                    retmode="text",
                )
                medline_records = Medline.parse(handle)

                for rec in medline_records:
                    pub_data = process_medline_record(rec, fetch_text=fetch_text)
                    if pub_data:
                        # Check for existing publication by DOI
                        if pub_data.get("doi"):
                            existing_pub = (
                                session.query(Publication)
                                .filter_by(doi=pub_data["doi"])
                                .first()
                            )
                            if existing_pub:
                                # If it exists, merge the new data into it
                                for key, value in pub_data.items():
                                    if value:
                                        setattr(existing_pub, key, value)
                                session.merge(existing_pub)
                                session.merge(
                                    SearchToPublication(
                                        search_id=search_term.id,
                                        pmid=existing_pub.pmid,
                                    )
                                )
                                continue

                        # If it doesn't exist, create a new one
                        publication = Publication(**pub_data)
                        session.merge(publication)
                        session.merge(
                            SearchToPublication(
                                search_id=search_term.id, pmid=pub_data["pmid"]
                            )
                        )
                        new_articles_count += 1
                session.commit()
                pbar.update(len(chunk))

        logger.info("✅ Download and processing complete.")
        return new_articles_count
    except Exception as e:
        logger.exception(f"An unexpected error occurred during the process: {e}")
        session.rollback()
        return 0
    finally:
        session.close()
        logger.info("Database session closed.")




def harvest_large_query(
    query: str, start_year: int, end_year: int, fetch_text: bool = False
) -> None:
    """
    Harvests a large query by splitting it into yearly chunks.
    """
    total_downloaded = 0
    for year in range(start_year, end_year + 1):
        logger.info(f"--- Harvesting data for year {year} ---")
        start_date = f"{year}/01/01"
        end_date = f"{year}/12/31"
        downloaded_this_year = run_pubmed_query(
            query, start_date=start_date, end_date=end_date, fetch_text=fetch_text
        )
        total_downloaded += downloaded_this_year
        logger.info(
            f"Downloaded {downloaded_this_year} new articles for {year}. Total downloaded: {total_downloaded}"
        )
    logger.info(
        f"🎉 Finished harvesting all years. Total new articles: {total_downloaded}"
    )


def download_by_pmids(
    pmids: list[str],
    fetch_text: bool = False,
    search_term: str = "Manually Added by PMID",
) -> int:
    """
    Downloads articles from a list of PMIDs.
    """
    create_tables()
    session = get_session()
    try:
        # Get or create the search term
        norm_query = normalize_query(search_term)
        search_term_obj = session.query(SearchTerm).filter_by(term=norm_query).first()
        if not search_term_obj:
            search_term_obj = SearchTerm(term=norm_query)
            session.add(search_term_obj)
            session.commit()

        existing_pmids = {
            res[0]
            for res in session.query(Publication.pmid)
            .filter(Publication.pmid.in_(pmids))
            .all()
        }
        logger.info(f"Found {len(existing_pmids)} articles already in the database by PMID.")

        new_pmids = [pmid for pmid in pmids if pmid not in existing_pmids]
        logger.info(f"🔍 Downloading {len(new_pmids)} new articles...")

        if not new_pmids:
            logger.info("✅ All found articles were already in the database.")
            return 0

        new_articles_count = 0
        with tqdm(total=len(new_pmids), desc="Fetching Articles") as pbar:
            for i in range(0, len(new_pmids), config.CHUNK_SIZE):
                chunk = new_pmids[i : i + config.CHUNK_SIZE]
                handle = safe_entrez_request(
                    Entrez.efetch,
                    db="pubmed",
                    id=chunk,
                    rettype="medline",
                    retmode="text",
                )
                medline_records = Medline.parse(handle)

                for rec in medline_records:
                    pub_data = process_medline_record(rec, fetch_text=fetch_text)
                    if pub_data:
                        # Check for existing publication by DOI
                        if pub_data.get("doi"):
                            existing_pub = (
                                session.query(Publication)
                                .filter_by(doi=pub_data["doi"])
                                .first()
                            )
                            if existing_pub:
                                # If it exists, merge the new data into it
                                for key, value in pub_data.items():
                                    if value:
                                        setattr(existing_pub, key, value)
                                session.merge(existing_pub)
                                session.merge(
                                    SearchToPublication(
                                        search_id=search_term_obj.id,
                                        pmid=existing_pub.pmid,
                                    )
                                )
                                continue

                        # If it doesn't exist, create a new one
                        publication = Publication(**pub_data)
                        session.merge(publication)
                        session.merge(
                            SearchToPublication(
                                search_id=search_term_obj.id, pmid=pub_data["pmid"]
                            )
                        )
                        new_articles_count += 1
                session.commit()
                pbar.update(len(chunk))

        logger.info("✅ Download and processing complete.")
        return new_articles_count
    except Exception as e:
        logger.exception(f"An unexpected error occurred during the process: {e}")
        session.rollback()
        return 0
    finally:
        session.close()
        logger.info("Database session closed.")


def download_full_text_for_existing_articles(
    batch_size: int = 200, recheck_days: int = 30
) -> None:
    """
    Downloads full text for articles that have a PMCID but no full text yet.
    """
    session = get_session()
    from datetime import datetime, timedelta

    try:
        while True:
            recheck_threshold = datetime.utcnow() - timedelta(days=recheck_days)
            articles_to_update = (
                session.query(Publication)
                .filter(
                    Publication.pmcid.isnot(None),
                    Publication.full_text.is_(None),
                    (
                        Publication.full_text_last_checked.is_(None)
                        | (Publication.full_text_last_checked < recheck_threshold)
                    ),
                )
                .limit(batch_size)
                .all()
            )

            if not articles_to_update:
                logger.info("No more articles to update with full text.")
                break

            logger.info(f"Found {len(articles_to_update)} articles to update.")
            for article in tqdm(articles_to_update, desc="Downloading Full Text"):
                article.full_text = fetch_full_text(article.pmcid)
                article.full_text_last_checked = datetime.utcnow()
            session.commit()
            logger.info(f"Updated {len(articles_to_update)} articles.")

    except Exception as e:
        logger.exception(f"An error occurred during full text download: {e}")
        session.rollback()
    finally:
        session.close()
