"""Core logic for fetching and processing UniProt data."""

import json
import re
from typing import Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Session
from tqdm import tqdm

from . import config
from .api import UniprotAPI
from .models import (
    Protein,
    SearchTerm,
    SearchToProtein,
    create_tables,
    get_session,
)
from .utils import normalize_query

# Configure logging when module is imported
config.configure_logging()


def get_next_link(link_header: str) -> Optional[str]:
    """Extracts the 'next' link from the Link header."""
    if not link_header:
        return None
    match = re.search(r'<([^>]+)>; rel="next"', link_header)
    if match:
        return match.group(1)
    return None


def fetch_all_proteins(
    query: str, page_size: int = 100, save_path: str = None
) -> dict:
    """
    Fetch _all_ proteins matching `query` by following Link header pagination
    until exhausted. Optionally save the combined raw JSON.
    Returns a dict with:
      - "totalCount": int (estimated)
      - "proteins": list of protein objects
    """
    all_proteins = []
    
    api = UniprotAPI()
    
    # Initial request
    data, link_header = api.search_proteins(query, size=page_size)
    if not data:
        return {"proteins": []}

    results = data.get("results", [])
    all_proteins.extend(results)
    
    next_url = get_next_link(link_header)

    with tqdm(desc="Fetching protein pages", unit="page") as pbar:
        while next_url:
            pbar.update(1)
            # We use _make_request directly with the full URL from the Link header
            response = api._make_request(next_url)
            if not response:
                break
            
            data = response.json()
            results = data.get("results", [])
            all_proteins.extend(results)
            
            link_header = response.headers.get("Link")
            next_url = get_next_link(link_header)
            
            logger.info(f"Fetched {len(results)} proteins (total so far: {len(all_proteins)})")

    result = {"proteins": all_proteins}

    if save_path:
        with open(save_path, "w") as f:
            json.dump(result, f, indent=2)
        logger.info(f"🔖 All {len(all_proteins)} proteins saved to {save_path}")

    return result


def process_and_store_protein(session: Session, protein_data: Dict, search_term_id: int):
    """
    Processes a single UniProt protein entry and stores its normalized data
    into the database.
    """
    accession = protein_data.get("primaryAccession")
    if not accession:
        logger.warning("Skipping protein with no accession.")
        return

    entry_name = protein_data.get("uniProtkbId")
    
    # Extract protein name
    protein_desc = protein_data.get("proteinDescription", {})
    rec_name = protein_desc.get("recommendedName", {})
    protein_name = rec_name.get("fullName", {}).get("value")
    if not protein_name:
        # Fallback to submission names or alt names
        sub_names = protein_desc.get("submissionNames", [])
        if sub_names:
            protein_name = sub_names[0].get("fullName", {}).get("value")

    # Extract gene name
    genes = protein_data.get("genes", [])
    gene_name = None
    if genes:
        gene_name = genes[0].get("geneName", {}).get("value")

    # Extract organism
    organism = protein_data.get("organism", {})
    organism_name = organism.get("scientificName")
    organism_id = organism.get("taxonId")

    # Extract sequence info
    sequence_data = protein_data.get("sequence", {})
    sequence = sequence_data.get("value")
    length = sequence_data.get("length")
    mass = sequence_data.get("molWeight")

    protein = Protein(
        accession=accession,
        entry_name=entry_name,
        protein_name=protein_name,
        gene_name=gene_name,
        organism_name=organism_name,
        organism_id=organism_id,
        sequence=sequence,
        length=length,
        mass=mass,
    )
    session.merge(protein)
    session.merge(SearchToProtein(search_id=search_term_id, accession=accession))


def run_uniprot_query(query: str, max_records: int = 9999) -> int:
    """
    Main function to run a UniProt query, fetch data, and store it.
    Returns the number of new proteins downloaded.
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

        logger.info(f"Searching UniProt for query: '{query}'...")
        
        # We handle limiting manually if needed, but fetch_all matches structure
        # However, fetch_all might get HUGE data.
        # For now, let's just fetch up to max_records or so.
        # Actually fetch_all_proteins loops until exhaustion.
        # Let's modify fetch_all_proteins or just break early if we have enough.
        # But wait, clinical_trials fetch_all fetches EVERYTHING.
        # UniProt can return millions. I should probably be careful.
        # But the prompt says "refactor it to be more similar to the other modules".
        # clinical_trials `run_clinical_trials_query` calls `fetch_all_trials`.
        # And then slices `all_studies[:max_records]`.
        # This is inefficient for large datasets but follows the pattern.
        # I will keep it consistent with the request, but maybe add a check in the loop.
        
        data = fetch_all_proteins(query, page_size=config.CHUNK_SIZE)
        all_proteins = data["proteins"]
        count = len(all_proteins)

        if count == 0:
            logger.info("No proteins found for this query.")
            return 0

        logger.info(f"Found {count} proteins for this query.")

        if count > max_records:
            logger.warning(
                f"Query returned {count} results, but only processing the first {max_records} as requested."
            )
            all_proteins = all_proteins[:max_records]

        # Check existing
        accessions = [p["primaryAccession"] for p in all_proteins if "primaryAccession" in p]
        
        existing_accessions = {
            res[0]
            for res in session.query(Protein.accession)
            .filter(Protein.accession.in_(accessions))
            .all()
        }
        logger.info(
            f"Found {len(existing_accessions)} proteins already in the database."
        )

        for accession in existing_accessions:
            session.merge(SearchToProtein(search_id=search_term.id, accession=accession))
        session.commit()

        new_proteins = [
            p
            for p in all_proteins
            if "primaryAccession" in p
            and p["primaryAccession"] not in existing_accessions
        ]
        logger.info(f"🔍 Processing and storing {len(new_proteins)} new proteins...")

        if not new_proteins:
            logger.info("✅ All found proteins were already in the database.")
            return 0

        for protein_data in tqdm(new_proteins, desc="Storing Proteins"):
            process_and_store_protein(session, protein_data, search_term.id)

        session.commit()
        logger.info("✅ Download and processing complete.")
        return len(new_proteins)

    except Exception as e:
        logger.exception(f"An unexpected error occurred during the process: {e}")
        session.rollback()
        return 0
    finally:
        session.close()
        logger.info("Database session closed.")
