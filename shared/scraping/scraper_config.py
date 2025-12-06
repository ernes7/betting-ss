"""Scraper configuration dataclass."""

from dataclasses import dataclass, field
from typing import Dict

from config import settings


# Browser-like headers to bypass Cloudflare
DEFAULT_HEADERS: Dict[str, str] = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}


def get_default_delay() -> float:
    """Calculate delay from global config (period / calls)."""
    try:
        calls = settings["scraping"]["sports_reference"]["rate_limit_calls"]
        period = settings["scraping"]["sports_reference"]["rate_limit_period"]
        return period / calls  # 60/20 = 3.0 seconds
    except (KeyError, TypeError):
        return 3.0  # Fallback default


@dataclass(frozen=True)
class ScraperConfig:
    """Configuration for scraping operations.

    Example:
        config = ScraperConfig(delay_seconds=3.0, timeout=30)
        scraper = Scraper(config)
    """

    delay_seconds: float = field(default_factory=get_default_delay)
    """Fixed delay between requests (rate limiting). Defaults to config value."""

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

    headers: Dict[str, str] = field(default_factory=lambda: DEFAULT_HEADERS.copy())
    """Additional HTTP headers for requests."""

    extract_comments: bool = True
    """Whether to extract tables from HTML comments (for PFR hidden tables)."""

    use_cloudscraper: bool = False
    """Whether to use cloudscraper for Cloudflare bypass (for FBRef)."""

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
    delay_seconds=get_default_delay(),
    timeout=30,
    extract_comments=True,
)

DRAFTKINGS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
}

DRAFTKINGS_CONFIG = ScraperConfig(
    delay_seconds=1.0,
    timeout=15,
    extract_comments=False,
    headers=DRAFTKINGS_HEADERS,
)

FBREF_CONFIG = ScraperConfig(
    delay_seconds=get_default_delay(),
    timeout=30,
    extract_comments=True,
    use_cloudscraper=True,  # Bypass Cloudflare protection
)
