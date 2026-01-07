# Biomed Tools

A Python library for interacting with various biomedical data sources.

## Modules

Detailed documentation for each module:

- [Clinical Trials](docs/clinical_trials.md)
- [GEO (Gene Expression Omnibus)](docs/geo.md)
- [PubMed](docs/pubmed.md)
- [RxNav](docs/rxnav.md)
- [DailyMed](docs/daily_med.md)
- [Orange Book](docs/orange_book.md)
- [Playwright Scraper](docs/playwright.md)
- [UniProt](docs/uniprot.md)
- [ChEMBL](docs/chembl.md)

## Installation

This project is managed with [uv](https://github.com/astral-sh/uv).

```bash
uv sync
```

## CLI Usage

The project provides a unified CLI tool named `miner` to interact with various harvesters and tools.

```bash
# List available tools
uv run miner --help

# Clinical Trials
uv run miner clinical-trials harvest "lung cancer"

# GEO
uv run miner geo harvest

# PubMed
uv run miner pubmed harvest "crispr"

# UniProt
uv run miner uniprot harvest "gene:brca1"

# ChEMBL
uv run miner chembl harvest "aspirin"

# OpenFDA
uv run miner openfda harvest "aspirin" --endpoint event
```

## Python Usage

You can also use the modules directly in Python.

### Clinical Trials
```python
from biomed_tools.clinical_trials import harvester
harvester.run_clinical_trials_query("lung cancer", max_records=100)
```

### PubMed
```python
from biomed_tools.pubmed import harvester
harvester.run_pubmed_query("asthma", max_records=50)
```

### UniProt
```python
from biomed_tools.uniprot import harvester
harvester.run_uniprot_query("gene:brca1", max_records=20)
```

### ChEMBL
```python
from biomed_tools.chembl import harvester
harvester.run_chembl_query("aspirin", max_records=100)
```

### OpenFDA
```python
from biomed_tools.openfda import harvester
harvester.run_openfda_query("aspirin", endpoint="event", max_records=100)
```

*(See individual module documentation for more examples)*

## Project Structure

- `src/biomed_tools/`: Source code.
- `tests/`: Unit tests.
- `docs/`: Module documentation.
- `orange_book_data/`: Directory where Orange Book data is downloaded.
- `db/`: Directory where SQLite databases are stored.
- `logs/`: Directory where logs are stored.

## ToDo

Future enhancements and tools to be added:

- [x] **OpenFDA**: Broader integration with other OpenFDA endpoints (Device events, Food enforcement, etc.).
- [x] **ChemBL**: Integration for bioactivity data.
- [x] **UniProt**: Programmatic access to protein sequence and functional information.
