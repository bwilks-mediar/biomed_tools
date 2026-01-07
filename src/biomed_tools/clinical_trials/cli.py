"""Command-line interface for the Clinical Trials miner."""

import argparse

from loguru import logger

from .. import clinical_trials


def add_subparsers(subparsers):
    """Add subparsers for Clinical Trials commands."""
    # --- Harvester command ---
    parser_harvest = subparsers.add_parser(
        "harvest", help="Download data from ClinicalTrials.gov."
    )
    parser_harvest.add_argument("query", help="The search query to run.")
    parser_harvest.add_argument(
        "--max-records",
        type=int,
        default=9999,
        help="Maximum number of records to download.",
    )

    # --- Clear command ---
    subparsers.add_parser("clear", help="Clear the database.")

    # --- Migrate command ---
    subparsers.add_parser("migrate", help="Create database tables.")


def main(args):
    """Main function for the Clinical Trials miner CLI."""
    clinical_trials.config.configure_logging()

    if args.subcommand == "harvest":
        clinical_trials.harvester.run_clinical_trials_query(
            args.query, max_records=args.max_records
        )
    elif args.subcommand == "clear":
        logger.info("Clearing the database...")
        clinical_trials.models.drop_tables()
        logger.info("Database cleared.")
    elif args.subcommand == "migrate":
        logger.info("Creating database tables if they don't exist...")
        clinical_trials.models.create_tables()
        logger.info("Database tables checked/created.")
