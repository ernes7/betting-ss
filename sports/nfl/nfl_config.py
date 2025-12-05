"""NFL-specific configuration implementing SportConfig interface."""

from shared.base.sport_config import SportConfig
from config import settings
from sports.nfl.teams import TEAMS
from sports.nfl.tables import (
    RANKINGS_TABLES,
    DEFENSE_TABLES,
    PROFILE_TABLES,
    RESULT_TABLES,
    RANKINGS_URL,
    DEFENSE_URL,
)
from sports.nfl.prompt_components import NFLPromptComponents


# NFL Season Year (loaded from config/settings.yaml via CURRENT_YEAR property)
NFL_SEASON_YEAR = 2025

# Odds market types for DraftKings scraping
NFL_ODDS_MARKET_TYPES = {
    # Game lines
    "game_lines": ["Moneyline", "Spread", "Total"],
    # Player props - Passing
    "passing_props": [
        "Passing Yards Milestones",
        "Passing Touchdowns Milestones",
        "Pass Completions Milestones",
        "Pass Attempts Milestones",
    ],
    # Player props - Rushing
    "rushing_props": [
        "Rushing Yards Milestones",
        "Rushing Attempts Milestones",
        "Rushing + Receiving Yards Milestones",
    ],
    # Player props - Receiving
    "receiving_props": [
        "Receiving Yards Milestones",
        "Receptions Milestones",
    ],
    # Touchdown scorers
    "touchdown_props": ["Anytime Touchdown Scorer"],
    # Defensive props
    "defensive_props": [
        "Sacks Milestones",
        "Tackles + Assists Milestones",
        "Interceptions Milestones",
    ],
}


class NFLConfig(SportConfig):
    """NFL-specific configuration."""

    @property
    def sport_name(self) -> str:
        return "nfl"

    @property
    def season_year(self) -> int:
        return NFL_SEASON_YEAR

    @property
    def teams(self) -> list[dict]:
        return TEAMS

    @property
    def ranking_tables(self) -> dict:
        return RANKINGS_TABLES

    @property
    def profile_tables(self) -> dict:
        return PROFILE_TABLES

    @property
    def result_tables(self) -> dict[str, str]:
        return RESULT_TABLES

    @property
    def stats_url(self) -> str:
        return RANKINGS_URL

    @property
    def defensive_stats_url(self) -> str:
        return DEFENSE_URL

    @property
    def defensive_ranking_tables(self) -> dict:
        return DEFENSE_TABLES

    @property
    def rate_limit_calls(self) -> int:
        return settings['scraping']['sports_reference']['rate_limit_calls']

    @property
    def rate_limit_period(self) -> int:
        return settings['scraping']['sports_reference']['rate_limit_period']

    @property
    def odds_market_types(self) -> dict:
        return NFL_ODDS_MARKET_TYPES

    @property
    def data_rankings_dir(self) -> str:
        return "sports/nfl/data/rankings"

    @property
    def data_profiles_dir(self) -> str:
        return "sports/nfl/data/profiles"

    @property
    def predictions_dir(self) -> str:
        return "sports/nfl/data/predictions"

    @property
    def predictions_ev_dir(self) -> str:
        return "sports/nfl/data/predictions_ev"

    @property
    def results_dir(self) -> str:
        return "sports/nfl/data/results"

    @property
    def analysis_dir(self) -> str:
        return "sports/nfl/data/analysis"

    @property
    def analysis_ev_dir(self) -> str:
        return "sports/nfl/data/analysis_ev"

    @property
    def prompt_components(self) -> NFLPromptComponents:
        return NFLPromptComponents()

    def build_team_url(self, team_abbr: str) -> str:
        """Build NFL team URL using Pro-Football-Reference pattern.

        Args:
            team_abbr: PFR team abbreviation (e.g., "mia" for Miami Dolphins)

        Returns:
            Complete URL for the team's page
        """
        return f"https://www.pro-football-reference.com/teams/{team_abbr}/{NFL_SEASON_YEAR}.htm"

    def build_boxscore_url(self, game_date: str, home_team_abbr: str) -> str:
        """Build NFL boxscore URL using Pro-Football-Reference pattern.

        Args:
            game_date: Game date in YYYY-MM-DD format
            home_team_abbr: PFR home team abbreviation (e.g., "buf")

        Returns:
            Complete URL for the game's boxscore page

        Example:
            build_boxscore_url("2025-10-23", "sdg")
            -> "https://www.pro-football-reference.com/boxscores/202510230sdg.htm"

        Note:
            PFR URLs include a "0" prefix before the team abbreviation
        """
        date_str = game_date.replace("-", "")  # "2025-10-23" -> "20251023"
        return f"https://www.pro-football-reference.com/boxscores/{date_str}0{home_team_abbr}.htm"
