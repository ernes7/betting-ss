"""NFL-specific configuration implementing SportConfig interface."""

from shared.base.sport_config import SportConfig
from nfl.teams import TEAMS
from nfl.constants import (
    CURRENT_YEAR,
    PFR_RATE_LIMIT_CALLS,
    PFR_RATE_LIMIT_PERIOD,
    NFL_STATS_URL,
    RANKING_TABLES,
    TEAM_PROFILE_TABLES,
    RESULT_TABLES,
    DATA_RANKINGS_DIR,
    DATA_PROFILES_DIR,
)
from nfl.prompt_components import NFLPromptComponents


class NFLConfig(SportConfig):
    """NFL-specific configuration."""

    @property
    def sport_name(self) -> str:
        return "nfl"

    @property
    def teams(self) -> list[dict]:
        return TEAMS

    @property
    def ranking_tables(self) -> dict[str, str]:
        return RANKING_TABLES

    @property
    def profile_tables(self) -> dict[str, str]:
        return TEAM_PROFILE_TABLES

    @property
    def result_tables(self) -> dict[str, str]:
        return RESULT_TABLES

    @property
    def stats_url(self) -> str:
        return NFL_STATS_URL

    @property
    def rate_limit_calls(self) -> int:
        return PFR_RATE_LIMIT_CALLS

    @property
    def rate_limit_period(self) -> int:
        return PFR_RATE_LIMIT_PERIOD

    @property
    def data_rankings_dir(self) -> str:
        return DATA_RANKINGS_DIR

    @property
    def data_profiles_dir(self) -> str:
        return DATA_PROFILES_DIR

    @property
    def predictions_dir(self) -> str:
        return "nfl/data/predictions"

    @property
    def results_dir(self) -> str:
        return "nfl/data/results"

    @property
    def analysis_dir(self) -> str:
        return "nfl/data/analysis"

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
        return f"https://www.pro-football-reference.com/teams/{team_abbr}/{CURRENT_YEAR}.htm"

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
