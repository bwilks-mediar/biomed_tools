# UniProt Module

The `uniprot` module allows you to search and harvest protein data from the UniProt Knowledgebase (UniProtKB).

## CLI Usage

### Harvest Data

To search for proteins and save them to the database:

```bash
uv run miner uniprot harvest "gene:brca1" --max-records 100
```

This will:
1. Search UniProtKB for proteins matching "gene:brca1".
2. Fetch up to 100 records (default is 9999).
3. Store the results in `db/uniprot.db`.

## Python Usage

You can use the module programmatically in your Python scripts.

### Fetch Data

```python
from biomed_tools.uniprot import harvester

# Run a query and store results in the database
count = harvester.run_uniprot_query("organism_id:9606 AND gene:tp53", max_records=50)
print(f"Stored {count} new proteins.")
```

### Direct API Access

```python
from biomed_tools.uniprot.api import UniprotAPI

api = UniprotAPI()

# Search for proteins
data, next_link = api.search_proteins("gene:brca1", size=10)
for protein in data["results"]:
    print(protein["primaryAccession"], protein["uniProtkbId"])

# Fetch a single protein
protein = api.fetch_protein("P04637")
print(protein["proteinDescription"]["recommendedName"]["fullName"]["value"])
```

## Database Schema

The module uses a SQLite database (`db/uniprot.db`) with the following main tables:

- **proteins**: Stores protein details (accession, name, gene, organism, sequence, etc.).
- **search_terms**: Stores normalized search queries.
- **search_to_proteins**: Link table between search terms and proteins.
