"""Scraper configuration dataclass for constructor injection."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScraperConfig:
    """Configuration for web scraping operations.

    All scraping parameters are configurable via constructor injection.
    Different services can pass their own configurations.

    Example:
        odds_config = ScraperConfig(
            interval_seconds=12.0,
            timeout_ms=30000,
            max_retries=3
        )
        results_config = ScraperConfig(
            interval_seconds=3.0,
            timeout_ms=30000,
            max_retries=3
        )
    """
    interval_seconds: float = 5.0
    timeout_ms: int = 30000
    max_retries: int = 3
    retry_delay_seconds: float = 2.0
    headless: bool = True
    wait_time_ms: int = 1000

    def __post_init__(self):
        """Validate configuration values."""
        if self.interval_seconds < 0:
            raise ValueError("interval_seconds must be non-negative")
        if self.timeout_ms <= 0:
            raise ValueError("timeout_ms must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds must be non-negative")
        if self.wait_time_ms < 0:
            raise ValueError("wait_time_ms must be non-negative")


@dataclass(frozen=True)
class RateLimitConfig:
    """Configuration for rate limiting.

    Example:
        sports_ref_limit = RateLimitConfig(calls=1, period_seconds=5.0)
        draftkings_limit = RateLimitConfig(calls=1, period_seconds=2.0)
    """
    calls: int = 1
    period_seconds: float = 5.0

    def __post_init__(self):
        """Validate configuration values."""
        if self.calls <= 0:
            raise ValueError("calls must be positive")
        if self.period_seconds <= 0:
            raise ValueError("period_seconds must be positive")


# Default configurations for different services
ODDS_SCRAPER_CONFIG = ScraperConfig(
    interval_seconds=12.0,
    timeout_ms=30000,
    max_retries=3,
    retry_delay_seconds=2.0,
    headless=True,
    wait_time_ms=2000
)

RESULTS_SCRAPER_CONFIG = ScraperConfig(
    interval_seconds=3.0,
    timeout_ms=30000,
    max_retries=3,
    retry_delay_seconds=2.0,
    headless=True,
    wait_time_ms=1000
)

PREDICTIONS_SCRAPER_CONFIG = ScraperConfig(
    interval_seconds=5.0,
    timeout_ms=30000,
    max_retries=3,
    retry_delay_seconds=2.0,
    headless=True,
    wait_time_ms=1000
)

# Rate limit configurations
SPORTS_REFERENCE_RATE_LIMIT = RateLimitConfig(calls=1, period_seconds=5.0)
DRAFTKINGS_RATE_LIMIT = RateLimitConfig(calls=1, period_seconds=2.0)
