import pytest
from unittest.mock import MagicMock, patch
from biomed_tools.rxnav.api import RxNavAPI
from biomed_tools.rxnav import harvester, models
import requests

@pytest.fixture
def api():
    return RxNavAPI()

def test_get_rxnorm_id(api):
    with patch.object(api.session, 'get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "idGroup": {"rxnormId": ["12345"]}
        }
        mock_get.return_value = mock_response

        rxcui = api.get_rxnorm_id("Lipitor")
        
        assert rxcui == "12345"
        mock_get.assert_called_once()
        assert "rxcui.json" in mock_get.call_args[0][0]

def test_get_moa(api):
    with patch.object(api.session, 'get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "rxclassDrugInfoList": {
                "rxclassDrugInfo": [
                    {"rxclassMinConceptItem": {"className": "MOA1"}}
                ]
            }
        }
        mock_get.return_value = mock_response

        moa = api.get_moa("12345")
        
        assert moa == ["MOA1"]
        mock_get.assert_called_once()

@patch('biomed_tools.rxnav.harvester.RxNavAPI')
@patch('biomed_tools.rxnav.harvester.get_session')
@patch('biomed_tools.rxnav.harvester.create_tables')
def test_run_rxnav_query(mock_create_tables, mock_get_session, MockRxNavAPI):
    # Setup mocks
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session
    
    mock_api = MockRxNavAPI.return_value
    mock_api.get_rxnorm_id.return_value = "12345"
    mock_api.get_class_by_rxcui.return_value = [
        {
            "rxclassMinConceptItem": {
                "classId": "C1",
                "className": "Class 1",
                "classType": "MOA"
            }
        }
    ]
    
    # Mock database queries
    mock_session.query.return_value.filter_by.return_value.first.return_value = None
    
    # Run function
    result = harvester.run_rxnav_query("Lipitor")
    
    # Verify
    assert result == 1
    mock_api.get_rxnorm_id.assert_called_with("Lipitor")
    assert mock_session.add.call_count >= 1 # Should add SearchTerm, Drug, Class
    mock_session.commit.assert_called()
