# RxNav Module

The RxNav module provides an interface to the RxNav API from the National Library of Medicine (NLM), allowing you to retrieve drug information, RxNorm IDs, and class relationships, and store them in a local database.

## Features

- **RxNavAPI**: A wrapper class for the RxNav REST API.
- **Drug ID Lookup**: Get RxNorm IDs (RxCUI) from drug names.
- **Class Information**: Retrieve drug classes (e.g., MoA, EPC) and class members.
- **Relationships**: Explore relationships between drugs and classes.
- **Local Database**: Store drugs, classes, and their relationships in a SQLite database.
- **CLI**: Command-line interface for harvesting drug data.

## CLI Usage

The module exposes commands through the main `miner` CLI.

```bash
# Harvest data for a specific drug
uv run miner rxnav harvest "Lipitor"

# Clear the database
uv run miner rxnav clear

# Initialize/Migrate database
uv run miner rxnav migrate
```

## Python Usage

### Using the API directly

```python
from biomed_tools.rxnav.api import RxNavAPI

api = RxNavAPI()

# Get RxNorm ID
rxcui = api.get_rxnorm_id("Lipitor")
print(f"RxNorm ID: {rxcui}")

# Get Mechanism of Action (MoA)
if rxcui:
    moa = api.get_moa(rxcui)
    print(f"Mechanism of Action: {moa}")

# Get class members
members = api.get_class_members("N0000175606") # Example Class ID
```

### Using the Harvester

```python
from biomed_tools.rxnav import harvester

# Fetch and store drug data
harvester.run_rxnav_query("Lipitor")
```

## Database Schema

The module uses SQLite with the following main tables:
- `drugs`: Stores drug information (name, RxCUI).
- `classes`: Stores drug class information (ID, name, type).
- `drug_classes`: Links drugs to classes with relationship types.
- `search_terms`: Tracks search queries.
