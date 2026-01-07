# Orange Book Module

The Orange Book module provides access to the FDA's "Approved Drug Products with Therapeutic Equivalence Evaluations" (Orange Book) data.

## Features

- **Automatic Download**: Downloads the latest data from the FDA website if local files are missing or stale (older than 30 days).
- **Database Storage**: Parses Products, Patents, and Exclusivity data and stores them in a normalized SQLite database.
- **CLI Support**: Provides a command-line interface to harvest data.

## CLI Usage

You can use the `miner` CLI to interact with the Orange Book module.

```bash
# Harvest data (download and populate database)
uv run miner orange-book harvest

# Force download of fresh data
uv run miner orange-book harvest --force

# Harvest without dropping existing tables (update)
uv run miner orange-book harvest --no-refresh

# Clear the database
uv run miner orange-book clear
```

## Python Usage

You can also use the module directly in Python.

```python
from biomed_tools.orange_book import harvester, models
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Run the harvest process
harvester.harvest()

# Query the database
engine = models.get_engine()
Session = sessionmaker(bind=engine)
session = Session()

# Get first 5 products
products = session.query(models.Product).limit(5).all()
for p in products:
    print(f"{p.trade_name} ({p.ingredient})")
    for patent in p.patents:
        print(f"  - Patent: {patent.patent_no} (Expires: {patent.patent_expire_date_text})")

session.close()
```

## Database Schema

The module uses a SQLite database with the following main tables:

- **products**: Core product information (Trade Name, Ingredient, Applicant, etc.).
- **patents**: Patent information linked to products.
- **exclusivity**: Exclusivity information linked to products.

## Configuration

- `DB_URL`: SQLite database path (default: `db/orange_book.db`).
- `DATA_DIR`: Directory to store the downloaded text files (default: `orange_book_data`).
- `MAX_AGE_DAYS`: Maximum age of local files before a re-download is triggered (default: 30 days).
