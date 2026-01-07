import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from biomed_tools.clinical_trials import harvester, models, config

@pytest.fixture
def db_session():
    """Creates a fresh in-memory database for each test."""
    engine = create_engine("sqlite:///:memory:")
    models.Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_fetch_all_trials():
    """Test fetching trials using the API wrapper."""
    with patch('biomed_tools.clinical_trials.harvester.ClinicalTrialsAPI') as MockAPI:
        api_instance = MockAPI.return_value
        
        # Mock responses
        page1 = {
            "studies": [
                {"protocolSection": {"identificationModule": {"nctId": "NCT001"}}},
                {"protocolSection": {"identificationModule": {"nctId": "NCT002"}}}
            ],
            "totalCount": 2,
            "nextPageToken": None
        }
        
        api_instance.list_studies.return_value = page1
        
        result = harvester.fetch_all_trials("test query")
        
        assert result["totalCount"] == 2
        assert len(result["studies"]) == 2
        assert result["studies"][0]["protocolSection"]["identificationModule"]["nctId"] == "NCT001"
        api_instance.list_studies.assert_called()

def test_process_and_store_trial(db_session):
    """Test storing a trial in the database."""
    study_data = {
        "protocolSection": {
            "identificationModule": {
                "nctId": "NCT12345",
                "briefTitle": "Test Study",
                "organization": {"fullName": "Test Org", "class": "INDUSTRY"}
            },
            "statusModule": {
                "overallStatus": "RECRUITING"
            }
        }
    }
    
    # Create a dummy search term
    search_term = models.SearchTerm(term="test")
    db_session.add(search_term)
    db_session.commit()
    
    harvester.process_and_store_trial(db_session, study_data, search_term.id)
    db_session.commit()
    
    # Verify storage
    trial = db_session.query(models.ClinicalTrial).filter_by(nct_id="NCT12345").first()
    assert trial is not None
    assert trial.brief_title == "Test Study"
    assert trial.overall_status == "RECRUITING"
    
    # Verify organization
    org = db_session.query(models.Organization).filter_by(name="Test Org").first()
    assert org is not None
    assert org.class_ == "INDUSTRY"
    
    # Verify link
    link = db_session.query(models.SearchToTrial).filter_by(search_id=search_term.id, nct_id="NCT12345").first()
    assert link is not None

def test_run_clinical_trials_query_integration():
    """Integration test for the harvester (mocking only the network call)."""
    with patch('biomed_tools.clinical_trials.harvester.ClinicalTrialsAPI') as MockAPI, \
         patch('biomed_tools.clinical_trials.harvester.get_session') as mock_get_session, \
         patch('biomed_tools.clinical_trials.harvester.create_tables'):
        
        # Setup DB
        engine = create_engine("sqlite:///:memory:")
        models.Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        mock_get_session.return_value = session
        
        # Mock API
        api_instance = MockAPI.return_value
        page1 = {
            "studies": [
                {"protocolSection": {"identificationModule": {"nctId": "NCT999"}}}
            ],
            "totalCount": 1,
            "nextPageToken": None
        }
        api_instance.list_studies.return_value = page1
        
        # Run harvester
        count = harvester.run_clinical_trials_query("integration test")
        
        assert count == 1
        
        # Verify DB
        trial = session.query(models.ClinicalTrial).filter_by(nct_id="NCT999").first()
        assert trial is not None
        
        # Verify Search Term
        term = session.query(models.SearchTerm).filter_by(term="integration test").first()
        assert term is not None
