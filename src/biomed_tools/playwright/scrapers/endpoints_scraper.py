# /scrapers/endpoints_scraper.py

import os
import glob
import random
from datetime import date
from loguru import logger
from playwright.async_api import Page, expect
from urllib.parse import urljoin


from .. import config
from .generic_scraper import GenericScraper

class EndpointsScraper(GenericScraper):
    """A scraper for endpoints.news, implementing site-specific logic."""
    def __init__(self, page: Page):
        super().__init__(page=page, base_dir=config.ENDPOINTS_BASE_DIR, state_file=config.ENDPOINTS_STATE_FILE)
        self.channels = config.ENDPOINTS_CHANNELS

    async def _login(self):
        logger.info("--- Performing Endpoints hybrid human/API login ---")
        email, password = os.getenv("ENDPOINTS_EMAIL"), os.getenv("ENDPOINTS_PASSWORD")
        if not email or not password:
            raise ValueError("Please set ENDPOINTS_EMAIL and ENDPOINTS_PASSWORD env vars.")

        logger.debug("Step 1: Navigating to login page and entering credentials.")
        await self.page.goto("https://profile.endpoints.news/log-in")
        await self.page.wait_for_load_state("networkidle")
        await self.human_type(self.page.locator('input[name="email"]'), email, random.randint(80, 150))
        await self.short_pause()
        await self.human_type(self.page.locator('input[name="password"]'), password, random.randint(90, 160))
        await self.short_pause()
        await self.page.locator('[data-testid="log-in-button"]').hover()

        logger.debug("Step 2: Authenticating with API to get tokens.")
        api_context = self.context.request
        try:
            # ... (API calls are unchanged, but we log the outcome) ...
            login_response = await api_context.post("https://api.profile.endpoints.news/auth/log-in", data={"email": email, "password": password, "returnPayload": True})
            access_token = (await login_response.json()).get("accessToken")
            if not access_token: raise Exception(f"Could not extract accessToken. Response: {await login_response.text()}")
            
            code_gen_response = await api_context.post("https://api.profile.endpoints.news/auth/log-in-code/generate", headers={"Authorization": f"Bearer {access_token}"}, data={"redirectURL": "https://endpoints.news/auth"})
            access_code = (await code_gen_response.json()).get("accessCode")
            if not access_code: raise Exception(f"Could not extract accessCode. Response: {await code_gen_response.text()}")
            logger.success("API tokens received successfully.")
        except Exception as e:
            logger.error(f"API authentication steps failed. Error: {e}")
            raise

        logger.debug("Step 3: Navigating to auth callback URL to finalize session.")
        await self.page.goto(f"https://endpoints.news/auth?accessCode={access_code}")
        await self.page.wait_for_url(lambda url: "endpoints.news" in url and "auth?accessCode" not in url, timeout=30000)

        logger.debug("Step 4: Verifying login and saving state.")
        try:
            await expect(self.page.locator('.epn_user h4:has-text("Hello,")')).to_be_visible(timeout=15000)
            logger.success("Login successful and verified on main site!")
            await self.context.storage_state(path=self.state_file)
            logger.info(f"Fresh, valid session state saved to '{self.state_file}'.")
        except Exception as e:
            logger.error("Could not verify login after final redirect.")
            raise Exception("Could not verify login after final redirect.") from e

    async def _is_session_valid(self) -> bool:
        await self.page.goto(f"https://endpoints.news/channel/{self.channels[0]}/")
        try:
            await expect(self.page.locator('.epn_user .dropdown-toggle')).to_be_visible(timeout=7000)
            return True
        except Exception:
            return False

    async def _scrape_site(self):
        shuffled_channels = self.channels.copy()
        random.shuffle(shuffled_channels)
        logger.info(f"Randomized channel order: {shuffled_channels}")

        for channel in shuffled_channels:
            num_to_download = 1 if channel == 'weekly' else random.randint(2, 8)
            logger.info(f"--- Processing channel: {channel} (Targeting {num_to_download} new articles) ---")
            channel_dir = os.path.join(self.base_dir, channel)
            os.makedirs(channel_dir, exist_ok=True)
            
            await self.page.goto(f"https://endpoints.news/channel/{channel}/")
            await self.page.wait_for_load_state("domcontentloaded")
            await self.simulate_skimming(random.uniform(3, 6))
            
            articles_to_scrape = []
            article_locators = await self.page.locator('.epn_result_list .epn_item h3 a').all()
            
            logger.debug(f"Found {len(article_locators)} articles on page. Checking for new ones.")
            for locator in article_locators:
                if len(articles_to_scrape) >= num_to_download: break
                
                title = await locator.get_attribute('title') or ""
                sanitized_title = self.sanitize_filename(title)
                
                if glob.glob(os.path.join(channel_dir, f"*_{sanitized_title}.html")):
                    logger.debug(f"Skipping (exists): {title[:70]}...")
                    continue
                
                logger.info(f"Queuing for download: {title[:70]}...")
                
                relative_url = await locator.get_attribute('href')
                full_url = urljoin("https://endpoints.news/", relative_url)
                articles_to_scrape.append({'url': full_url, 'title': title})
            
            if not articles_to_scrape:
                logger.info(f"No new articles to download for channel '{channel}'.")
                continue

            logger.info(f"Downloading {len(articles_to_scrape)} new articles from '{channel}'...")
            for i, article in enumerate(articles_to_scrape):
                logger.debug(f"Downloading article {i+1}/{len(articles_to_scrape)}: {article['title']}")
                try:
                    await self.page.goto(article['url'])
                    await self.page.wait_for_load_state("domcontentloaded")
                    await self.reading_delay()
                    
                    html_content = await self.page.content()
                    today_str = date.today().strftime("%Y-%m-%d")
                    filepath = os.path.join(channel_dir, f"{today_str}_{self.sanitize_filename(article['title'])}.html")
                    
                    with open(filepath, 'w', encoding='utf-8') as f: f.write(html_content)
                    logger.success(f"Saved to {filepath}")
                except Exception as e:
                    logger.error(f"FAILED to download article: {article['url']}. Error: {e}")
            
            await self.short_pause()
