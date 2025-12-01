"""Web scraping utility using Playwright with configurable settings."""

import time
from contextlib import contextmanager
from typing import Any

from playwright.sync_api import sync_playwright, Page, Response

from shared.scraping.scraper_config import ScraperConfig


class WebScraper:
    """Configurable web scraper using Playwright.

    Uses constructor injection for all configuration parameters.
    Each service can provide its own ScraperConfig with appropriate settings.

    Example:
        from shared.scraping.scraper_config import ODDS_SCRAPER_CONFIG

        scraper = WebScraper(config=ODDS_SCRAPER_CONFIG)
        with scraper.launch() as page:
            scraper.navigate_and_wait(page, "https://example.com")
            # Extract data...
    """

    def __init__(self, config: ScraperConfig):
        """Initialize web scraper with configuration.

        Args:
            config: ScraperConfig dataclass with all scraping parameters
        """
        self.config = config

    @contextmanager
    def launch(self):
        """Context manager for launching browser and returning page.

        Yields:
            Page: Playwright page object

        Example:
            with scraper.launch() as page:
                page.goto("https://example.com")
                content = page.content()
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.config.headless)
            page = browser.new_page()
            try:
                yield page
            finally:
                browser.close()

    def navigate_and_wait(self, page: Page, url: str, wait_time_ms: int | None = None) -> Response | None:
        """Navigate to URL and wait for content to load.

        Args:
            page: Playwright page object
            url: URL to navigate to
            wait_time_ms: Override wait time in milliseconds (uses config default if None)

        Returns:
            Response object from page navigation or None
        """
        wait_time = wait_time_ms if wait_time_ms is not None else self.config.wait_time_ms
        response = page.goto(url, wait_until="domcontentloaded", timeout=self.config.timeout_ms)
        page.wait_for_timeout(wait_time)
        return response

    def scrape_with_retry(self, url: str, extract_fn: callable) -> Any:
        """Scrape URL with automatic retry on failure.

        Args:
            url: URL to scrape
            extract_fn: Function that takes a Page and returns extracted data

        Returns:
            Extracted data from extract_fn

        Raises:
            Exception: If all retries are exhausted
        """
        last_error = None

        for attempt in range(self.config.max_retries):
            try:
                with self.launch() as page:
                    self.navigate_and_wait(page, url)
                    return extract_fn(page)
            except Exception as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay_seconds)

        raise last_error

    def wait_between_requests(self):
        """Wait the configured interval between requests.

        Call this between consecutive requests to respect rate limits.
        """
        time.sleep(self.config.interval_seconds)
