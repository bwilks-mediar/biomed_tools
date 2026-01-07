import os
import glob
import random
from datetime import date
from urllib.parse import urljoin
from loguru import logger
from playwright.async_api import Page

from .. import config
from .generic_scraper import GenericScraper

class BioPharmaDiveScraper(GenericScraper):
    """A scraper for biopharmadive.com."""

    def __init__(self, page: Page):
        super().__init__(page=page, base_dir=config.BIOPHARMA_DIVE_BASE_DIR, state_file=None)
        self.channels = config.BIOPHARMA_DIVE_CHANNELS
        self.base_url = "https://www.biopharmadive.com"

    async def _login(self):
        """No-op: Login is not required for this site."""
        logger.info("Login not required for BioPharma Dive. Skipping.")
        pass

    async def _is_session_valid(self) -> bool:
        """Always returns True as there is no session to validate."""
        return True

    async def _scrape_site(self):
        """Scrapes articles from all configured BioPharma Dive channels."""
        shuffled_channels = self.channels.copy()
        random.shuffle(shuffled_channels)
        logger.info(f"Randomized channel order for BioPharma Dive.")

        for channel_url in shuffled_channels:
            # Determine channel name and the correct CSS selector
            is_press_release = "/press-release/" in channel_url
            if is_press_release:
                channel_name = "press-release"
                article_selector = "li.js-pressrelease h3.feed__title a"
            else:
                channel_name = channel_url.strip('/').split('/')[-1]
                # This selector targets article list items but explicitly excludes ad items.
                article_selector = "li.feed__item:not(.feed-item-ad) h3.feed__title a"

            num_to_download = random.randint(4, 8)
            logger.info(f"--- Processing channel: {channel_name} (Targeting {num_to_download} new articles) ---")

            channel_dir = os.path.join(self.base_dir, self.sanitize_filename(channel_name))
            os.makedirs(channel_dir, exist_ok=True)
            
            try:
                await self.page.goto(channel_url, wait_until="domcontentloaded")
            except Exception as e:
                logger.error(f"Failed to navigate to channel {channel_url}. Error: {e}")
                continue
            
            await self.simulate_skimming(random.uniform(3, 6))
            
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
                    logger.debug(f"Skipping (exists): {title[:70]}...")
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
                    await self.reading_delay()
                    
                    html_content = await self.page.content()
                    today_str = date.today().strftime("%Y-%m-%d")
                    filepath = os.path.join(channel_dir, f"{today_str}_{self.sanitize_filename(article['title'])}.html")
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    logger.success(f"Saved to {filepath}")
                except Exception as e:
                    logger.error(f"FAILED to download article: {article['url']}. Error: {e}")
            
            await self.short_pause()
