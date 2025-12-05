"""Scraper configuration dataclass."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ScraperConfig:
    """Configuration for scraping operations.

    Example:
        config = ScraperConfig(delay_seconds=3.0, timeout=30)
        scraper = Scraper(config)
    """

    delay_seconds: float = 3.0
    """Fixed delay between requests (rate limiting)."""

    timeout: int = 30
    """Request timeout in seconds."""

    max_retries: int = 3
    """Number of retries on failure."""

    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    """User-Agent header for requests."""

    extract_comments: bool = True
    """Whether to extract tables from HTML comments (for PFR hidden tables)."""

    def __post_init__(self):
        """Validate configuration values."""
        if self.delay_seconds < 0:
            raise ValueError("delay_seconds must be non-negative")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")


# Default configurations for different sources
PFR_CONFIG = ScraperConfig(
    delay_seconds=3.0,
    timeout=30,
    extract_comments=True,
)

DRAFTKINGS_CONFIG = ScraperConfig(
    delay_seconds=1.0,
    timeout=15,
    extract_comments=False,
)

FBREF_CONFIG = ScraperConfig(
    delay_seconds=3.0,
    timeout=30,
    extract_comments=True,
)
