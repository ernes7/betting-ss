"""Global constants shared across all sports modules.

IMPORTANT: This file is maintained for backwards compatibility.
New code should import from shared.config instead:

    from shared.config import SPORTS_REFERENCE_RATE_LIMIT_CALLS, SPORTS_REFERENCE_RATE_LIMIT_PERIOD

All configuration has been moved to shared/config/ for better organization.
"""

# Import from new config location
from shared.config import (
    SPORTS_REFERENCE_RATE_LIMIT_CALLS,
    SPORTS_REFERENCE_RATE_LIMIT_PERIOD
)

# Re-export for backwards compatibility
__all__ = [
    "SPORTS_REFERENCE_RATE_LIMIT_CALLS",
    "SPORTS_REFERENCE_RATE_LIMIT_PERIOD"
]
