"""Command-line interface for the Orange Book miner."""

import argparse
from loguru import logger
from . import harvester, models, config

def add_subparsers(subparsers):
    """Add subparsers for Orange Book commands."""
    # --- Harvest command ---
    parser_harvest = subparsers.add_parser(
        "harvest", help="Download and process Orange Book data."
    )
    parser_harvest.add_argument(
        "--force", "-f", action="store_true", help="Force download of fresh data."
    )
    parser_harvest.add_argument(
        "--no-refresh", action="store_false", dest="refresh", help="Do not drop existing tables (default is to drop)."
    )
    # Default refresh to True
    parser_harvest.set_defaults(refresh=True)

    # --- Clear command ---
    subparsers.add_parser("clear", help="Clear the database.")

    # --- Migrate command ---
    subparsers.add_parser("migrate", help="Create database tables.")

def main(args):
    """Main function for the Orange Book miner CLI."""
    config.configure_logging()

    if args.subcommand == "harvest":
        harvester.harvest(force_download=args.force, full_refresh=args.refresh)
    elif args.subcommand == "clear":
        logger.info("Clearing the database...")
        models.drop_tables()
        logger.info("Database cleared.")
    elif args.subcommand == "migrate":
        logger.info("Creating database tables if they don't exist...")
        models.create_tables()
        logger.info("Database tables checked/created.")
