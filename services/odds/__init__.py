"""ODDS Service - Fetches and manages betting odds.

This service is responsible for:
- Fetching odds from DraftKings (via URL or saved HTML)
- Saving odds to the data directory
- Loading and querying existing odds

Example:
    from services.odds import OddsService, OddsServiceConfig

    # Create service with default config for NFL
    service = OddsService(sport="nfl")

    # Fetch odds from URL
    odds = service.fetch_from_url(draftkings_url)

    # Save odds
    path = service.save_odds(odds)

    # Load existing odds
    odds = service.load_odds("2024-12-01", "dal", "nyg")
"""

from services.odds.config import (
    OddsServiceConfig,
    get_default_config,
    NFL_INCLUDED_MARKETS,
    NFL_EXCLUDED_MARKETS,
    NBA_INCLUDED_MARKETS,
    NBA_EXCLUDED_MARKETS,
)
from services.odds.parser import DraftKingsParser
from services.odds.scraper import OddsScraper
from services.odds.service import OddsService

__all__ = [
    # Main service
    "OddsService",
    # Configuration
    "OddsServiceConfig",
    "get_default_config",
    "NFL_INCLUDED_MARKETS",
    "NFL_EXCLUDED_MARKETS",
    "NBA_INCLUDED_MARKETS",
    "NBA_EXCLUDED_MARKETS",
    # Components
    "OddsScraper",
    "DraftKingsParser",
]
