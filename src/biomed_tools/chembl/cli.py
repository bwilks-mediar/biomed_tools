"""Command-line interface for the ChEMBL Miner."""

from loguru import logger
from . import harvester, models, config

def add_subparsers(subparsers):
    """Add subparsers for ChEMBL commands."""
    # --- Harvester command ---
    parser_harvest = subparsers.add_parser(
        "harvest", help="Download data from ChEMBL."
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
    """Main function for the ChEMBL miner CLI."""
    config.configure_logging()

    if args.subcommand == "harvest":
        harvester.run_chembl_query(
            args.query, max_records=args.max_records
        )
    elif args.subcommand == "clear":
        logger.info("Clearing the database...")
        models.drop_tables()
        logger.info("Database cleared.")
    elif args.subcommand == "migrate":
        logger.info("Creating database tables if they don't exist...")
        models.create_tables()
        logger.info("Database tables checked/created.")
