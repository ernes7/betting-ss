"""Timezone utilities for consistent Eastern Time usage across the app.

All datetime operations in this application use US Eastern Time (America/New_York)
to ensure consistent filing and display of sports betting data, regardless of where
the application is run.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

# US Eastern timezone (handles EST/EDT automatically)
EASTERN_TZ = ZoneInfo("America/New_York")


def get_eastern_now() -> datetime:
    """Get current time in US Eastern timezone (handles EST/EDT automatically).

    Returns:
        datetime: Current time in Eastern timezone with tzinfo

    Example:
        >>> now = get_eastern_now()
        >>> now.tzinfo
        ZoneInfo(key='America/New_York')
    """
    return datetime.now(EASTERN_TZ)


def get_eastern_now_naive() -> datetime:
    """Get current time in US Eastern timezone as naive datetime.

    Returns:
        datetime: Current time in Eastern timezone without tzinfo

    Example:
        >>> now = get_eastern_now_naive()
        >>> now.tzinfo is None
        True
    """
    return datetime.now(EASTERN_TZ).replace(tzinfo=None)


def utc_to_eastern(utc_dt: datetime) -> datetime:
    """Convert UTC datetime to Eastern timezone.

    Args:
        utc_dt: Datetime in UTC (aware or naive)

    Returns:
        datetime: Datetime converted to Eastern timezone

    Example:
        >>> from datetime import datetime
        >>> utc = datetime(2025, 11, 10, 1, 20, 0)  # 1:20 AM UTC
        >>> eastern = utc_to_eastern(utc)
        >>> eastern.hour  # 8:20 PM previous day in EST
        20
    """
    if utc_dt.tzinfo is None:
        # Assume UTC if naive
        utc_dt = utc_dt.replace(tzinfo=ZoneInfo("UTC"))
    return utc_dt.astimezone(EASTERN_TZ)


def parse_iso_to_eastern(iso_str: str) -> datetime:
    """Parse ISO timestamp (with Z suffix) to Eastern timezone.

    DraftKings API returns timestamps in UTC with 'Z' suffix.
    This function converts them to Eastern time for correct date filing.

    Args:
        iso_str: ISO format timestamp string (e.g., "2025-11-10T01:20:00Z")

    Returns:
        datetime: Datetime in Eastern timezone

    Example:
        >>> dt = parse_iso_to_eastern("2025-11-10T01:20:00Z")
        >>> dt.strftime("%Y-%m-%d %H:%M")  # Nov 9, 8:20 PM EST
        '2025-11-09 20:20'
    """
    # Replace Z with +00:00 for fromisoformat compatibility
    utc_dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return utc_dt.astimezone(EASTERN_TZ)


def get_eastern_date_folder() -> str:
    """Get current date in YYYY-MM-DD format based on Eastern time.

    Used for creating date-based folder names for odds, predictions, and results.

    Returns:
        str: Date string in YYYY-MM-DD format

    Example:
        >>> folder = get_eastern_date_folder()
        >>> folder
        '2025-11-09'
    """
    return get_eastern_now().strftime("%Y-%m-%d")


def iso_to_eastern_date_folder(iso_str: str) -> str:
    """Convert ISO timestamp to Eastern date folder string.

    Args:
        iso_str: ISO format timestamp string (e.g., "2025-11-10T01:20:00Z")

    Returns:
        str: Date string in YYYY-MM-DD format based on Eastern timezone

    Example:
        >>> folder = iso_to_eastern_date_folder("2025-11-10T01:20:00Z")
        >>> folder  # Nov 9 in Eastern time
        '2025-11-09'
    """
    eastern_dt = parse_iso_to_eastern(iso_str)
    return eastern_dt.strftime("%Y-%m-%d")
