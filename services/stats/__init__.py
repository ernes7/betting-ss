"""STATS Service - Fetches and manages team rankings and profiles.

This service is responsible for:
- Fetching league-wide rankings from PFR
- Fetching team-specific profiles from PFR
- Saving stats to the data directory
- Loading and querying existing stats

Example:
    from services.stats import StatsService, StatsServiceConfig

    # Create service with default config for NFL
    service = StatsService(sport="nfl")

    # Fetch rankings
    rankings = service.fetch_rankings()

    # Save rankings
    path = service.save_rankings(rankings)

    # Fetch team profile
    profile = service.fetch_team_profile("dal")
"""

from services.stats.config import (
    StatsServiceConfig,
    get_default_config,
    NFL_RANKING_TABLES,
    NFL_DEFENSIVE_TABLES,
    NFL_PROFILE_TABLES,
)
from services.stats.fetcher import StatsFetcher
from services.stats.service import StatsService

__all__ = [
    # Main service
    "StatsService",
    # Configuration
    "StatsServiceConfig",
    "get_default_config",
    "NFL_RANKING_TABLES",
    "NFL_DEFENSIVE_TABLES",
    "NFL_PROFILE_TABLES",
    # Components
    "StatsFetcher",
]
