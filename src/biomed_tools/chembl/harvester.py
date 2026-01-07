from typing import Dict, List, Optional
from loguru import logger
from sqlalchemy.orm import Session
from tqdm import tqdm
from datetime import datetime

from . import config
from .api import ChemblAPI
from .models import (
    create_tables,
    get_session,
    Molecule,
    MoleculeProperty,
    MoleculeSynonym,
    Mechanism,
    MoleculeATC,
    MoleculeCrossReference,
    SearchTerm,
    SearchToMolecule
)
from .utils import normalize_query

config.configure_logging()

def fetch_all_molecules(query: str, max_records: int = 100) -> List[Dict]:
    """
    Fetch molecules matching query.
    """
    api = ChemblAPI()
    all_molecules = []
    
    # First request
    params = {"limit": config.CHUNK_SIZE, "offset": 0}
    data = api.search_molecules(query, params=params)
    
    if not data:
        return []
        
    molecules = data.get("molecules", [])
    if not molecules:
        logger.info(f"No molecules found for query '{query}'")
        return []

    all_molecules.extend(molecules)
    
    page_meta = data.get("page_meta", {})
    total_count = page_meta.get("total_count", 0)
    
    logger.info(f"Found {total_count} molecules for query '{query}'")
    
    # Pagination
    # Determine how many more to fetch
    to_fetch = min(total_count, max_records)
    
    with tqdm(total=to_fetch, initial=len(molecules), desc="Fetching molecules") as pbar:
        while len(all_molecules) < to_fetch:
            next_offset = len(all_molecules)
            params["offset"] = next_offset
            
            data = api.search_molecules(query, params=params)
            if not data:
                break
                
            new_molecules = data.get("molecules", [])
            if not new_molecules:
                break
                
            all_molecules.extend(new_molecules)
            pbar.update(len(new_molecules))
            
            # Safety break if no progress
            if not new_molecules:
                break

    return all_molecules[:max_records]

def process_and_store_molecule(session: Session, molecule_data: Dict):
    """
    Store molecule data in DB.
    """
    chembl_id = molecule_data.get("molecule_chembl_id")
    if not chembl_id:
        return

    # Create Molecule object
    props = molecule_data.get("molecule_properties") or {}
    struct = molecule_data.get("molecule_structures") or {}
    
    molecule = Molecule(
        chembl_id=chembl_id,
        pref_name=molecule_data.get("pref_name"),
        molecule_type=molecule_data.get("molecule_type"),
        max_phase=molecule_data.get("max_phase"),
        therapeutic_flag=molecule_data.get("therapeutic_flag"),
        structure_type=molecule_data.get("structure_type"),
        inchi_key=struct.get("standard_inchi_key"),
        canonical_smiles=struct.get("canonical_smiles"),
        standard_inchi=struct.get("standard_inchi"),
        
        first_approval=molecule_data.get("first_approval"),
        black_box_warning=molecule_data.get("black_box_warning"),
        natural_product=molecule_data.get("natural_product"),
        prodrug=molecule_data.get("prodrug"),
        oral=molecule_data.get("oral"),
        parenteral=molecule_data.get("parenteral"),
        topical=molecule_data.get("topical"),
        inorganic_flag=molecule_data.get("inorganic_flag"),
        dosed_ingredient=molecule_data.get("dosed_ingredient"),
    )
    
    # Properties
    if props:
        # Check if values are None, SQLAlchemy handles None but just to be safe
        molecule.properties = MoleculeProperty(
            molecular_weight=props.get("full_mwt"),
            alogp=props.get("alogp"),
            hba=props.get("hba"),
            hbd=props.get("hbd"),
            psa=props.get("psa"),
            rtb=props.get("rtb"),
            
            aromatic_rings=props.get("aromatic_rings"),
            heavy_atoms=props.get("heavy_atoms"),
            mw_freebase=props.get("mw_freebase"),
            np_likeness_score=props.get("np_likeness_score"),
            num_ro5_violations=props.get("num_ro5_violations"),
            qed_weighted=props.get("qed_weighted"),
            ro3_pass=props.get("ro3_pass"),
        )
        
    # Synonyms
    synonyms_data = molecule_data.get("molecule_synonyms", [])
    if synonyms_data:
        molecule.synonyms = [
            MoleculeSynonym(
                synonym=syn.get("molecule_synonym"),
                syn_type=syn.get("syn_type")
            ) for syn in synonyms_data if syn.get("molecule_synonym")
        ]
        
    # ATC
    atc_codes = molecule_data.get("atc_classifications", [])
    if atc_codes:
        molecule.atc_classifications = [
            MoleculeATC(level5=code) for code in atc_codes
        ]
        
    # Cross Refs
    xrefs = molecule_data.get("cross_references", [])
    if xrefs:
        molecule.cross_references = [
            MoleculeCrossReference(
                xref_src=xref.get("xref_src"),
                xref_id_val=xref.get("xref_id"),
                xref_name=xref.get("xref_name")
            ) for xref in xrefs
        ]

    # Mechanisms
    api = ChemblAPI()
    mechanisms_data = api.molecule_mechanisms(chembl_id)
    if mechanisms_data and "mechanisms" in mechanisms_data:
        molecule.mechanisms = [
            Mechanism(
                mechanism_of_action=mech.get("mechanism_of_action"),
                target_name=mech.get("target_name"),
                target_chembl_id=mech.get("target_chembl_id"),
                action_type=mech.get("action_type")
            ) for mech in mechanisms_data["mechanisms"]
        ]
    
    session.merge(molecule)

def run_chembl_query(query: str, max_records: int = 9999) -> int:
    create_tables()
    session = get_session()
    
    try:
        norm_query = normalize_query(query)
        search_term = session.query(SearchTerm).filter_by(term=norm_query).first()
        if not search_term:
            search_term = SearchTerm(term=norm_query, timestamp=datetime.now())
            session.add(search_term)
            session.flush() # to get id
        else:
            search_term.timestamp = datetime.now()
        
        molecules = fetch_all_molecules(query, max_records)
        
        for mol_data in tqdm(molecules, desc="Storing molecules"):
            process_and_store_molecule(session, mol_data)
            
            # Link to search
            chembl_id = mol_data.get("molecule_chembl_id")
            if chembl_id:
                link = SearchToMolecule(search_id=search_term.id, chembl_id=chembl_id)
                session.merge(link)
        
        session.commit()
        logger.info(f"Successfully processed {len(molecules)} molecules.")
        return len(molecules)
        
    except Exception as e:
        logger.exception(f"Error running ChEMBL query: {e}")
        session.rollback()
        return 0
    finally:
        session.close()
