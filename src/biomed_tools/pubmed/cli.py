"""Command-line interface for the PubMed miner."""

import argparse

from loguru import logger

from .. import pubmed


def add_subparsers(subparsers):
    """Add subparsers for PubMed commands."""
    # --- Harvester command ---
    parser_harvest = subparsers.add_parser(
        "harvest",
        help="Download data from PubMed.",
        formatter_class=argparse.RawTextHelpFormatter,
        description="""
        Download data from PubMed using a search query.
        This command allows for fine-grained control over the data fetching process.

        Examples:
        # Basic query
        miner pubmed harvest "asthma[mesh]"

        # Query with a date range
        miner pubmed harvest "covid-19" --start-year 2020 --end-year 2021

        # Fetch full text for articles
        miner pubmed harvest "crispr" --full-text

        # Use a specific sort order
        miner pubmed harvest "gene therapy" --sort pub_date
        """,
    )
    parser_harvest.add_argument(
        "--full-text",
        action="store_true",
        help="Attempt to download full text for articles with PMCID.",
    )
    parser_harvest.add_argument("query", help="The search query to run on PubMed.")
    parser_harvest.add_argument(
        "--email", help="Email for Entrez API (overrides .env setting)."
    )
    parser_harvest.add_argument(
        "--max-records",
        type=int,
        default=10000,
        help="Maximum number of records to download.",
    )
    parser_harvest.add_argument(
        "--start-year", type=int, help="Start year for date-range-based harvesting."
    )
    parser_harvest.add_argument(
        "--end-year", type=int, help="End year for date-range-based harvesting."
    )
    # ESearch parameters
    parser_harvest.add_argument(
        "--esearch-rettype",
        default="uilist",
        help="ESearch rettype parameter. (e.g., uilist, count)",
    )
    parser_harvest.add_argument(
        "--esearch-retmode",
        default="xml",
        help="ESearch retmode parameter. (e.g., xml, json)",
    )
    parser_harvest.add_argument(
        "--sort",
        default="relevance",
        help="ESearch sort parameter. (e.g., relevance, pub_date, author, journalname)",
    )
    parser_harvest.add_argument(
        "--field", help="ESearch field parameter. (e.g., title, author)"
    )
    parser_harvest.add_argument(
        "--idtype", help="ESearch idtype parameter. (e.g., acc)"
    )
    parser_harvest.add_argument(
        "--datetype",
        default="pdat",
        help="ESearch datetype parameter. (e.g., pdat, mdat, edat)",
    )
    parser_harvest.add_argument(
        "--reldate",
        type=int,
        help="ESearch reldate parameter. (e.g., 30, 60, 90)",
    )
    parser_harvest.add_argument(
        "--mindate", help="ESearch mindate parameter. (e.g., YYYY/MM/DD)"
    )
    parser_harvest.add_argument(
        "--maxdate", help="ESearch maxdate parameter. (e.g., YYYY/MM/DD)"
    )
    # EFetch parameters
    parser_harvest.add_argument(
        "--efetch-rettype",
        default="medline",
        help="EFetch rettype parameter. (e.g., medline, abstract, fasta)",
    )
    parser_harvest.add_argument(
        "--efetch-retmode",
        default="text",
        help="EFetch retmode parameter. (e.g., text, xml, html)",
    )
    parser_harvest.add_argument(
        "--strand", help="EFetch strand parameter. (e.g., 1, 2)"
    )
    parser_harvest.add_argument(
        "--seq-start", type=int, help="EFetch seq_start parameter."
    )
    parser_harvest.add_argument(
        "--seq-stop", type=int, help="EFetch seq_stop parameter."
    )
    parser_harvest.add_argument(
        "--complexity", type=int, help="EFetch complexity parameter. (e.g., 0, 1, 2, 3, 4)"
    )

    # --- Query command ---
    parser_query = subparsers.add_parser("query", help="Query the local database.")
    parser_query.add_argument(
        "keyword", nargs="?", default=None, help="Keyword to search for."
    )
    parser_query.add_argument(
        "--summarize", action="store_true", help="Print a summary of the database."
    )

    # --- Update command ---
    parser_update = subparsers.add_parser(
        "update", help="Update records with missing identifiers."
    )
    parser_update.add_argument(
        "--rate-limit",
        type=int,
        default=3,
        help="Requests per second to PubMed.",
    )
    parser_update.add_argument(
        "--batch-size",
        type=int,
        default=200,
        help="Number of records to update per batch.",
    )
    parser_update.add_argument(
        "--recheck-days",
        type=int,
        default=30,
        help="Number of days to wait before rechecking a publication.",
    )

    # --- Clear command ---
    subparsers.add_parser("clear", help="Clear the database.")

    # --- Migrate command ---
    subparsers.add_parser("migrate", help="Create database tables.")

    # --- Full-text command ---
    parser_full_text = subparsers.add_parser(
        "full-text", help="Download full text for existing articles."
    )
    parser_full_text.add_argument(
        "--batch-size",
        type=int,
        default=200,
        help="Number of records to update per batch.",
    )
    parser_full_text.add_argument(
        "--recheck-days",
        type=int,
        default=30,
        help="Number of days to wait before rechecking a publication.",
    )

    # --- Download by PMIDs command ---
    parser_download_pmids = subparsers.add_parser(
        "download-pmids",
        help="Download articles from a list of PMIDs.",
        formatter_class=argparse.RawTextHelpFormatter,
        description="""
        Download articles from a list of PMIDs.
        This command allows for downloading specific articles by their PubMed ID.

        Examples:
        # Download a single article
        miner pubmed download-pmids 12345678

        # Download multiple articles
        miner pubmed download-pmids 12345678 87654321
        """,
    )
    parser_download_pmids.add_argument(
        "pmids", nargs="+", help="A list of PMIDs to download."
    )
    parser_download_pmids.add_argument(
        "--full-text",
        action="store_true",
        help="Attempt to download full text for articles with PMCID.",
    )
    parser_download_pmids.add_argument(
        "--search-term",
        default="Manually Added by PMID",
        help="The search term to associate with the downloaded articles.",
    )


