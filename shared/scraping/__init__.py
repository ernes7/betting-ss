"""Shared scraping utilities using pandas.

This module provides a unified Scraper class for both HTML table
extraction and JSON API fetching.

Example:
    from shared.scraping import Scraper, ScraperConfig, PFR_CONFIG

    # Create scraper with default config
    scraper = Scraper()

    # Or with custom config
    scraper = Scraper(ScraperConfig(delay_seconds=5.0))

    # Scrape HTML tables
    tables = scraper.scrape_tables(url, column_map={"Tm": "team"})

    # Scrape JSON API
    df = scraper.scrape_api(url, parser=my_parser_fn)
"""

from shared.scraping.scraper import Scraper
from shared.scraping.scraper_config import (
    ScraperConfig,
    PFR_CONFIG,
    DRAFTKINGS_CONFIG,
    FBREF_CONFIG,
)

__all__ = [
    # Main scraper class
    "Scraper",
    # Config class
    "ScraperConfig",
    # Default configs
    "PFR_CONFIG",
    "DRAFTKINGS_CONFIG",
    "FBREF_CONFIG",
]
