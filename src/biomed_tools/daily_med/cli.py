"""Command-line interface for the DailyMed miner."""

import argparse
from loguru import logger
from . import config, harvester, models

def add_subparsers(subparsers):
    """Add subparsers for DailyMed commands."""
    # --- Harvester command ---
    parser_harvest = subparsers.add_parser(
        "harvest", help="Download data from DailyMed."
    )
    parser_harvest.add_argument("query", help="The search query for drugs (e.g., 'tylenol').")

    # --- Clear command ---
    subparsers.add_parser("clear", help="Clear the database.")

    # --- Migrate command ---
    subparsers.add_parser("migrate", help="Create database tables.")

def main(args):
    """Main function for the DailyMed miner CLI."""
    config.configure_logging()

    if args.subcommand == "harvest":
        harvester.run_daily_med_query(args.query)
    elif args.subcommand == "clear":
        logger.info("Clearing the database...")
        models.drop_tables()
        logger.info("Database cleared.")
    elif args.subcommand == "migrate":
        logger.info("Creating database tables if they don't exist...")
        models.create_tables()
        logger.info("Database tables checked/created.")
