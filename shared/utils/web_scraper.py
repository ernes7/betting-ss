"""Web scraping utility using Playwright."""

from contextlib import contextmanager
from playwright.sync_api import sync_playwright, Page


class WebScraper:
    """Wrapper for Playwright web scraping operations."""

    def __init__(self, headless: bool = True, timeout: int = 10000):
        """Initialize web scraper configuration.

        Args:
            headless: Run browser in headless mode
            timeout: Page load timeout in milliseconds
        """
        self.headless = headless
        self.timeout = timeout

    @contextmanager
    def launch(self):
        """Context manager for launching browser and returning page.

        Yields:
            Page: Playwright page object

        Example:
            with scraper.launch() as page:
                page.goto("https://example.com")
                # ... extract data
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page()
            try:
                yield page
            finally:
                browser.close()

    def navigate_and_wait(self, page: Page, url: str, wait_time: int = 1000):
        """Navigate to URL and wait for content to load.

        Args:
            page: Playwright page object
            url: URL to navigate to
            wait_time: Additional wait time in milliseconds for JS tables

        Returns:
            Response object from page navigation
        """
        response = page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)
        page.wait_for_timeout(wait_time)
        return response
