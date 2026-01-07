# /scrapers/generic_scraper.py

import os
import random
import asyncio
import numpy as np
from abc import ABC, abstractmethod
from loguru import logger
from playwright.async_api import Page, Locator

from .. import config
from ..utils import sanitize_filename

class GenericScraper(ABC):
    """
    An abstract base class for web scrapers that encapsulates generic,
    reusable scraping logic and human-like interaction patterns.
    """
    def __init__(self, page: Page, base_dir: str, state_file: str):
        self.page = page
        self.context = page.context
        self.base_dir = base_dir
        self.state_file = state_file
        os.makedirs(self.base_dir, exist_ok=True)
        self.sanitize_filename = sanitize_filename

    @abstractmethod
    async def _login(self):
        """Site-specific login procedure."""
        pass

    @abstractmethod
    async def _is_session_valid(self) -> bool:
        """Checks if the current session is valid."""
        pass

    @abstractmethod
    async def _scrape_site(self):
        """Main site-specific scraping logic."""
        pass

    async def short_pause(self):
        delay = random.uniform(config.SHORT_PAUSE_MIN, config.SHORT_PAUSE_MAX)
        logger.debug(f"Pausing for {delay:.2f} seconds...")
        await asyncio.sleep(delay)

    async def is_at_bottom(self) -> bool:
        return await self.page.evaluate("Math.abs(window.scrollY + window.innerHeight - document.body.scrollHeight) < 5")

    async def move_mouse_randomly(self):
        viewport = self.page.viewport_size
        if viewport:
            x, y = random.randint(0, viewport['width']), random.randint(0, viewport['height'])
            await self.page.mouse.move(x, y, steps=random.randint(5, 10))

    async def simulate_skimming(self, duration: float):
        logger.info(f"Simulating 'skim' for up to {duration:.2f}s: fast, large scrolls.")
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < duration:
            if await self.is_at_bottom():
                logger.debug("Reached end of document during skim.")
                break
            await self.page.mouse.wheel(0, random.randint(800, 1500))
            await asyncio.sleep(random.uniform(0.5, 1.2))

    async def simulate_reading(self, duration: float):
        logger.info(f"Simulating 'read' for up to {duration:.2f}s: slow scrolls, mouse drifts.")
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < duration:
            if await self.is_at_bottom():
                logger.debug("Reached end of document during read.")
                break
            await self.page.mouse.wheel(0, random.randint(100, 250))
            if random.random() < 0.25: await self.move_mouse_randomly()
            await asyncio.sleep(random.uniform(1.5, 4.0))

    async def reading_delay(self):
        doc_height = await self.page.evaluate("document.body.scrollHeight")
        view_height = self.page.viewport_size['height'] if self.page.viewport_size else 950
        screens = doc_height / view_height if view_height > 0 else 1
        choice = np.random.choice(['skim', 'read'], p=config.BIMODAL_WEIGHTS)
        if choice == 'skim':
            base_duration = screens * config.SKIM_SECONDS_PER_SCREEN
            duration = max(config.MIN_SKIM_TIME, min(config.MAX_SKIM_TIME, base_duration * random.uniform(0.7, 1.3)))
            await self.simulate_skimming(duration)
        else:
            base_duration = screens * config.READ_SECONDS_PER_SCREEN
            duration = max(config.MIN_READ_TIME, min(config.MAX_READ_TIME, base_duration * random.uniform(0.8, 1.2)))
            await self.simulate_reading(duration)
    
    async def human_type(self, locator: Locator, text: str, delay_ms: int):
        await locator.click()
        await locator.type(text, delay=delay_ms)

    async def run(self):
        """
        Main execution flow: validates session, logs in if needed, then scrapes.
        """
        logger.info(f"--- Initializing Scraper: {self.__class__.__name__} ---")
        
        # --- vvv THIS IS THE CORRECTED LOGIC vvv ---
        # Only perform login/session checks if a state file is configured.
        if self.state_file:
            if not os.path.exists(self.state_file):
                logger.warning(f"State file '{self.state_file}' not found. Performing fresh login.")
                await self._login()
            else:
                logger.info("--- Validating Login Session ---")
                if not await self._is_session_valid():
                    logger.warning("Session is stale or invalid. Re-authenticating...")
                    await self._login()
                else:
                    logger.success("Session is active. Continuing.")
        else:
            # If no state file, just call the _login method directly.
            # For scrapers without login, this will be a no-op.
            await self._login()
            
        await self._scrape_site()
