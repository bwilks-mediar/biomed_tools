"""Tests for ChEMBL Miner."""

import pytest
from unittest.mock import MagicMock, patch
from biomed_tools.chembl.api import ChemblAPI
from biomed_tools.chembl.harvester import run_chembl_query
from biomed_tools.chembl import config

def test_api_search_molecules():
    with patch("requests.Session") as mock_session:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "molecules": [{"molecule_chembl_id": "CHEMBL1"}],
            "page_meta": {"total_count": 1}
        }
        mock_session.return_value.get.return_value = mock_response

        api = ChemblAPI()
        data = api.search_molecules("aspirin")
        
        assert data["molecules"][0]["molecule_chembl_id"] == "CHEMBL1"
        assert data["page_meta"]["total_count"] == 1

def test_run_chembl_query_integration(tmp_path):
    # Mock database to use a temporary file
    db_path = tmp_path / "test_chembl.db"
    config.DB_URL = f"sqlite:///{db_path}"
    
    with patch("biomed_tools.chembl.harvester.ChemblAPI") as MockAPI:
        mock_api_instance = MockAPI.return_value
        
        # Mock search_molecules response
        mock_api_instance.search_molecules.side_effect = [
            {
                "molecules": [
                    {
                        "molecule_chembl_id": "CHEMBL25",
                        "pref_name": "ASPIRIN",
                        "molecule_type": "Small molecule",
                        "molecule_properties": {
                            "full_mwt": 180.16,
                            "alogp": 1.19
                        }
                    }
                ],
                "page_meta": {"total_count": 1}
            },
            None # For subsequent call if loop continues
        ]
        
        # Mock molecule_mechanisms response
        mock_api_instance.molecule_mechanisms.return_value = {
            "mechanisms": [
                {
                    "mechanism_of_action": "COX inhibitor",
                    "target_name": "Cyclooxygenase",
                    "target_chembl_id": "CHEMBL123",
                    "action_type": "INHIBITOR"
                }
            ]
        }
        
        # Run query
        count = run_chembl_query("aspirin")
        
        assert count == 1
        
        # Verify DB content
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from biomed_tools.chembl.models import Molecule, SearchTerm
        
        engine = create_engine(config.DB_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        molecule = session.query(Molecule).first()
        assert molecule.chembl_id == "CHEMBL25"
        assert molecule.pref_name == "ASPIRIN"
        assert molecule.properties.molecular_weight == 180.16
        assert len(molecule.mechanisms) == 1
        assert molecule.mechanisms[0].mechanism_of_action == "COX inhibitor"
        
        search_term = session.query(SearchTerm).first()
        assert search_term.term == "aspirin"
        
        session.close()
