"""Core logic for fetching and processing Orange Book data."""

import pandas as pd
from sqlalchemy.orm import Session
from tqdm import tqdm
from loguru import logger

from . import config, utils
from .models import (
    Product,
    Patent,
    Exclusivity,
    create_tables,
    get_session,
    drop_tables
)

# Configure logging when module is imported
config.configure_logging()

def load_products(session: Session, products_df: pd.DataFrame):
    """Loads products into the database."""
    # Rename columns to match model
    column_map = {
        'Ingredient': 'ingredient',
        'DF;Route': 'df_route',
        'Trade_Name': 'trade_name',
        'Applicant': 'applicant',
        'Strength': 'strength',
        'Appl_Type': 'appl_type',
        'Appl_No': 'appl_no',
        'Product_No': 'product_no',
        'TE_Code': 'te_code',
        'Approval_Date': 'approval_date',
        'RLD': 'rld',
        'RS': 'rs',
        'Type': 'type',
        'Applicant_Full_Name': 'applicant_full_name'
    }
    products_df = products_df.rename(columns=column_map)
    
    # Fill NaN with None or empty string
    products_df = products_df.where(pd.notnull(products_df), None)
    
    # Convert to list of dicts
    products_data = products_df.to_dict(orient='records')
    
    # Bulk save might be faster, but merge handles updates
    # Given the size, let's try to upsert individually or use bulk_save_objects if we wipe first
    # Since we are likely doing a full refresh, wiping tables might be better.
    
    for row in tqdm(products_data, desc="Loading Products"):
        product = Product(**row)
        session.merge(product)

def load_patents(session: Session, patent_df: pd.DataFrame):
    """Loads patents into the database."""
    column_map = {
        'Appl_Type': 'appl_type',
        'Appl_No': 'appl_no',
        'Product_No': 'product_no',
        'Patent_No': 'patent_no',
        'Patent_Expire_Date_Text': 'patent_expire_date_text',
        'Drug_Substance_Flag': 'drug_substance_flag',
        'Drug_Product_Flag': 'drug_product_flag',
        'Patent_Use_Code': 'patent_use_code',
        'Delist_Flag': 'delist_flag',
        'Submission_Date': 'submission_date'
    }
    patent_df = patent_df.rename(columns=column_map)
    patent_df = patent_df.where(pd.notnull(patent_df), None)
    
    patents_data = patent_df.to_dict(orient='records')
    
    for row in tqdm(patents_data, desc="Loading Patents"):
        # We don't have a unique ID for patents in the source, so we can just add them.
        # But if we merge, we need a PK.
        # Since we might wipe tables, just adding is fine.
        patent = Patent(**row)
        session.add(patent)

def load_exclusivity(session: Session, exclusivity_df: pd.DataFrame):
    """Loads exclusivity data into the database."""
    column_map = {
        'Appl_Type': 'appl_type',
        'Appl_No': 'appl_no',
        'Product_No': 'product_no',
        'Exclusivity_Code': 'exclusivity_code',
        'Exclusivity_Date': 'exclusivity_date'
    }
    exclusivity_df = exclusivity_df.rename(columns=column_map)
    exclusivity_df = exclusivity_df.where(pd.notnull(exclusivity_df), None)
    
    exclusivity_data = exclusivity_df.to_dict(orient='records')
    
    for row in tqdm(exclusivity_data, desc="Loading Exclusivity"):
        excl = Exclusivity(**row)
        session.add(excl)

def harvest(force_download: bool = False, full_refresh: bool = True):
    """
    Main function to harvest Orange Book data.
    """
    if force_download or utils.is_data_stale():
        logger.info("Data is stale or force_download is True. Downloading...")
        utils.download_data()
    else:
        logger.info("Data is fresh.")

    products_path = config.DATA_DIR / 'products.txt'
    exclusivity_path = config.DATA_DIR / 'exclusivity.txt'
    patent_path = config.DATA_DIR / 'patent.txt'
    
    if not products_path.exists():
         raise FileNotFoundError(f"Data not found at {config.DATA_DIR} even after attempted download.")

    logger.info("Reading CSV files...")
    # Force dtype=str to preserve leading zeros in Appl_No, Product_No
    dtype_map = {'Appl_No': str, 'Product_No': str, 'Appl_Type': str}
    
    products_df = pd.read_csv(products_path, sep='~', low_memory=False, dtype=dtype_map)
    patent_df = pd.read_csv(patent_path, sep='~', low_memory=False, dtype=dtype_map)
    exclusivity_df = pd.read_csv(exclusivity_path, sep='~', low_memory=False, dtype=dtype_map)

    create_tables()
    session = get_session()
    
    try:
        if full_refresh:
            logger.info("Performing full refresh. Dropping and recreating tables...")
            drop_tables()
            create_tables()
        
        load_products(session, products_df)
        load_patents(session, patent_df)
        load_exclusivity(session, exclusivity_df)
        
        session.commit()
        logger.info("Harvest complete.")
        
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        session.rollback()
    finally:
        session.close()
