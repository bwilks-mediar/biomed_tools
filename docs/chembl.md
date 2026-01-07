# ChEMBL Module

The ChEMBL module allows you to search for molecules and bioactivity data from the ChEMBL database.

## CLI Usage

The `miner` CLI provides a `chembl` command with subcommands.

### Harvest Data

Search for molecules by name and save them to the local SQLite database.

```bash
uv run miner chembl harvest "aspirin" --max-records 50
```

### Manage Database

Clear the database:

```bash
uv run miner chembl clear
```

Initialize/Migrate database tables:

```bash
uv run miner chembl migrate
```

## Python Usage

You can use the `harvester` module directly in Python scripts.

```python
from biomed_tools.chembl import harvester, fetch_all_molecules

# Search for molecules matching "aspirin"
count = harvester.run_chembl_query("aspirin", max_records=100)
print(f"Downloaded {count} molecules.")
```

## Data Model

The module uses SQLAlchemy to model the data. Key tables include:

- `molecules`: Core molecule information (ChEMBL ID, preferred name, structure info, approval info, flags).
- `molecule_properties`: Physicochemical properties (Molecular Weight, LogP, PSA, HBA/HBD, etc.).
- `molecule_synonyms`: Synonyms for the molecule.
- `molecule_atc`: ATC classifications.
- `molecule_cross_refs`: Cross-references to other databases.
- `mechanisms`: Mechanism of action data.
- `search_terms`: Tracks search queries.
- `search_to_molecule`: Links search terms to found molecules.

## Configuration

Configuration is handled in `src/biomed_tools/chembl/config.py`.

- **Database**: `db/chembl.db`
- **Logs**: `logs/chembl.log`
