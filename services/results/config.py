"""Configuration for the RESULTS service."""

from dataclasses import dataclass, field
from typing import Dict

from shared.scraping import ScraperConfig, RESULTS_SCRAPER_CONFIG


@dataclass(frozen=True)
class ResultsServiceConfig:
    """Configuration for the RESULTS service.

    Attributes:
        scraper_config: Scraping configuration (intervals, timeouts)
        data_root: Root directory for results data
        result_tables: Mapping of table names to HTML IDs for extraction
    """
    scraper_config: ScraperConfig = field(default_factory=lambda: RESULTS_SCRAPER_CONFIG)
    data_root: str = "{sport}/data/results"
    result_tables: Dict[str, str] = field(default_factory=dict)


# NFL result tables to extract from Pro-Football-Reference boxscores
NFL_RESULT_TABLES = {
    "scoring": "scoring",
    "game_info": "game_info",
    "team_stats": "team_stats",
    "player_offense": "player_offense",  # Will be split into passing/rushing/receiving
    "defense": "player_defense",
    "home_starters": "home_starters",
    "away_starters": "vis_starters",
}

# NBA result tables to extract from Basketball-Reference boxscores
NBA_RESULT_TABLES = {
    "line_score": "line_score",
    "four_factors": "four_factors",
    "home_basic": "box-{home}-game-basic",  # Template - needs team abbr
    "away_basic": "box-{away}-game-basic",
    "home_advanced": "box-{home}-game-advanced",
    "away_advanced": "box-{away}-game-advanced",
}


def get_default_config(sport: str) -> ResultsServiceConfig:
    """Get default configuration for a sport.

    Args:
        sport: Sport name (nfl, nba)

    Returns:
        ResultsServiceConfig with sport-specific settings
    """
    if sport.lower() == "nfl":
        return ResultsServiceConfig(
            result_tables=NFL_RESULT_TABLES,
        )
    elif sport.lower() == "nba":
        return ResultsServiceConfig(
            result_tables=NBA_RESULT_TABLES,
        )
    else:
        return ResultsServiceConfig()


# URL templates for boxscores
BOXSCORE_URL_TEMPLATES = {
    "nfl": "https://www.pro-football-reference.com/boxscores/{date}0{home_abbr}.htm",
    "nba": "https://www.basketball-reference.com/boxscores/{game_id}.html",
}


def build_boxscore_url(sport: str, **kwargs) -> str:
    """Build boxscore URL for a sport.

    Args:
        sport: Sport name
        **kwargs: URL parameters (date, home_abbr for NFL; game_id for NBA)

    Returns:
        Formatted boxscore URL
    """
    template = BOXSCORE_URL_TEMPLATES.get(sport.lower(), "")
    return template.format(**kwargs)
