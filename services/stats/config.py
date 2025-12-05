"""Configuration for the STATS service."""

from dataclasses import dataclass, field
from typing import Dict

from shared.scraping import ScraperConfig, PFR_CONFIG


@dataclass(frozen=True)
class StatsServiceConfig:
    """Configuration for the STATS service.

    Attributes:
        scraper_config: Scraping configuration (delays, timeouts)
        data_root: Root directory for stats data
        rankings_tables: Tables to extract from rankings page
        defensive_tables: Tables to extract from defensive stats page
        profile_tables: Tables to extract from team profile page
    """
    scraper_config: ScraperConfig = field(default_factory=lambda: PFR_CONFIG)
    data_root: str = "sports/{sport}/data"
    rankings_tables: Dict[str, str] = field(default_factory=dict)
    defensive_tables: Dict[str, str] = field(default_factory=dict)
    profile_tables: Dict[str, str] = field(default_factory=dict)


# NFL table configurations (from sports/nfl/constants.py)
NFL_RANKING_TABLES = {
    "team_offense": "team_stats",
    "passing_offense": "passing",
    "rushing_offense": "rushing",
    "scoring_offense": "team_scoring",
    "afc_standings": "AFC",
    "nfc_standings": "NFC",
}

NFL_DEFENSIVE_TABLES = {
    "team_defense": "team_stats",
    "advanced_defense": "advanced_defense",
    "passing_defense": "passing",
    "rushing_defense": "rushing",
}

NFL_PROFILE_TABLES = {
    "injury_report": "{pfr_abbr}_injury_report",
    "team_stats": "team_stats",
    "schedule_results": "games",
    "passing": "passing",
    "rushing_receiving": "rushing_and_receiving",
    "defense_fumbles": "defense",
    "scoring_summary": "scoring",
    "touchdown_log": "team_td_log",
}


def get_default_config(sport: str) -> StatsServiceConfig:
    """Get default configuration for a sport.

    Args:
        sport: Sport name (nfl, nba)

    Returns:
        StatsServiceConfig with sport-specific table configs
    """
    if sport.lower() == "nfl":
        return StatsServiceConfig(
            rankings_tables=NFL_RANKING_TABLES,
            defensive_tables=NFL_DEFENSIVE_TABLES,
            profile_tables=NFL_PROFILE_TABLES,
        )
    else:
        return StatsServiceConfig()
