"""Core logic for running Playwright scrapers."""

import os
import asyncio
from dotenv import load_dotenv
from loguru import logger
from playwright.async_api import async_playwright

from . import config
from . import utils

# --- Scraper Imports and Registry ---
# Import all your scraper classes here
from .scrapers.endpoints_scraper import EndpointsScraper
from .scrapers.fierce_biotech_scraper import FierceBiotechScraper
from .scrapers.biopharma_dive_scraper import BioPharmaDiveScraper
from .scrapers.biospace_scraper import BioSpaceScraper

# The registry maps a command-line name to a scraper class.
# This makes it easy to add new scrapers.
SCRAPER_REGISTRY = {
    "endpoints": EndpointsScraper,
    "fierce": FierceBiotechScraper, 
    "biopharma": BioPharmaDiveScraper, 
    "biospace": BioSpaceScraper,
    # "another": AnotherScraper, # Example for the future
}


async def run_scraper(args):
    """Initializes and runs the specified scraper based on command-line arguments."""
    # --- Configuration Loading ---
    load_dotenv()

    # Determine run-time settings, prioritizing command-line flags over config file
    is_debug = args.debug or config.DEBUG_MODE
    is_headless = args.headless if args.headless is not None else config.HEADLESS_MODE

    # Use the 'is_debug' variable to setup logging correctly
    utils.setup_logging(debug=is_debug)

    scraper_name = args.scraper_name
    ScraperClass = SCRAPER_REGISTRY.get(scraper_name)

    if not ScraperClass:
        logger.critical(f"Scraper '{scraper_name}' not found in registry.")
        return

    logger.info(f"Starting scraper: '{scraper_name}'")
    logger.info(f"Run configuration: Headless={is_headless}, Debug={is_debug}")

    # Ensure profile directory exists
    user_data_dir = config.PROFILE_DIR
    os.makedirs(user_data_dir, exist_ok=True)
    logger.info(f"Using persistent profile at: {user_data_dir}")

    async with async_playwright() as p:
        # Use persistent context for better anti-detection
        # This replaces browser.launch() + browser.new_context()
        
        args_list = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-blink-features=AutomationControlled", # Anti-detection
        ]
        
        # Note: persistent context with headless=True might behave differently than launch()
        # but it is generally supported.
        
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=is_headless,
                args=args_list,
                viewport={"width": 1920, "height": 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                # channel="chrome", # Uncomment if Chrome is installed and preferred
            )
        except Exception as e:
            logger.critical(f"Failed to launch persistent context: {e}")
            return

        # Add webdriver property removal script
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Get the default page or create new one
        page = context.pages[0] if context.pages else await context.new_page()
        
        if is_debug:
            logger.info("Attaching network request/response loggers.")
            page.on("request", utils.log_request)
            page.on("response", utils.log_response)

        # --- Instantiate and run the selected scraper ---
        scraper_instance = ScraperClass(page)

        try:
            await scraper_instance.run()
            logger.success("Scraping script completed successfully!")
        except Exception as e:
            logger.critical(f"An unhandled error occurred in '{scraper_name}': {e}", exc_info=True)
            screenshot_path = os.path.join(config.SCREENSHOTS_DIR, f"{scraper_name}_error_page.png")
            try:
                await page.screenshot(path=screenshot_path, full_page=True)
                logger.error(f"Screenshot saved for debugging: {screenshot_path}")
            except Exception:
                logger.error("Could not save screenshot (browser might be closed).")
        finally:
            logger.info("Closing context...")
            await context.close()
            logger.info("Context closed.")
