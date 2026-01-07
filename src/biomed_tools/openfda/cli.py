"""Command-line interface for the OpenFDA miner."""

import argparse
from loguru import logger
from .. import openfda

def add_subparsers(subparsers):
    """Add subparsers for OpenFDA commands."""
    # --- Harvester command ---
    parser_harvest = subparsers.add_parser(
        "harvest", help="Download data from OpenFDA."
    )
    parser_harvest.add_argument("query", help="The search query to run (e.g. 'patient.drug.medicinalproduct:aspirin').")
    parser_harvest.add_argument(
        "--endpoint",
        type=str,
        default="event",
        choices=["event", "label", "ndc", "enforcement", "drugsfda"],
        help="OpenFDA endpoint to query (default: event)."
    )
    parser_harvest.add_argument(
        "--max-records",
        type=int,
        default=100,
        help="Maximum number of records to download (max 5000).",
    )

def main(args):
    """Main function for the OpenFDA miner CLI."""
    openfda.config.configure_logging()

    if args.subcommand == "harvest":
        openfda.harvester.run_openfda_query(
            args.query, endpoint=args.endpoint, max_records=args.max_records
        )
