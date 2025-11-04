"""Scraping configuration constants for web data extraction."""

# Rate limiting for Sports-Reference sites (to avoid HTTP 429 errors)
# This applies to Pro-Football-Reference, Basketball-Reference, Hockey-Reference, etc.
# All Sports-Reference sites share the same infrastructure and rate limits
SPORTS_REFERENCE_RATE_LIMIT_CALLS = 1  # Number of calls allowed
SPORTS_REFERENCE_RATE_LIMIT_PERIOD = 5  # Time period in seconds

# DraftKings rate limiting
DRAFTKINGS_RATE_LIMIT_CALLS = 1
DRAFTKINGS_RATE_LIMIT_PERIOD = 2  # seconds

# Playwright/Browser Configuration
BROWSER_HEADLESS = True  # Run browser in headless mode
BROWSER_TIMEOUT = 30000  # 30 seconds (in milliseconds)
PAGE_LOAD_TIMEOUT = 10000  # 10 seconds wait for page load

# Retry Configuration
MAX_RETRIES = 3  # Maximum number of retry attempts
RETRY_DELAY = 2  # Delay between retries in seconds
