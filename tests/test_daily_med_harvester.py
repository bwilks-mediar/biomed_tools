import pytest
from unittest.mock import MagicMock, patch
from biomed_tools.daily_med.harvester import run_daily_med_query
from biomed_tools.daily_med.models import Drug, SearchTerm

@patch("biomed_tools.daily_med.harvester.DailyMedApi")
@patch("biomed_tools.daily_med.harvester.get_session")
@patch("biomed_tools.daily_med.harvester.create_tables")
def test_run_daily_med_query(mock_create_tables, mock_get_session, mock_api_cls):
    # Setup mocks
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session
    
    mock_api = MagicMock()
    mock_api_cls.return_value = mock_api
    
    # Mock search response (pagination)
    mock_api.search_spls.side_effect = [
        {
            "data": [
                {"title": "Test Drug 1", "setid": "set1", "spl_version": 1},
                {"title": "Test Drug 2", "setid": "set2", "spl_version": 2},
            ],
            "metadata": {"total_pages": 1}
        },
        {"data": []} # Subsequent calls (though loop should stop based on page logic)
    ]
    
    # Mock database queries
    mock_session.query.return_value.filter_by.return_value.first.return_value = None  # No existing search term

    # Run the function
    count = run_daily_med_query("test drug")

    # Assertions
    assert count == 2
    mock_create_tables.assert_called_once()
    mock_api.search_spls.assert_called()
    
    # Verify drugs were added to session
    # We expect 2 merges for drugs + 1 add for search term + 1 commit
    assert mock_session.merge.call_count == 2
    assert mock_session.add.call_count == 1  # Search term
    assert mock_session.commit.call_count >= 1

    # Verify call arguments for merge (Drugs)
    calls = mock_session.merge.call_args_list
    assert calls[0][0][0].set_id == "set1"
    assert calls[0][0][0].drug_name == "Test Drug 1"
    assert calls[1][0][0].set_id == "set2"
    assert calls[1][0][0].drug_name == "Test Drug 2"

@patch("biomed_tools.daily_med.harvester.DailyMedApi")
@patch("biomed_tools.daily_med.harvester.get_session")
@patch("biomed_tools.daily_med.harvester.create_tables")
def test_run_daily_med_query_no_results(mock_create_tables, mock_get_session, mock_api_cls):
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session
    mock_api = MagicMock()
    mock_api_cls.return_value = mock_api
    
    mock_api.search_spls.return_value = {"data": [], "metadata": {"total_pages": 0}}
    mock_session.query.return_value.filter_by.return_value.first.return_value = None

    count = run_daily_med_query("unknown drug")

    assert count == 0
    mock_session.merge.assert_not_called()
