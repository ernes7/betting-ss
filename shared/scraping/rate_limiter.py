"""Rate limiting utilities for web scraping."""

import time
from functools import wraps
from typing import Callable, Any

from ratelimit import limits, sleep_and_retry

from shared.scraping.scraper_config import RateLimitConfig


def create_rate_limiter(config: RateLimitConfig) -> Callable:
    """Create a rate limiting decorator from configuration.

    Args:
        config: RateLimitConfig with calls and period settings

    Returns:
        Decorator function that rate limits the wrapped function

    Example:
        from shared.scraping.scraper_config import SPORTS_REFERENCE_RATE_LIMIT

        rate_limit = create_rate_limiter(SPORTS_REFERENCE_RATE_LIMIT)

        @rate_limit
        def fetch_data(url):
            # This function will be rate limited
            pass
    """
    @sleep_and_retry
    @limits(calls=config.calls, period=config.period_seconds)
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return func(*args, **kwargs)
        return wrapper

    # Return a decorator that applies rate limiting
    def rate_limit_decorator(func: Callable) -> Callable:
        @sleep_and_retry
        @limits(calls=config.calls, period=config.period_seconds)
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return func(*args, **kwargs)
        return wrapper

    return rate_limit_decorator


class RateLimiter:
    """Class-based rate limiter for more complex scenarios.

    Useful when you need to track rate limiting state or
    share a limiter across multiple methods.

    Example:
        limiter = RateLimiter(config=SPORTS_REFERENCE_RATE_LIMIT)

        for url in urls:
            limiter.wait()
            response = fetch(url)
    """

    def __init__(self, config: RateLimitConfig):
        """Initialize rate limiter with configuration.

        Args:
            config: RateLimitConfig with rate limiting settings
        """
        self.config = config
        self._last_call_time: float | None = None
        self._calls_in_period: int = 0
        self._period_start: float | None = None

    def wait(self) -> None:
        """Wait if necessary to respect rate limits.

        Call this before each request to ensure rate limits are respected.
        """
        current_time = time.time()

        if self._period_start is None:
            self._period_start = current_time
            self._calls_in_period = 1
            return

        # Check if we're still in the same period
        elapsed = current_time - self._period_start

        if elapsed >= self.config.period_seconds:
            # Start new period
            self._period_start = current_time
            self._calls_in_period = 1
            return

        # Still in same period
        self._calls_in_period += 1

        if self._calls_in_period > self.config.calls:
            # Need to wait until period ends
            sleep_time = self.config.period_seconds - elapsed
            time.sleep(sleep_time)
            # Start new period
            self._period_start = time.time()
            self._calls_in_period = 1

    def reset(self) -> None:
        """Reset rate limiter state."""
        self._last_call_time = None
        self._calls_in_period = 0
        self._period_start = None
