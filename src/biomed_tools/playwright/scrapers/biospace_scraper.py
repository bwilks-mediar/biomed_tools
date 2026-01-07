# /scrapers/biospace_scraper.py

import os
import glob
import random
import asyncio
from datetime import date
from urllib.parse import urljoin
from loguru import logger
from playwright.async_api import Page, TimeoutError, Error as PlaywrightError

from .. import config
from .generic_scraper import GenericScraper

class BioSpaceScraper(GenericScraper):
    """
    A scraper for biospace.com, using an advanced asynchronous "guardian"
    to handle pop-ups that appear on a time-delay or after scrolling.
    """

    def __init__(self, page: Page):
        super().__init__(page=page, base_dir=config.BIOSPACE_BASE_DIR, state_file=None)
        self.channels = config.BIOSPACE_CHANNELS
        self.base_url = "https://www.biospace.com"

    async def _login(self):
        pass

    async def _is_session_valid(self) -> bool:
        return True

    async def _popup_guardian(self, stop_event: asyncio.Event):
        """
        A background task that continuously watches for and closes pop-ups.
        It tries multiple common selectors for pop-up iframes.
        """
        logger.info("[Guardian] Task started. Watching for pop-ups.")
        
        # --- List of potential selectors for the pop-up iframe ---
        # We will try all of these until one works.
        iframe_selectors = [
            'iframe[id^="hubspot-messages-iframe"]', # Original guess
            'iframe[title*="notification"]',        # For notification/subscription frames
            'iframe[title*="interactive"]',         # For interactive content
            'iframe[src*="hs-sites.com"]',           # Based on network logs
            'iframe[title="Popup CTA"]',            # From your HTML source
        ]
        
        close_button_selector = "div#interactive-close-button"

        while not stop_event.is_set():
            found_and_closed = False
            for selector in iframe_selectors:
                try:
                    # Locate the iframe using the current selector in the list
                    frame_loc = self.page.frame_locator(selector).first
                    
                    # If the iframe exists, try to find and click the close button
                    if await frame_loc.locator('body').is_visible(timeout=250):
                        logger.debug(f"[Guardian] Found a potential iframe with selector: '{selector}'")
                        close_button = frame_loc.locator(close_button_selector)
                        
                        if await close_button.is_visible(timeout=500):
                            logger.success(f"[Guardian] POP-UP DETECTED in iframe '{selector}'! Closing it.")
                            await close_button.click(force=True, timeout=2000)
                            await asyncio.sleep(2) # Pause after closing
                            found_and_closed = True
                            break # Exit the for loop since we closed one
                
                except (TimeoutError, PlaywrightError):
                    continue # This selector didn't work, try the next one
            
            if not found_and_closed:
                # If we looped through all selectors and found nothing, wait and restart.
                await asyncio.sleep(0.5)

        logger.info("[Guardian] Task has been stopped.")


    async def _clear_page_and_read(self):
        """
        Simulates reading while a background 'guardian' task handles any
        pop-ups that appear on a delay.
        """
        logger.info("Starting guarded reading simulation...")
        
        stop_guardian_event = asyncio.Event()
        guardian_task = asyncio.create_task(self._popup_guardian(stop_guardian_event))

        reading_duration = random.uniform(10, 20)
        logger.info(f"Main task will now simulate reading for {reading_duration:.2f} seconds.")

        try:
            # The guardian is watching while we do this. A small initial scroll
            # helps trigger any on-scroll scripts.
            await self.page.mouse.wheel(0, 500)
            await self.simulate_reading(reading_duration) 
        finally:
            logger.info("Reading simulation finished. Stopping guardian task...")
            stop_guardian_event.set()
            try:
                await asyncio.wait_for(guardian_task, timeout=2.0)
            except asyncio.TimeoutError:
                logger.warning("[Guardian] Guardian task did not shut down cleanly within the timeout.")

    async def _scrape_site(self):
        # This method does not need changes.
        shuffled_channels = self.channels.copy()
        random.shuffle(shuffled_channels)
        logger.info(f"Randomized channel order for BioSpace.")

        for channel_url in shuffled_channels:
            is_press_release = "/search-press-releases" in channel_url
            if is_press_release:
                channel_name = "press-releases"
                article_selector = "ul.search-results-list a.search-results-item-title-link"
            else:
                channel_name = channel_url.strip('/').split('/')[-1] if channel_url.strip('/') != self.base_url else "news"
                article_selector = "div.PagePromo-title a.Link"

            num_to_download = random.randint(1, 2) # Reduced for faster debugging
            logger.info(f"--- Processing channel: {channel_name} (Targeting {num_to_download} new articles) ---")

            channel_dir = os.path.join(self.base_dir, self.sanitize_filename(channel_name))
            os.makedirs(channel_dir, exist_ok=True)

            try:
                await self.page.goto(channel_url, wait_until="domcontentloaded")
                await self.simulate_skimming(random.uniform(2, 4))
            except Exception as e:
                logger.error(f"Failed to navigate to channel {channel_url}. Error: {e}")
                continue

            articles_to_scrape = []
            article_locators = await self.page.locator(article_selector).all()
            logger.debug(f"Found {len(article_locators)} potential articles using selector '{article_selector}'.")

            for locator in article_locators:
                if len(articles_to_scrape) >= num_to_download: break
                title = await locator.text_content()
                title = title.strip() if title else ""
                if not title: continue
                sanitized_title = self.sanitize_filename(title)
                if glob.glob(os.path.join(channel_dir, f"*_{sanitized_title}.html")):
                    continue
                logger.info(f"Queuing for download: {title[:70]}...")
                relative_url = await locator.get_attribute('href')
                full_url = urljoin(self.base_url, relative_url or "")
                articles_to_scrape.append({'url': full_url, 'title': title})

            if not articles_to_scrape:
                logger.info(f"No new articles to download for channel '{channel_name}'.")
                continue

            logger.info(f"Downloading {len(articles_to_scrape)} new articles from '{channel_name}'...")
            for i, article in enumerate(articles_to_scrape):
                logger.debug(f"Downloading article {i+1}/{len(articles_to_scrape)}: {article['title']}")
                try:
                    await self.page.goto(article['url'], wait_until="domcontentloaded")
                    await self._clear_page_and_read()
                    html_content = await self.page.content()
                    today_str = date.today().strftime("%Y-%m-%d")
                    filepath = os.path.join(channel_dir, f"{today_str}_{self.sanitize_filename(article['title'])}.html")
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    logger.success(f"Saved to {filepath}")
                except Exception as e:
                    screenshot_path = os.path.join(config.SCREENSHOTS_DIR, f"biospace_article_fail_{i}.png")
                    await self.page.screenshot(path=screenshot_path, full_page=True)
                    logger.error(f"FAILED to download article: {article['url']}. Screenshot saved to '{screenshot_path}'. Error: {e}", exc_info=True)
            
            await self.short_pause()
