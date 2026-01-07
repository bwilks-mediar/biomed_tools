import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date
from biomed_tools.pubmed import harvester, models, api, utils

@pytest.fixture
def db_session():
    """Creates a fresh in-memory database for each test."""
    engine = create_engine("sqlite:///:memory:")
    models.Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_process_medline_record():
    record = {
        "PMID": "12345",
        "TI": "Test Title",
        "AB": "Test Abstract",
        "AU": ["Author A", "Author B"],
        "DP": "2023 Jan 01",
        "AID": ["PMC12345 [pmcid]", "10.1234/test [doi]"]
    }
    result = harvester.process_medline_record(record)
    assert result["pmid"] == "12345"
    assert result["title"] == "Test Title"
    assert result["pmcid"] == "PMC12345"
    assert result["doi"] == "10.1234/test"
    assert result["pub_date"] == date(2023, 1, 1)

def test_run_pubmed_query(db_session):
    # Mocking Entrez and Medline in harvester
    with patch("biomed_tools.pubmed.harvester.Entrez") as mock_entrez, \
         patch("biomed_tools.pubmed.harvester.Medline") as mock_medline, \
         patch("biomed_tools.pubmed.harvester.get_session", return_value=db_session), \
         patch("biomed_tools.pubmed.harvester.create_tables"):

        # Mock ESearch response
        mock_entrez.esearch.return_value = MagicMock()
        mock_entrez.read.side_effect = [
            {"Count": "1", "IdList": ["12345"], "WebEnv": "env", "QueryKey": "1"},
            {"IdList": ["12345"]} # Handle potentially extra read calls if any, though run_pubmed_query logic handles one if count < max
        ]

        # Mock EFetch response
        mock_entrez.efetch.return_value = MagicMock()
        
        # Mock Medline parsing
        mock_medline.parse.return_value = [
            {
                "PMID": "12345",
                "TI": "Test Study",
                "AB": "Abstract",
                "DP": "2023"
            }
        ]

        # Mock safe_entrez_request to call the function passed to it (which is the mock)
        with patch("biomed_tools.pubmed.harvester.safe_entrez_request") as mock_safe:
             # Define side_effect to mimic calling the function
            def side_effect(func, *args, **kwargs):
                return func(*args, **kwargs)
            mock_safe.side_effect = side_effect
            
            count = harvester.run_pubmed_query("test query")
            
            assert count == 1
            
            # Verify DB
            pub = db_session.query(models.Publication).filter_by(pmid="12345").first()
            assert pub is not None
            assert pub.title == "Test Study"

def test_fetch_full_text():
    with patch("biomed_tools.pubmed.api.safe_entrez_request") as mock_safe:
        mock_handle = MagicMock()
        mock_handle.read.return_value = b"<article><body><p>Paragraph 1</p><p>Paragraph 2</p></body></article>"
        mock_handle.close = MagicMock()
        
        mock_safe.return_value = mock_handle
        
        text = api.fetch_full_text("PMC123")
        assert "Paragraph 1" in text
        assert "Paragraph 2" in text
