import pytest
from unittest.mock import MagicMock, patch
from biomed_tools.daily_med import DailyMedApi
import requests

@pytest.fixture
def api():
    return DailyMedApi()

def test_search_drug_name(api):
    with patch.object(api.session, 'get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response

        result = api.search_drug_name("ASPIRIN")
        
        assert result == {"data": []}
        mock_get.assert_called_once()
        assert "drugnames.json" in mock_get.call_args[0][0]
        assert mock_get.call_args[1]['params'] == {"drug_name": "ASPIRIN"}

def test_get_drug_spls(api):
    with patch.object(api.session, 'get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<xml>data</xml>"
        mock_get.return_value = mock_response

        result = api.get_drug_spls("setid")
        
        assert result == b"<xml>data</xml>"
        mock_get.assert_called_once()
