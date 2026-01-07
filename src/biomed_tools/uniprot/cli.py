"""CLI commands for UniProt Miner."""

import argparse
from typing import Optional

from .harvester import run_uniprot_query


def harvest_command(args: argparse.Namespace):
    """Handles the 'harvest' command."""
    query = args.query
    max_records = args.max_records
    run_uniprot_query(query, max_records)


def add_subparsers(subparsers):
    """Adds subparsers for UniProt commands."""
    harvest_parser = subparsers.add_parser("harvest", help="Fetch data from UniProt")
    harvest_parser.add_argument("query", type=str, help="Search query (e.g., 'gene:brca1')")
    harvest_parser.add_argument(
        "--max-records",
        type=int,
        default=9999,
        help="Maximum number of records to fetch",
    )
    harvest_parser.set_defaults(func=harvest_command)


def main(args: argparse.Namespace):
    """Main entry point for the UniProt CLI."""
    if hasattr(args, "func"):
        args.func(args)
    else:
        print("No subcommand specified. Use --help for more information.")
