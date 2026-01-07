"""Core logic for fetching and processing OpenFDA data."""

import json
from typing import Dict, List, Optional, Callable
from loguru import logger
from sqlalchemy.orm import Session
from tqdm import tqdm

from . import config
from .api import OpenFDAAPI
from .models import (
    DrugEvent, DrugEventDrug, DrugEventReaction, SearchToEvent,
    DrugLabel, SearchToLabel,
    DrugNDC, SearchToNDC,
    DrugEnforcement, SearchToEnforcement,
    DrugAtFDA, SearchToDrugsFDA,
    SearchTerm, create_tables, get_session,
)
from .utils import normalize_query

config.configure_logging()

def fetch_records(api_method: Callable, query: str, max_records: int) -> List[Dict]:
    """
    Generic fetch loop for OpenFDA endpoints.
    """
    all_records = []
    limit = config.CHUNK_SIZE
    skip = 0
    
    if max_records > 5000:
        logger.warning("OpenFDA API pagination limit is typically 5000 records via skip parameter. Capping request.")
        max_records = 5000

    total_fetched = 0
    
    with tqdm(total=max_records, desc="Fetching records", unit="rec") as pbar:
        while total_fetched < max_records:
            current_limit = min(limit, max_records - total_fetched)
            # Call the bound method
            data = api_method(query, limit=current_limit, skip=skip)
            
            if not data or "results" not in data:
                break
                
            records = data["results"]
            all_records.extend(records)
            count = len(records)
            total_fetched += count
            skip += count
            pbar.update(count)
            
            if count < current_limit:
                break
                
    return all_records

def process_event(session: Session, event_data: Dict, search_id: int):
    safetyreportid = event_data.get("safetyreportid")
    if not safetyreportid: return

    patient = event_data.get("patient", {})
    
    drug_event = DrugEvent(
        safetyreportid=safetyreportid,
        receivedate=event_data.get("receivedate"),
        serious=str(event_data.get("serious")),
        seriousnessdeath=str(event_data.get("seriousnessdeath")),
        seriousnesshospitalization=str(event_data.get("seriousnesshospitalization")),
        patient_onsetage=str(patient.get("patientonsetage")),
        patient_onsetageunit=str(patient.get("patientonsetageunit")),
        patient_sex=str(patient.get("patientsex")),
        patient_weight=str(patient.get("patientweight")),
        data=event_data
    )
    session.merge(drug_event)
    
    # Drugs
    session.query(DrugEventDrug).filter_by(safetyreportid=safetyreportid).delete()
    for drug_data in patient.get("drug", []):
        openfda = drug_data.get("openfda", {})
        drug_entry = DrugEventDrug(
            safetyreportid=safetyreportid,
            medicinalproduct=drug_data.get("medicinalproduct"),
            drugcharacterization=str(drug_data.get("drugcharacterization")),
            drugindication=drug_data.get("drugindication"),
            brand_name="|".join(openfda.get("brand_name", [])),
            generic_name="|".join(openfda.get("generic_name", [])),
            substance_name="|".join(openfda.get("substance_name", [])),
            manufacturer_name="|".join(openfda.get("manufacturer_name", [])),
        )
        session.add(drug_entry)

    # Reactions
    session.query(DrugEventReaction).filter_by(safetyreportid=safetyreportid).delete()
    for reaction_data in patient.get("reaction", []):
        reaction_entry = DrugEventReaction(
            safetyreportid=safetyreportid,
            reactionmeddrapt=reaction_data.get("reactionmeddrapt"),
            reactionoutcome=str(reaction_data.get("reactionoutcome")),
        )
        session.add(reaction_entry)
        
    session.merge(SearchToEvent(search_id=search_id, safetyreportid=safetyreportid))

