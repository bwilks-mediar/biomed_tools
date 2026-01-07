"""Command-line interface for the Playwright scraper."""

import argparse
import asyncio
from loguru import logger
from . import harvester as playwright_main

def add_subparsers(subparsers):
    """Add subparsers for Playwright commands."""
    # --- Harvest command ---
    parser_harvest = subparsers.add_parser(
        "harvest", help="Run a playwright scraper."
    )
    parser_harvest.add_argument(
        "scraper_name",
        type=str,
        help="The name of the scraper to run."
    )
    parser_harvest.add_argument(
        "-d", "--debug",
        action="store_true",
        help="Enable debug mode. Overrides config setting. Logs verbose output and network traffic."
    )
    parser_harvest.add_argument(
        "--headless",
        action="store_true",
        help="Run the browser in headless mode. Overrides config setting."
    )
    parser_harvest.add_argument(
        "--no-headless",
        dest='headless',
        action='store_false',
        help="Run the browser in non-headless (headed) mode. Overrides config setting."
    )
    parser_harvest.set_defaults(headless=None)

def main(args):
    """Main function for the Playwright miner CLI."""
    if args.subcommand == "harvest":
        # We need to run the async function
        asyncio.run(playwright_main.run_scraper(args))
