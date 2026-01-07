"""Update existing database records with additional information from PubMed."""

import re
import time
from typing import List

from sqlalchemy.orm import Session

from ..pubmed.api import fetch_publication_details_from_pubmed
from ..pubmed.models import Publication, get_session


def update_publications_from_pubmed(
    session: Session, publications: List[Publication]
) -> None:
    """
    Updates a list of Publication objects with details from PubMed.
    """
    pmids = [p.pmid for p in publications]
    if not pmids:
        return

    data = fetch_publication_details_from_pubmed(pmids)
    if not data or "result" not in data:
        return

    for pmid, details in data["result"].items():
        if pmid == "uids":
            continue
        for pub in publications:
            if pub.pmid == pmid:
                # Extract PMCID and DOI if available
                if "articleids" in details:
                    for article_id in details["articleids"]:
                        if article_id.get("idtype") == "pmcid":
                            pmcid_value = article_id.get("value")
                            if pmcid_value:
                                match = re.search(r'PMC(\d+)', pmcid_value)
                                if match:
                                    pub.pmcid = match.group(0)
                                else:
                                    # Fallback for IDs that are just numbers
                                    numeric_match = re.search(r'(\d+)', pmcid_value)
                                    if numeric_match:
                                        pub.pmcid = f"PMC{numeric_match.group(0)}"
                        elif article_id.get("idtype") == "doi":
                            doi_value = article_id.get("value")
                            if doi_value:
                                # Check if the DOI already exists in the database
                                existing_pub_with_doi = (
                                    session.query(Publication)
                                    .filter_by(doi=doi_value)
                                    .first()
                                )
                                if existing_pub_with_doi and existing_pub_with_doi.pmid != pub.pmid:
                                    print(
                                        f"Warning: DOI {doi_value} already exists for PMID {existing_pub_with_doi.pmid}. "
                                        f"Skipping update for PMID {pub.pmid}."
                                    )
                                else:
                                    pub.doi = doi_value
                break
    session.commit()


def find_and_update_missing_identifiers(
    rate_limit: int = 3, batch_size: int = 200, recheck_days: int = 30
) -> None:
    """
    Finds publications with missing PMCID or DOI and updates them from PubMed.
    """
    session = get_session()
    from datetime import datetime, timedelta

    while True:
        recheck_threshold = datetime.utcnow() - timedelta(days=recheck_days)
        publications_to_update = (
            session.query(Publication)
            .filter(
                (Publication.pmcid.is_(None) | Publication.doi.is_(None))
                & (
                    Publication.last_checked.is_(None)
                    | (Publication.last_checked < recheck_threshold)
                )
            )
            .limit(batch_size)
            .all()
        )

        if not publications_to_update:
            print("No more publications to update at this time.")
            break

        print(f"Found {len(publications_to_update)} publications to update.")
        for pub in publications_to_update:
            pub.last_checked = datetime.utcnow()
        session.commit()

        update_publications_from_pubmed(session, publications_to_update)
        print(f"Updated {len(publications_to_update)} publications.")

        # Respect the rate limit
        time.sleep(1 / rate_limit)

    session.close()
