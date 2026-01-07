import argparse
import sys
from biomed_tools.clinical_trials import cli as clinical_trials_cli
from biomed_tools.geo import cli as geo_cli
from biomed_tools.pubmed import cli as pubmed_cli
from biomed_tools.playwright import cli as playwright_cli
from biomed_tools.orange_book import cli as orange_book_cli
from biomed_tools.daily_med import cli as daily_med_cli
from biomed_tools.rxnav import cli as rxnav_cli
from biomed_tools.uniprot import cli as uniprot_cli
from biomed_tools.chembl import cli as chembl_cli
from biomed_tools.openfda import cli as openfda_cli

def main():
    parser = argparse.ArgumentParser(description="Biomed Tools CLI")
    subparsers = parser.add_subparsers(dest="tool", help="Tool to use")

    # Clinical Trials
    ct_parser = subparsers.add_parser("clinical-trials", help="Clinical Trials tools")
    ct_subparsers = ct_parser.add_subparsers(dest="subcommand", help="Clinical Trials commands")
    clinical_trials_cli.add_subparsers(ct_subparsers)

    # GEO
    geo_parser = subparsers.add_parser("geo", help="GEO tools")
    geo_subparsers = geo_parser.add_subparsers(dest="subcommand", help="GEO commands")
    geo_cli.add_subparsers(geo_subparsers)

    # PubMed
    pubmed_parser = subparsers.add_parser("pubmed", help="PubMed tools")
    pubmed_subparsers = pubmed_parser.add_subparsers(dest="subcommand", help="PubMed commands")
    pubmed_cli.add_subparsers(pubmed_subparsers)

    # Playwright
    playwright_parser = subparsers.add_parser("playwright", help="Playwright tools")
    playwright_subparsers = playwright_parser.add_subparsers(dest="subcommand", help="Playwright commands")
    playwright_cli.add_subparsers(playwright_subparsers)

    # Orange Book
    orange_book_parser = subparsers.add_parser("orange-book", help="Orange Book tools")
    orange_book_subparsers = orange_book_parser.add_subparsers(dest="subcommand", help="Orange Book commands")
    orange_book_cli.add_subparsers(orange_book_subparsers)

    # DailyMed
    daily_med_parser = subparsers.add_parser("daily-med", help="DailyMed tools")
    daily_med_subparsers = daily_med_parser.add_subparsers(dest="subcommand", help="DailyMed commands")
    daily_med_cli.add_subparsers(daily_med_subparsers)

    # RxNav
    rxnav_parser = subparsers.add_parser("rxnav", help="RxNav tools")
    rxnav_subparsers = rxnav_parser.add_subparsers(dest="subcommand", help="RxNav commands")
    rxnav_cli.add_subparsers(rxnav_subparsers)

    # UniProt
    uniprot_parser = subparsers.add_parser("uniprot", help="UniProt tools")
    uniprot_subparsers = uniprot_parser.add_subparsers(dest="subcommand", help="UniProt commands")
    uniprot_cli.add_subparsers(uniprot_subparsers)

    # ChEMBL
    chembl_parser = subparsers.add_parser("chembl", help="ChEMBL tools")
    chembl_subparsers = chembl_parser.add_subparsers(dest="subcommand", help="ChEMBL commands")
    chembl_cli.add_subparsers(chembl_subparsers)

    # OpenFDA
    openfda_parser = subparsers.add_parser("openfda", help="OpenFDA tools")
    openfda_subparsers = openfda_parser.add_subparsers(dest="subcommand", help="OpenFDA commands")
    openfda_cli.add_subparsers(openfda_subparsers)

    args = parser.parse_args()

    if args.tool == "clinical-trials":
        clinical_trials_cli.main(args)
    elif args.tool == "geo":
        geo_cli.main(args)
    elif args.tool == "pubmed":
        pubmed_cli.main(args)
    elif args.tool == "playwright":
        playwright_cli.main(args)
    elif args.tool == "orange-book":
        orange_book_cli.main(args)
    elif args.tool == "daily-med":
        daily_med_cli.main(args)
    elif args.tool == "rxnav":
        rxnav_cli.main(args)
    elif args.tool == "uniprot":
        uniprot_cli.main(args)
    elif args.tool == "chembl":
        chembl_cli.main(args)
    elif args.tool == "openfda":
        openfda_cli.main(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
