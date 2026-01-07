import os
import glob
import random
from datetime import date
from urllib.parse import urljoin
from loguru import logger
from playwright.async_api import Page, TimeoutError

from .. import config
from .generic_scraper import GenericScraper

class FierceBiotechScraper(GenericScraper):
    """
    A scraper for fiercebiotech.com. This site does not require a login
    but may present pop-ups that need to be dismissed.
    """

    def __init__(self, page: Page):
        # No state_file is needed as there is no login.
        super().__init__(page=page, base_dir=config.FIERCE_BASE_DIR, state_file=None)
        self.channels = config.FIERCE_CHANNELS
        self.base_url = "https://www.fiercebiotech.com"

    async def _login(self):
        """No-op: Login is not required for this site."""
        logger.info("Login not required for Fierce Biotech. Skipping.")
        pass

    async def _is_session_valid(self) -> bool:
        """Always returns True as there is no session to validate."""
        return True

    async def _handle_popups(self):
        """
        Attempts to find and close common pop-ups (like cookie consents or ads)
        in a non-blocking way.
        """
        # Selector for the OneTrust cookie consent banner "Accept All" button
        cookie_button_selector = "button#onetrust-accept-btn-handler"
        
        try:
            # Use a short timeout to avoid slowing down the scrape if no pop-up exists
            cookie_button = self.page.locator(cookie_button_selector)
            is_visible = await cookie_button.is_visible(timeout=2500)
            if is_visible:
                logger.info("Cookie consent pop-up detected. Clicking 'Accept All'.")
                await cookie_button.click()
                await self.short_pause() # Pause briefly after clicking
        except TimeoutError:
            logger.debug("No cookie consent pop-up found. Continuing.")
        except Exception as e:
            logger.warning(f"Could not handle pop-up. Error: {e}")

    async def _scrape_site(self):
        """Scrapes articles from all configured Fierce Biotech channels."""
        shuffled_channels = self.channels.copy()
        random.shuffle(shuffled_channels)
        logger.info(f"Randomized channel order for Fierce Biotech.")

        for channel_url in shuffled_channels:
            channel_name = channel_url.split("/")[-1] or channel_url.split("/")[-2]
            num_to_download = random.randint(3, 7)
            logger.info(f"--- Processing channel: {channel_name} (Targeting {num_to_download} new articles) ---")

            channel_dir = os.path.join(self.base_dir, self.sanitize_filename(channel_name))
            os.makedirs(channel_dir, exist_ok=True)
            
            try:
                await self.page.goto(channel_url)
                await self.page.wait_for_load_state("domcontentloaded")
            except Exception as e:
                logger.error(f"Failed to navigate to channel {channel_url}. Error: {e}")
                continue
            
            await self._handle_popups()
            await self.simulate_skimming(random.uniform(4, 7))
            
            articles_to_scrape = []
            
            # --- vvv THIS IS THE CORRECTED LINE vvv ---
            article_locators = await self.page.locator('article.node-listing .element-title a').all()
            # --- ^^^ END OF CORRECTION ^^^ ---
            
            logger.debug(f"Found {len(article_locators)} articles on page. Checking for new ones.")
            for locator in article_locators:
                # ... (rest of the loop is unchanged) ...
                if len(articles_to_scrape) >= num_to_download:
                    break
                
                title = await locator.text_content()
                title = title.strip() if title else ""
                sanitized_title = self.sanitize_filename(title)
                
                if not title:
                    continue

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
                    await self._handle_popups() # Check for pop-ups on the article page too
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
