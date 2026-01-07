import pytest
from unittest.mock import MagicMock, patch
from biomed_tools.openfda.api import OpenFDAAPI
from biomed_tools.openfda.harvester import run_openfda_query
from biomed_tools.openfda.models import DrugEvent, DrugLabel, DrugNDC, DrugEnforcement, DrugAtFDA

def test_api_search_events():
    api = OpenFDAAPI()
    with patch("requests.Session.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [{"safetyreportid": "123"}]}
        mock_get.return_value = mock_response
        
        result = api.search_events("aspirin", limit=1)
        assert result["results"][0]["safetyreportid"] == "123"

def test_harvester_events(tmp_path):
    # Mock DB URL to use tmp file
    db_url = f"sqlite:///{tmp_path}/test_openfda.db"
    with patch("biomed_tools.openfda.config.DB_URL", db_url):
        with patch("biomed_tools.openfda.api.OpenFDAAPI.search_events") as mock_search:
            mock_search.return_value = {
                "results": [
                    {
                        "safetyreportid": "TEST001",
                        "receivedate": "20220101",
                        "patient": {
                            "drug": [{"medicinalproduct": "ASPIRIN", "drugcharacterization": "1"}]
                        }
                    }
                ]
            }
            
            count = run_openfda_query("aspirin", endpoint="event", max_records=1)
            assert count == 1
            
            # Verify DB content
            from biomed_tools.openfda.models import get_session
            session = get_session()
            event = session.query(DrugEvent).first()
            assert event.safetyreportid == "TEST001"
            session.close()

def test_harvester_labels(tmp_path):
    db_url = f"sqlite:///{tmp_path}/test_openfda.db"
    with patch("biomed_tools.openfda.config.DB_URL", db_url):
        with patch("biomed_tools.openfda.api.OpenFDAAPI.search_labels") as mock_search:
            mock_search.return_value = {
                "results": [
                    {
                        "id": "LABEL001",
                        "set_id": "SET001",
                        "openfda": {"brand_name": ["BrandA"]}
                    }
                ]
            }
            
            count = run_openfda_query("ibuprofen", endpoint="label", max_records=1)
            assert count == 1
            
            from biomed_tools.openfda.models import get_session
            session = get_session()
            label = session.query(DrugLabel).first()
            assert label.id == "LABEL001"
            session.close()
