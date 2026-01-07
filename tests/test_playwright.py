from biomed_tools.playwright import harvester, cli
from biomed_tools.playwright.scrapers.generic_scraper import GenericScraper
import argparse
import pytest

def test_scraper_registry():
    """Test that all expected scrapers are registered."""
    expected_scrapers = ["endpoints", "fierce", "biopharma", "biospace"]
    for scraper in expected_scrapers:
        assert scraper in harvester.SCRAPER_REGISTRY
        assert issubclass(harvester.SCRAPER_REGISTRY[scraper], GenericScraper)

def test_cli_setup():
    """Test that the CLI arguments are set up correctly."""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    cli.add_subparsers(subparsers)
    
    # Verify harvest command is added
    assert "harvest" in subparsers.choices

def test_scraper_imports():
    """Test that we can import all scraper classes."""
    from biomed_tools.playwright.scrapers.endpoints_scraper import EndpointsScraper
    from biomed_tools.playwright.scrapers.fierce_biotech_scraper import FierceBiotechScraper
    from biomed_tools.playwright.scrapers.biopharma_dive_scraper import BioPharmaDiveScraper
    from biomed_tools.playwright.scrapers.biospace_scraper import BioSpaceScraper

    assert EndpointsScraper
    assert FierceBiotechScraper
    assert BioPharmaDiveScraper
    assert BioSpaceScraper
