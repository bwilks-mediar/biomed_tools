# GEO Module

The GEO module provides tools to download and query the GEOmetadb database, which contains metadata for Gene Expression Omnibus (GEO) datasets.

## Features

- **Downloader**: Fetches the compressed `GEOmetadb.sqlite` file from the official source.
- **Query**: Helper functions to search the local database for Series (GSE) by keyword.
- **CLI**: Command-line interface for managing the database and querying.

## Usage

### CLI

```bash
# Download the GEOmetadb database
miner geo harvest

# Query the database
miner geo query "melanoma"

# Clear the local database file
miner geo clear
```

### Python API

#### Downloading the Database

```python
from biomed_tools.geo import harvester

# Downloads and extracts GEOmetadb.sqlite
harvester.download_geometadb()
```

#### Querying

```python
from biomed_tools.geo import utils

# Find GSE series matching a keyword
df = utils.find_gse_by_keyword("lung cancer")
print(df.head())
```

## Configuration

Configuration is handled in `src/biomed_tools/geo/config.py`. Key settings:
- `DB_URL`: Path to the SQLite database (default: `db/GEOmetadb.sqlite`).
- `LOG_FILE`: Path to the log file (default: `logs/geo.log`).

Logging is automatically configured when using the CLI or importing the `harvester` module.
