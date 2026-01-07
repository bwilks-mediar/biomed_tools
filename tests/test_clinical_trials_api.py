import pytest
from unittest.mock import MagicMock, patch, call
from biomed_tools.clinical_trials import ClinicalTrialsAPI, config
import requests
import time

@pytest.fixture
def api():
    return ClinicalTrialsAPI()

def test_list_studies(api):
    with patch.object(api.session, 'get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"studies": []}
        mock_get.return_value = mock_response

        studies = api.list_studies(params={"query.cond": "test"})
        
        assert studies == {"studies": []}
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert "studies" in args[0]
        assert kwargs['params'] == {"query.cond": "test"}

def test_fetch_study(api):
    with patch.object(api.session, 'get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"study": "data"}
        mock_get.return_value = mock_response

        study = api.fetch_study("NCT123456")
        
        assert study == {"study": "data"}
        mock_get.assert_called_once()
        assert "studies/NCT123456" in mock_get.call_args[0][0]

def test_retry_logic_success(api):
    """Test that the API retries on failure and eventually succeeds."""
    with patch.object(api.session, 'get') as mock_get, \
         patch('time.sleep') as mock_sleep:  # Mock sleep to speed up tests
        
        # Fail twice, then succeed
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        
        mock_get.side_effect = [
            requests.exceptions.RequestException("Fail 1"),
            requests.exceptions.RequestException("Fail 2"),
            mock_response
        ]
        
        result = api._make_request("test")
        
        assert result == {"success": True}
        assert mock_get.call_count == 3

def test_retry_logic_failure(api):
    """Test that the API gives up after MAX_RETRIES."""
    with patch.object(api.session, 'get') as mock_get, \
         patch('time.sleep') as mock_sleep:
        
        mock_get.side_effect = requests.exceptions.RequestException("Fail always")
        
        result = api._make_request("test")
        
        assert result is None
        assert mock_get.call_count == config.MAX_RETRIES

def test_list_studies_paginated(api):
    """Test pagination logic."""
    with patch.object(api, '_make_request') as mock_request:
        # Page 1
        page1 = {
            "studies": [{"id": 1}, {"id": 2}],
            "nextPageToken": "token1"
        }
        # Page 2
        page2 = {
            "studies": [{"id": 3}],
            "nextPageToken": "token2"
        }
        # Page 3 (last)
        page3 = {
            "studies": [{"id": 4}]
        }
        
        mock_request.side_effect = [page1, page2, page3]
        
        studies = api.list_studies_paginated(max_pages=5)
        
        assert len(studies) == 4
        assert studies == [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}]
        assert mock_request.call_count == 3
        
        # Verify calls had correct tokens
        calls = mock_request.call_args_list
        # Arguments are positional: _make_request("studies", params)
        assert calls[0][0][1].get('pageToken') is None
        assert calls[1][0][1]['pageToken'] == "token1"
        assert calls[2][0][1]['pageToken'] == "token2"

def test_list_studies_paginated_limit(api):
    """Test that pagination stops at max_pages."""
    with patch.object(api, '_make_request') as mock_request:
        page1 = {"studies": [{"id": 1}], "nextPageToken": "token1"}
        page2 = {"studies": [{"id": 2}], "nextPageToken": "token2"}
        
        mock_request.side_effect = [page1, page2]
        
        studies = api.list_studies_paginated(max_pages=1)
        
        assert len(studies) == 1
        assert studies == [{"id": 1}]
        assert mock_request.call_count == 1