def main(args):
    """Main function for the PubMed miner CLI."""
    pubmed.config.configure_logging()

    if args.subcommand == "harvest":
        # If a CLI email is provided, it overrides the one from the .env file.
        if args.email:
            pubmed.config.ENTREZ_EMAIL = args.email
        
        # The config module will have already raised an error if no email is available.
        
        if args.start_year and args.end_year:
            pubmed.harvester.harvest_large_query(
                args.query,
                args.start_year,
                args.end_year,
                fetch_text=args.full_text,
            )
        else:
            pubmed.harvester.run_pubmed_query(
                query=args.query,
                max_records=args.max_records,
                fetch_text=args.full_text,
                esearch_rettype=args.esearch_rettype,
                esearch_retmode=args.esearch_retmode,
                sort=args.sort,
                field=args.field,
                idtype=args.idtype,
                datetype=args.datetype,
                reldate=args.reldate,
                mindate=args.mindate,
                maxdate=args.maxdate,
                efetch_rettype=args.efetch_rettype,
                efetch_retmode=args.efetch_retmode,
                strand=args.strand,
                seq_start=args.seq_start,
                seq_stop=args.seq_stop,
                complexity=args.complexity,
            )
    elif args.subcommand == "query":
        session = pubmed.query.get_db_session()
        if args.summarize:
            pubmed.query.summarize_database(session)
        if args.keyword:
            df = pubmed.query.find_publications_by_keyword(session, args.keyword)
            print(df)
        session.close()
    elif args.subcommand == "update":
        logger.info("Updating publications with missing identifiers...")
        pubmed.updater.find_and_update_missing_identifiers(
            rate_limit=args.rate_limit,
            batch_size=args.batch_size,
            recheck_days=args.recheck_days,
        )
        logger.info("Finished updating publications.")
    elif args.subcommand == "clear":
        logger.info("Clearing the database...")
        pubmed.models.drop_tables()
        logger.info("Database cleared.")
    elif args.subcommand == "migrate":
        logger.info("Creating database tables if they don't exist...")
        pubmed.models.create_tables()
        logger.info("Database tables checked/created.")
    elif args.subcommand == "full-text":
        logger.info("Downloading full text for existing articles...")
        pubmed.harvester.download_full_text_for_existing_articles(
            batch_size=args.batch_size, recheck_days=args.recheck_days
        )
        logger.info("Finished downloading full text.")
    elif args.subcommand == "download-pmids":
        logger.info(f"Downloading articles for {len(args.pmids)} PMIDs...")
        pubmed.harvester.download_by_pmids(
            pmids=args.pmids,
            fetch_text=args.full_text,
            search_term=args.search_term,
        )
        logger.info("Finished downloading articles by PMID.")
