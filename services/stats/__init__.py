"""STATS Service - Sport-agnostic stats fetching and storage.

This is a black box service that:
- Takes sport configuration as input (URLs, table mappings)
- Fetches HTML tables from sports reference sites
- Outputs CSV files

All sport-specific details come from the config parameter.

Example:
    from services.stats import StatsService, StatsServiceConfig
    from sports.nfl.nfl_config import get_nfl_stats_config

    # Create service with NFL config
    config = get_nfl_stats_config()
    service = StatsService(sport="nfl", config=config)

    # Fetch rankings
    rankings = service.fetch_rankings()

    # Save rankings as CSV
    path = service.save_rankings(rankings)

    # Fetch team profile
    profile = service.fetch_team_profile("dal")
"""

from services.stats.config import StatsServiceConfig
from services.stats.fetcher import StatsFetcher
from services.stats.service import StatsService

__all__ = [
    "StatsService",
    "StatsServiceConfig",
    "StatsFetcher",
]
