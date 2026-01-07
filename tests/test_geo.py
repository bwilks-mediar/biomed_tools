import pytest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
import pandas as pd
import sqlite3
from biomed_tools.geo import harvester, utils

@pytest.fixture
def mock_db_path(tmp_path):
    db_path = tmp_path / "GEOmetadb.sqlite"
    with patch("biomed_tools.geo.config.get_db_path", return_value=db_path):
        yield db_path

def test_download_geometadb_exists(mock_db_path):
    mock_db_path.touch()
    with patch("biomed_tools.geo.harvester.requests") as mock_req:
        harvester.download_geometadb()
        mock_req.get.assert_not_called()

def test_download_geometadb_download():
    # Use mocks for paths to avoid filesystem issues with mocked open
    mock_db_path_obj = MagicMock()
    mock_db_path_obj.exists.return_value = False
    mock_gz_path = MagicMock()
    mock_db_path_obj.with_suffix.return_value = mock_gz_path
    
    with patch("biomed_tools.geo.config.get_db_path", return_value=mock_db_path_obj), \
         patch("biomed_tools.geo.harvester.requests.get") as mock_get, \
         patch("biomed_tools.geo.harvester.gzip.open") as mock_gzip, \
         patch("biomed_tools.geo.harvester.shutil.copyfileobj") as mock_copy, \
         patch("builtins.open", mock_open()) as mock_file:
        
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"chunk1"]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value.__enter__.return_value = mock_response

        harvester.download_geometadb()
        
        mock_get.assert_called_once()
        assert mock_copy.called
        mock_gz_path.unlink.assert_called()

def test_find_gse_by_keyword_no_db(mock_db_path):
    if mock_db_path.exists():
        mock_db_path.unlink()
    
    df = utils.find_gse_by_keyword("cancer")
    assert df.empty

def test_find_gse_by_keyword_with_db(mock_db_path):
    # Create a real sqlite db for testing
    con = sqlite3.connect(mock_db_path)
    con.execute("CREATE TABLE gse (gse TEXT, title TEXT, summary TEXT)")
    con.execute("INSERT INTO gse VALUES ('GSE1', 'Lung Cancer Study', 'Summary of lung cancer')")
    con.execute("INSERT INTO gse VALUES ('GSE2', 'Breast Cancer', 'Summary')")
    con.execute("INSERT INTO gse VALUES ('GSE3', 'Other', 'Nothing')")
    con.commit()
    con.close()
    
    df = utils.find_gse_by_keyword("Lung")
    assert len(df) == 1
    assert df.iloc[0]['gse'] == 'GSE1'
    
    df = utils.find_gse_by_keyword("Cancer")
    assert len(df) == 2
