# DailyMed Module

The DailyMed module provides an interface to the DailyMed API, allowing you to search for drug product information and package inserts (labels). It also supports harvesting data into a local SQLite database.

## Features

- **DailyMedApi**: A wrapper class for the DailyMed REST API (v2).
- **Drug Search**: Search for drugs by name.
- **Label Retrieval**: Get drug label information by Set ID.
- **NDC Lookup**: Get drug information by National Drug Code (NDC).
- **CLI**: Command-line tools for harvesting and managing data.
- **Database**: SQLite storage for harvested drug data.

## CLI Usage

You can use the `miner` CLI to interact with DailyMed.

```bash
# Harvest drug data
uv run miner daily-med harvest "tylenol"

# Clear the database
uv run miner daily-med clear

# Migrate/Create database tables
uv run miner daily-med migrate
```

## Python Usage

### API Access

```python
from biomed_tools.daily_med import DailyMedApi

api = DailyMedApi()

# Search for a drug
drug_info = api.search_drug_name("Tylenol")
print(drug_info)

# Get drug by NDC
ndc_data = api.get_drug_by_ndc("50090-0006")
print(ndc_data)
```

### Harvester

```python
from biomed_tools.daily_med import harvester

# Run a query and save to database
count = harvester.run_daily_med_query("aspirin")
print(f"Stored {count} drugs.")
```

## Class Methods (API)

- `search_drug_name(drug_name)`: Search for drugs matching a name.
- `get_drug_label(set_id)`: Get label details for a specific Set ID.
- `get_drug_by_ndc(ndc)`: Get drug details for a specific NDC.
- `get_drug_spls(setid)`: Download the SPL (Structured Product Labeling) XML file.
