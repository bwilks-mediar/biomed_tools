# Clinical Trials Module

The Clinical Trials module allows you to interact with the ClinicalTrials.gov API (v2) to fetch, process, and store clinical trial data.

## Features

- **API Client**: Wrapper around ClinicalTrials.gov API with automatic retries and pagination.
- **Harvester**: Downloads trials based on a search query and stores them in a local SQLite database.
- **Database Models**: SQLAlchemy models for structured storage of trial data (conditions, interventions, outcomes, etc.).
- **CLI**: Command-line interface for easy interaction.

## Usage

### CLI

You can use the CLI to harvest data:

```bash
# Harvest trials for a specific query
miner clinical-trials harvest "lung cancer" --max-records 100

# Clear the database
miner clinical-trials clear

# Create/Migrate database tables
miner clinical-trials migrate
```

### Python API

#### Using the API Wrapper

```python
from biomed_tools.clinical_trials.api import ClinicalTrialsAPI

api = ClinicalTrialsAPI()
params = {"query.cond": "asthma", "pageSize": 10}
data = api.list_studies(params=params)

for study in data.get("studies", []):
    print(study["protocolSection"]["identificationModule"]["nctId"])
```

#### Running the Harvester

```python
from biomed_tools.clinical_trials import harvester

# This will download trials and store them in the configured SQLite database
harvester.run_clinical_trials_query("diabetes", max_records=50)
```

## Configuration

Configuration is handled in `src/biomed_tools/clinical_trials/config.py`. Key settings:
- `DB_URL`: Path to the SQLite database (default: `db/clinical_trials.db`).
- `LOG_FILE`: Path to the log file (default: `logs/clinical_trials.log`).

Logging is automatically configured when using the CLI or importing the `harvester` module.
