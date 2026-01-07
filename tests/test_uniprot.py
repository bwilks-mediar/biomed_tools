"""Tests for UniProt Miner."""

import pytest
from unittest.mock import MagicMock, patch
from biomed_tools.uniprot.api import UniprotAPI
from biomed_tools.uniprot.harvester import get_next_link, run_uniprot_query
from biomed_tools.uniprot import config

@pytest.fixture
def api_mock():
    return MagicMock(spec=UniprotAPI)

def test_get_next_link():
    link_header = '<https://rest.uniprot.org/uniprotkb/search?cursor=xyz&query=gene:brca1&size=500>; rel="next"'
    next_link = get_next_link(link_header)
    assert next_link == "https://rest.uniprot.org/uniprotkb/search?cursor=xyz&query=gene:brca1&size=500"

    link_header_multiple = '<https://rest.uniprot.org/uniprotkb/search?cursor=xyz>; rel="next", <https://rest.uniprot.org/uniprotkb/search?cursor=abc>; rel="last"'
    next_link = get_next_link(link_header_multiple)
    assert next_link == "https://rest.uniprot.org/uniprotkb/search?cursor=xyz"

    assert get_next_link(None) is None
    assert get_next_link("invalid") is None

def test_api_search_proteins():
    with patch("requests.Session") as mock_session:
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": [{"primaryAccession": "P12345"}]}
        mock_response.headers = {"Link": '<next_url>; rel="next"'}
        mock_session.return_value.get.return_value = mock_response

        api = UniprotAPI()
        data, link = api.search_proteins("gene:brca1")
        
        assert data == {"results": [{"primaryAccession": "P12345"}]}
        assert link == '<next_url>; rel="next"'

def test_run_uniprot_query_integration(tmp_path):
    # Mock database to use a temporary file
    db_path = tmp_path / "test_uniprot.db"
    config.DB_URL = f"sqlite:///{db_path}"
    
    with patch("biomed_tools.uniprot.harvester.UniprotAPI") as MockAPI:
        mock_api_instance = MockAPI.return_value
        
        # Mock search_proteins response
        mock_api_instance.search_proteins.return_value = (
            {
                "results": [
                    {
                        "primaryAccession": "P12345",
                        "uniProtkbId": "TEST_HUMAN",
                        "proteinDescription": {
                            "recommendedName": {
                                "fullName": {"value": "Test Protein"}
                            }
                        },
                        "genes": [{"geneName": {"value": "TEST1"}}],
                        "organism": {"scientificName": "Homo sapiens", "taxonId": 9606},
                        "sequence": {"value": "MKVL", "length": 4, "molWeight": 500}
                    }
                ]
            },
            None # No next page
        )
        
        # Run query
        count = run_uniprot_query("gene:test1")
        
        assert count == 1
        
        # Verify DB content
        from sqlalchemy import create_engine, inspect
        from sqlalchemy.orm import sessionmaker
        from biomed_tools.uniprot.models import Protein, SearchTerm
        
        engine = create_engine(config.DB_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        protein = session.query(Protein).first()
        assert protein.accession == "P12345"
        assert protein.protein_name == "Test Protein"
        assert protein.gene_name == "TEST1"
        
        search_term = session.query(SearchTerm).first()
        assert search_term.term == "gene:test1"
        
        session.close()
