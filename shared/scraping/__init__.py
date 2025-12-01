"""Shared scraping utilities with configurable settings.

This module provides reusable scraping components that can be configured
via constructor injection for different services.

Example:
    from shared.scraping import WebScraper, ScraperConfig, TableExtractor

    # Create config for odds service
    config = ScraperConfig(interval_seconds=12.0, timeout_ms=30000)
    scraper = WebScraper(config=config)

    with scraper.launch() as page:
        scraper.navigate_and_wait(page, url)
        data = TableExtractor.extract(page, "player_stats")
"""

from shared.scraping.scraper_config import (
    ScraperConfig,
    RateLimitConfig,
    ODDS_SCRAPER_CONFIG,
    RESULTS_SCRAPER_CONFIG,
    PREDICTIONS_SCRAPER_CONFIG,
    SPORTS_REFERENCE_RATE_LIMIT,
    DRAFTKINGS_RATE_LIMIT,
)
from shared.scraping.web_scraper import WebScraper
from shared.scraping.rate_limiter import create_rate_limiter, RateLimiter
from shared.scraping.table_extractor import TableExtractor

__all__ = [
    # Config classes
    "ScraperConfig",
    "RateLimitConfig",
    # Default configs
    "ODDS_SCRAPER_CONFIG",
    "RESULTS_SCRAPER_CONFIG",
    "PREDICTIONS_SCRAPER_CONFIG",
    "SPORTS_REFERENCE_RATE_LIMIT",
    "DRAFTKINGS_RATE_LIMIT",
    # Scraper classes
    "WebScraper",
    "TableExtractor",
    # Rate limiting
    "create_rate_limiter",
    "RateLimiter",
]
