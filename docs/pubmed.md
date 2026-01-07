# PubMed Module

The PubMed module allows you to interact with the NCBI PubMed database to search and retrieve biomedical literature. It handles rate limiting, parsing of Medline records, and storage into a relational database.

## Features

- **Harvester**: Downloads articles based on a search query. Supports large queries by splitting them by year.
- **Full Text**: Can attempt to fetch full text for articles with a PMCID.
- **Database Models**: Stores publications, authors, affiliations, mesh terms, etc. in a local SQLite database.
- **CLI**: Command-line interface for harvesting, updating, and querying.
- **API Wrapper**: Provides direct access to PubMed E-utilities with built-in rate limiting and error handling.

## Usage

### CLI

The CLI is the easiest way to get started.

```bash
# Harvest articles
miner pubmed harvest "crispr" --max-records 100

# Harvest with date range (useful for large queries)
miner pubmed harvest "cancer" --start-year 2020 --end-year 2021

# Harvest and attempt to download full text
miner pubmed harvest "covid-19" --full-text

# Download full text for existing articles in the DB that have a PMCID
miner pubmed full-text

# Update records with missing identifiers (PMCID/DOI)
miner pubmed update

# Download specific articles by PMIDs
miner pubmed download-pmids 12345678 87654321
```

### Python API

You can use the module programmatically in your Python scripts.

#### Harvesting Data

```python
from biomed_tools.pubmed import harvester

# Run a query and store results in DB
# Returns the number of new articles downloaded
count = harvester.run_pubmed_query("asthma", max_records=50)
print(f"Downloaded {count} new articles.")

# Harvests data year by year to avoid limits and manage large datasets
harvester.harvest_large_query("idiopathic pulmonary fibrosis", start_year=2015, end_year=2020)

# Download specific PMIDs
harvester.download_by_pmids(["12345678", "87654321"], fetch_text=True)
```

#### Direct API Access

For more granular control, you can use the `api` module to interact directly with NCBI E-utilities.

```python
from biomed_tools.pubmed import api
from Bio import Entrez

# Fetch full text for a PMC ID
full_text = api.fetch_full_text("PMC1234567")
if full_text:
    print(full_text[:100])

# Make a safe request to Entrez (handles rate limits)
handle = api.safe_entrez_request(
    Entrez.esummary,
    db="pubmed",
    id="12345678",
    retmode="json"
)
data = handle.read()
handle.close()
print(data)

# Fetch publication details for a list of PMIDs
details = api.fetch_publication_details_from_pubmed(["12345678", "87654321"])
print(details)
```

#### Database Access

You can interact with the stored data using SQLAlchemy models.

```python
from biomed_tools.pubmed.models import get_session, Publication

session = get_session()

# Query publications
pubs = session.query(Publication).filter(Publication.title.ilike("%idiopathic pulmonary fibrosis%")).limit(10).all()

for pub in pubs:
    print(f"{pub.pmid}: {pub.title}")
    if pub.full_text:
        print("  (Full text available)")

session.close()
```

## Configuration

Configuration is handled in `src/biomed_tools/pubmed/config.py`. Key settings:
- `ENTREZ_EMAIL`: Your email (Required for NCBI Entrez API). Set in `.env` file.
- `API_KEY`: NCBI API Key (Optional but recommended for higher rate limits). Set in `.env` file.
- `DB_URL`: Path to the SQLite database (default: `db/pubmed.db`).
- `LOG_FILE`: Path to the log file (default: `logs/pubmed.log`).

Logging is automatically configured when using the CLI or importing the `harvester` module.
