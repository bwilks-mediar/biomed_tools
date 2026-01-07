"""Command-line interface for the GEO miner."""

import argparse
from loguru import logger
from . import harvester, utils, config

def add_subparsers(subparsers):
    """Add subparsers for GEO commands."""
    # --- Harvester command ---
    parser_harvest = subparsers.add_parser(
        "harvest", help="Download the GEOmetadb SQLite file."
    )

    # --- Query command ---
    parser_query = subparsers.add_parser("query", help="Query the local database.")
    parser_query.add_argument(
        "keyword", nargs="?", default=None, help="Keyword to search for."
    )
    
    # --- Clear command ---
    subparsers.add_parser("clear", help="Remove the local GEOmetadb database.")


def main(args):
    """Main function for the GEO miner CLI."""
    config.configure_logging()

    if args.subcommand == "harvest":
        harvester.download_geometadb()
    elif args.subcommand == "query":
        if args.keyword:
            df = utils.find_gse_by_keyword(args.keyword)
            if not df.empty:
                print(df)
            else:
                logger.info("No results found.")
        else:
            logger.warning("Please provide a keyword to query.")
    elif args.subcommand == "clear":
        db_path = config.get_db_path()
        if db_path.exists():
            logger.info(f"Removing database at {db_path}...")
            db_path.unlink()
            logger.info("Database removed.")
        else:
            logger.info("No database found to remove.")
