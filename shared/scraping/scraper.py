"""Unified scraper for HTML tables and JSON APIs using pandas."""

import re
import time
from io import StringIO
from typing import Callable

import pandas as pd
import requests

from .scraper_config import ScraperConfig


class Scraper:
    """Unified scraper for HTML tables and JSON APIs."""

    def __init__(self, config: ScraperConfig | None = None):
        self.config = config or ScraperConfig()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.config.user_agent})

    # === HTML Table Extraction ===

    def fetch_html(self, url: str) -> str:
        """Fetch HTML content with rate limiting."""
        time.sleep(self.config.delay_seconds)
        response = self.session.get(url, timeout=self.config.timeout)
        response.raise_for_status()
        return response.text

    def extract_tables(
        self, html: str, extract_comments: bool | None = None
    ) -> list[pd.DataFrame]:
        """Extract all tables from HTML, including commented-out tables.

        Args:
            html: Raw HTML string
            extract_comments: Whether to extract tables from HTML comments.
                             Defaults to config.extract_comments.

        Returns:
            List of DataFrames, one per table found.
        """
        if extract_comments is None:
            extract_comments = self.config.extract_comments

        tables = []

        # Extract visible tables
        try:
            tables.extend(pd.read_html(StringIO(html)))
        except ValueError:
            # No tables found in main HTML
            pass

        # Extract tables from HTML comments (e.g., PFR hidden tables)
        if extract_comments:
            comments = re.findall(r"<!--(.+?)-->", html, re.DOTALL)
            for comment in comments:
                if "<table" in comment:
                    try:
                        tables.extend(pd.read_html(StringIO(comment)))
                    except ValueError:
                        # No valid table in this comment
                        pass

        return tables

    def scrape_tables(
        self,
        url: str,
        table_indices: list[int] | None = None,
        column_map: dict[str, str] | None = None,
    ) -> list[pd.DataFrame]:
        """Fetch URL and extract tables with optional column renaming.

        Args:
            url: URL to fetch
            table_indices: If provided, only return tables at these indices
            column_map: If provided, rename columns using this mapping

        Returns:
            List of DataFrames
        """
        html = self.fetch_html(url)
        tables = self.extract_tables(html)

        if table_indices:
            tables = [tables[i] for i in table_indices if i < len(tables)]

        if column_map:
            tables = [df.rename(columns=column_map) for df in tables]

        return tables

    def scrape_table(
        self,
        url: str,
        table_index: int = 0,
        column_map: dict[str, str] | None = None,
    ) -> pd.DataFrame:
        """Fetch URL and extract a single table.

        Args:
            url: URL to fetch
            table_index: Index of table to extract (default 0)
            column_map: If provided, rename columns using this mapping

        Returns:
            Single DataFrame
        """
        tables = self.scrape_tables(url, table_indices=[table_index], column_map=column_map)
        if not tables:
            raise ValueError(f"No table found at index {table_index}")
        return tables[0]

    # === JSON API Extraction ===

    def fetch_json(self, url: str) -> dict:
        """Fetch JSON data with rate limiting."""
        time.sleep(self.config.delay_seconds)
        response = self.session.get(url, timeout=self.config.timeout)
        response.raise_for_status()
        return response.json()

    def scrape_api(
        self, url: str, parser: Callable[[dict], pd.DataFrame]
    ) -> pd.DataFrame:
        """Fetch JSON API and parse with provided function.

        Args:
            url: API endpoint URL
            parser: Function that takes JSON dict and returns DataFrame

        Returns:
            DataFrame parsed from API response
        """
        data = self.fetch_json(url)
        return parser(data)

    # === Utility Methods ===

    def save_csv(self, df: pd.DataFrame, path: str, index: bool = False) -> None:
        """Save DataFrame to CSV."""
        df.to_csv(path, index=index)
