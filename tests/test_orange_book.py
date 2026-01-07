import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from biomed_tools.orange_book import harvester, models, utils, config

@pytest.fixture
def db_session():
    """Creates a fresh in-memory database for each test."""
    engine = create_engine("sqlite:///:memory:")
    models.Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_models(db_session):
    """Test creating and retrieving models."""
    prod = models.Product(
        appl_no="000123",
        appl_type="N",
        product_no="001",
        trade_name="TestDrug",
        ingredient="TestIng"
    )
    db_session.add(prod)
    db_session.commit()
    
    retrieved = db_session.query(models.Product).first()
    assert retrieved.appl_no == "000123"
    assert retrieved.trade_name == "TestDrug"
    
    pat = models.Patent(
        appl_no="000123",
        appl_type="N",
        product_no="001",
        patent_no="9999999",
        patent_expire_date_text="Jan 1, 2030"
    )
    db_session.add(pat)
    db_session.commit()
    
    retrieved_pat = db_session.query(models.Patent).first()
    assert retrieved_pat.product.trade_name == "TestDrug"

def test_load_products(db_session):
    df = pd.DataFrame({
        'Appl_No': ['123'],
        'Appl_Type': ['A'],
        'Product_No': ['001'],
        'Trade_Name': ['DrugA'],
        'Ingredient': ['IngA']
    })
    
    harvester.load_products(db_session, df)
    db_session.commit()
    
    prod = db_session.query(models.Product).first()
    assert prod.appl_no == "123"
    assert prod.trade_name == "DrugA"

def test_load_patents(db_session):
    # Ensure product exists first due to foreign key constraint
    prod = models.Product(appl_no="123", appl_type="A", product_no="001")
    db_session.add(prod)
    db_session.commit()

    df = pd.DataFrame({
        'Appl_No': ['123'],
        'Appl_Type': ['A'],
        'Product_No': ['001'],
        'Patent_No': ['Pat1']
    })
    
    harvester.load_patents(db_session, df)
    db_session.commit()
    
    pat = db_session.query(models.Patent).first()
    assert pat.patent_no == "Pat1"

def test_harvest_flow():
    """Test the full harvest flow with mocks."""
    with patch('biomed_tools.orange_book.utils.is_data_stale', return_value=False), \
         patch('pathlib.Path.exists', return_value=True), \
         patch('pandas.read_csv') as mock_read_csv, \
         patch('biomed_tools.orange_book.harvester.get_session') as mock_get_session, \
         patch('biomed_tools.orange_book.harvester.drop_tables'), \
         patch('biomed_tools.orange_book.harvester.create_tables'):
        
        # Mock DB Session
        engine = create_engine("sqlite:///:memory:")
        models.Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        mock_get_session.return_value = session
        
        # Mock DataFrames
        df_prod = pd.DataFrame({'Appl_No': ['1'], 'Appl_Type': ['N'], 'Product_No': ['1'], 'Trade_Name': ['T1']})
        df_pat = pd.DataFrame({'Appl_No': ['1'], 'Appl_Type': ['N'], 'Product_No': ['1'], 'Patent_No': ['P1']})
        df_excl = pd.DataFrame({'Appl_No': ['1'], 'Appl_Type': ['N'], 'Product_No': ['1'], 'Exclusivity_Code': ['E1']})
        
        mock_read_csv.side_effect = [df_prod, df_pat, df_excl]
        
        harvester.harvest(full_refresh=True)
        
        # Verify data loaded
        assert session.query(models.Product).count() == 1
        assert session.query(models.Patent).count() == 1
        assert session.query(models.Exclusivity).count() == 1

def test_is_data_stale():
    with patch('pathlib.Path.exists', return_value=False):
        assert utils.is_data_stale() is True
