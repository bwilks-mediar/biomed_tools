"""Command-line interface for the RxNav miner."""

import argparse
from loguru import logger
from .. import rxnav

def add_subparsers(subparsers):
    """Add subparsers for RxNav commands."""
    # --- Harvester command ---
    parser_harvest = subparsers.add_parser(
        "harvest", help="Fetch drug information from RxNav."
    )
    parser_harvest.add_argument("query", help="The drug name to search for.")

    # --- Clear command ---
    subparsers.add_parser("clear", help="Clear the database.")

    # --- Migrate command ---
    subparsers.add_parser("migrate", help="Create database tables.")


def main(args):
    """Main function for the RxNav miner CLI."""
    rxnav.config.configure_logging()

    if args.subcommand == "harvest":
        rxnav.harvester.run_rxnav_query(args.query)
    elif args.subcommand == "clear":
        logger.info("Clearing the database...")
        rxnav.models.drop_tables()
        logger.info("Database cleared.")
    elif args.subcommand == "migrate":
        logger.info("Creating database tables if they don't exist...")
        rxnav.models.create_tables()
        logger.info("Database tables checked/created.")
