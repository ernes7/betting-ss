"""Global constants shared across all sports modules."""

# Rate limiting for Sports-Reference sites (to avoid HTTP 429 errors)
# This applies to Pro-Football-Reference, Basketball-Reference, Hockey-Reference, etc.
# All Sports-Reference sites share the same infrastructure and rate limits
SPORTS_REFERENCE_RATE_LIMIT_CALLS = 1  # Number of calls allowed
SPORTS_REFERENCE_RATE_LIMIT_PERIOD = 5  # Time period in seconds
