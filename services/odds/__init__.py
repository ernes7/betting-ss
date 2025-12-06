"""ODDS Service - Sport-agnostic odds fetching and storage.

This is a black box service that:
- Takes sport configuration as input (API URLs, market mappings)
- Fetches odds from DraftKings
- Outputs CSV files (game_lines.csv, player_props.csv)

All sport-specific details come from the config parameter.

Example:
    from services.odds import OddsService, OddsServiceConfig
    from sports.nfl.nfl_config import get_nfl_odds_config

    # Create service with NFL config
    config = get_nfl_odds_config()
    service = OddsService(sport="nfl", config=config)

    # Fetch odds from URL
    odds = service.fetch_from_url(draftkings_url)

    # Save odds as CSV
    path = service.save_odds(odds)

    # Load existing odds
    odds = service.load_odds("2024-12-01", "dal", "nyg")
"""

from services.odds.config import OddsServiceConfig
from services.odds.parser import DraftKingsParser
from services.odds.scraper import OddsScraper
from services.odds.service import OddsService

__all__ = [
    "OddsService",
    "OddsServiceConfig",
    "OddsScraper",
    "DraftKingsParser",
]