def process_label(session: Session, data: Dict, search_id: int):
    # ID is usually id or set_id. The docs say 'id' is unique for the document version.
    label_id = data.get("id")
    if not label_id:
        label_id = data.get("set_id")
    if not label_id: return
    
    openfda = data.get("openfda", {})
    label = DrugLabel(
        id=label_id,
        set_id=data.get("set_id", ""),
        spl_id=data.get("spl_id"),
        brand_name="|".join(openfda.get("brand_name", [])),
        generic_name="|".join(openfda.get("generic_name", [])),
        manufacturer_name="|".join(openfda.get("manufacturer_name", [])),
        effective_time=data.get("effective_time"),
        data=data
    )
    session.merge(label)
    session.merge(SearchToLabel(search_id=search_id, label_id=label_id))

def process_ndc(session: Session, data: Dict, search_id: int):
    pid = data.get("product_id")
    if not pid: return
    
    ndc = DrugNDC(
        product_id=pid,
        product_ndc=data.get("product_ndc"),
        brand_name=data.get("brand_name"),
        generic_name=data.get("generic_name"),
        labeler_name=data.get("labeler_name"),
        finished=data.get("finished"),
        dea_schedule=data.get("dea_schedule"),
        data=data
    )
    session.merge(ndc)
    session.merge(SearchToNDC(search_id=search_id, ndc_id=pid))

def process_enforcement(session: Session, data: Dict, search_id: int):
    rid = data.get("recall_number")
    if not rid: return
    
    enf = DrugEnforcement(
        recall_number=rid,
        reason_for_recall=data.get("reason_for_recall"),
        status=data.get("status"),
        distribution_pattern=data.get("distribution_pattern"),
        product_description=data.get("product_description"),
        recall_initiation_date=data.get("recall_initiation_date"),
        data=data
    )
    session.merge(enf)
    session.merge(SearchToEnforcement(search_id=search_id, recall_number=rid))

def process_drugsfda(session: Session, data: Dict, search_id: int):
    app_num = data.get("application_number")
    if not app_num: return
    
    da = DrugAtFDA(
        application_number=app_num,
        sponsor_name=data.get("sponsor_name"),
        products=data.get("products", []),
        data=data
    )
    session.merge(da)
    session.merge(SearchToDrugsFDA(search_id=search_id, app_num=app_num))

def run_openfda_query(query: str, endpoint: str = "event", max_records: int = 100) -> int:
    """
    Main function to run an OpenFDA query.
    endpoint: 'event', 'label', 'ndc', 'enforcement', 'drugsfda'
    """
    create_tables()
    session = get_session()
    
    try:
        norm_query = normalize_query(query)
        search_term = session.query(SearchTerm).filter_by(term=norm_query, endpoint=endpoint).first()
        if not search_term:
            logger.info(f"Creating new search entry for query: '{query}' ({endpoint})")
            search_term = SearchTerm(term=norm_query, endpoint=endpoint)
            session.add(search_term)
            session.commit()
        else:
            logger.info(f"Using existing search entry for query: '{query}' ({endpoint})")
            
        api = OpenFDAAPI()
        
        # Select method and processor
        if endpoint == "event":
            fetch_func = api.search_events
            process_func = process_event
        elif endpoint == "label":
            fetch_func = api.search_labels
            process_func = process_label
        elif endpoint == "ndc":
            fetch_func = api.search_ndc
            process_func = process_ndc
        elif endpoint == "enforcement":
            fetch_func = api.search_enforcement
            process_func = process_enforcement
        elif endpoint == "drugsfda":
            fetch_func = api.search_drugsfda
            process_func = process_drugsfda
        else:
            logger.error(f"Unknown endpoint: {endpoint}")
            return 0
            
        logger.info(f"Searching OpenFDA {endpoint} for: '{query}'...")
        records = fetch_records(fetch_func, query, max_records)
        
        if not records:
            logger.info("No records found.")
            return 0
            
        logger.info(f"Processing {len(records)} records...")
        for record in tqdm(records, desc="Storing records"):
            process_func(session, record, search_term.id)
            
        session.commit()
        logger.info("Harvest complete.")
        return len(records)
        
    except Exception as e:
        logger.exception(f"Error during harvest: {e}")
        session.rollback()
        return 0
    finally:
        session.close()
