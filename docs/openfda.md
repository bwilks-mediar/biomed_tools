# OpenFDA Module

The OpenFDA module provides access to the FDA's openFDA API for querying public data about drugs.

## Features

- **API Client**: Wrapper around openFDA API with automatic retries and pagination logic.
- **Multiple Endpoints**: Supports harvesting data from:
    - **Adverse Events** (`drug/event`)
    - **Product Labeling** (`drug/label`)
    - **NDC Directory** (`drug/ndc`)
    - **Recall Enforcement Reports** (`drug/enforcement`)
    - **Drugs@FDA** (`drug/drugsfda`)
- **Harvester**: Downloads records based on a search query and endpoint, storing them in a local SQLite database.
- **Structured Database Models**: SQLAlchemy models for structured storage of key fields, with raw JSON backup.
- **CLI**: Command-line interface for easy interaction.

## Usage

### CLI

You can use the CLI to harvest data from specific endpoints. The query string uses [OpenFDA search syntax](https://open.fda.gov/apis/query-syntax/).

```bash
# Harvest adverse events for "aspirin"
uv run miner openfda harvest "patient.drug.medicinalproduct:aspirin" --endpoint event --max-records 100

# Harvest labeling for "ibuprofen"
uv run miner openfda harvest "ibuprofen" --endpoint label --max-records 50

# Harvest NDC data
uv run miner openfda harvest "brand_name:tylenol" --endpoint ndc

# Harvest Enforcement Reports
uv run miner openfda harvest "product_description:ice cream" --endpoint enforcement

# Harvest Drugs@FDA
uv run miner openfda harvest "sponsor_name:pfizer" --endpoint drugsfda
```

### Python API

#### Using the API Wrapper

```python
from biomed_tools.openfda.api import OpenFDAAPI

api = OpenFDAAPI()

# Search Adverse Events
events = api.search_events("patient.drug.medicinalproduct:aspirin", limit=10)
if events:
    print(f"Found {events['meta']['results']['total']} events")

# Search Labels
labels = api.search_labels("openfda.brand_name:tylenol", limit=5)
```

#### Running the Harvester

```python
from biomed_tools.openfda import harvester

# Harvest Adverse Events
harvester.run_openfda_query("aspirin", endpoint="event", max_records=100)

# Harvest Labels
harvester.run_openfda_query("ibuprofen", endpoint="label", max_records=50)
```

## Configuration

Configuration is handled in `src/biomed_tools/openfda/config.py`. Key settings:
- `DB_URL`: Path to the SQLite database (default: `db/openfda.db`).
- `LOG_FILE`: Path to the log file (default: `logs/openfda.log`).
- `API_BASE_URL`: `https://api.fda.gov/drug`

## Database Models

The module uses SQLAlchemy to map OpenFDA JSON responses to relational tables.
- `DrugEvent`: Stores safety reports, patient demographics, reaction outcomes.
- `DrugLabel`: Stores SPL set IDs, brand/generic names, effective time.
- `DrugNDC`: Stores product IDs, packaging, marketing category.
- `DrugEnforcement`: Stores recall numbers, reasons, status.
- `DrugAtFDA`: Stores application numbers, sponsors, products.

Each model also stores the full original JSON in a `data` column for flexibility.
