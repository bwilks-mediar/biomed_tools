"""Core logic for fetching and processing RxNav data."""

import json
from datetime import datetime
from typing import Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Session
from tqdm import tqdm

from . import config
from .api import RxNavAPI
from .models import (
    Drug,
    Class,
    DrugClass,
    SearchTerm,
    SearchToDrug,
    create_tables,
    get_session,
)
from .utils import normalize_query

# Configure logging when module is imported
config.configure_logging()

def process_and_store_drug(session: Session, drug_name: str, rxcui: str, search_term_id: int):
    """
    Processes a single drug and stores its data into the database.
    """
    # Store Drug
    drug = session.query(Drug).filter_by(rxcui=rxcui).first()
    if not drug:
        drug = Drug(rxcui=rxcui, name=drug_name)
        session.add(drug)
        session.flush()
    else:
        # Update name if it was missing or different (though rxcui is the stable identifier)
        if not drug.name:
            drug.name = drug_name
            session.merge(drug)
    
    # Link Search to Drug
    session.merge(SearchToDrug(search_id=search_term_id, drug_id=drug.id))
    
    api = RxNavAPI()
    
    # Fetch Classes (MoA, EPC, PE, etc.)
    # We query for 'all' relationships if possible, or specific ones. 
    # RxClass API allows getting classes by RxCUI. 
    # If we don't specify rela, it might return all? 
    # The API method definition in api.py takes rela.
    # Let's try iterating over common relationships or assume 'all' works if supported by API wrapper logic 
    # (though my wrapper simply passes it).
    # Actually, the RxClass API documentation suggests fetching by RxCUI returns classes connected by any relation 
    # if not filtered, but the wrapper code passed `relas` param.
    # Let's try fetching "has_MoA" and "has_EPC" specifically as they are most common.
    
    relationships = ["has_MoA", "has_EPC", "may_treat", "may_prevent"]
    
    for rela in relationships:
        classes_info = api.get_class_by_rxcui(rxcui, rela)
        if classes_info:
            for info in classes_info:
                concept = info.get('rxclassMinConceptItem', {})
                class_id = concept.get('classId')
                class_name = concept.get('className')
                class_type = concept.get('classType')
                
                if class_id:
                    # Store Class
                    cls = session.query(Class).filter_by(class_id=class_id).first()
                    if not cls:
                        cls = Class(class_id=class_id, name=class_name, type=class_type)
                        session.add(cls)
                        session.flush()
                    
                    # Link Drug to Class
                    session.merge(DrugClass(
                        drug_id=drug.id,
                        class_id=cls.id,
                        relation_type=rela
                    ))

def run_rxnav_query(query: str) -> int:
    """
    Main function to run a RxNav query, fetch data, and store it.
    Returns 1 if drug found, 0 otherwise.
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

        logger.info(f"Searching RxNav for drug: '{query}'...")
        
        api = RxNavAPI()
        rxcui = api.get_rxnorm_id(query)
        
        if not rxcui:
            logger.warning(f"No RxNorm ID found for drug: '{query}'")
            return 0
            
        logger.info(f"Found RxNorm ID: {rxcui}")
        
        process_and_store_drug(session, query, rxcui, search_term.id)
        
        session.commit()
        logger.info("✅ Download and processing complete.")
        return 1

    except Exception as e:
        logger.exception(f"An unexpected error occurred during the process: {e}")
        session.rollback()
        return 0
    finally:
        session.close()
        logger.info("Database session closed.")
