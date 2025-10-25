"""NBA-specific configuration implementing SportConfig interface."""

from shared.base.sport_config import SportConfig
from nba.teams import TEAMS
from nba.constants import (
    CURRENT_YEAR,
    BBR_RATE_LIMIT_CALLS,
    BBR_RATE_LIMIT_PERIOD,
    NBA_STATS_URL,
    NBA_TEAM_URL_PATTERN,
    RANKING_TABLES,
    TEAM_PROFILE_TABLES,
    DATA_RANKINGS_DIR,
    DATA_PROFILES_DIR,
)
from nba.prompt_components import NBAPromptComponents


class NBAConfig(SportConfig):
    """NBA-specific configuration."""

    @property
    def sport_name(self) -> str:
        return "nba"

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
    def stats_url(self) -> str:
        return NBA_STATS_URL

    @property
    def rate_limit_calls(self) -> int:
        return BBR_RATE_LIMIT_CALLS

    @property
    def rate_limit_period(self) -> int:
        return BBR_RATE_LIMIT_PERIOD

    @property
    def data_rankings_dir(self) -> str:
        return DATA_RANKINGS_DIR

    @property
    def data_profiles_dir(self) -> str:
        return DATA_PROFILES_DIR

    @property
    def predictions_dir(self) -> str:
        return "nba/predictions"

    @property
    def results_dir(self) -> str:
        return "nba/results"

    @property
    def analysis_dir(self) -> str:
        return "nba/analysis"

    @property
    def prompt_components(self) -> NBAPromptComponents:
        return NBAPromptComponents()

    def build_team_url(self, team_abbr: str) -> str:
        """Build NBA team URL using Basketball-Reference pattern.

        Args:
            team_abbr: Basketball-Reference team abbreviation (e.g., "LAL" for Lakers)

        Returns:
            Complete URL for the team's page
        """
        return NBA_TEAM_URL_PATTERN.format(pbr_abbr=team_abbr)

    def build_boxscore_url(self, game_date: str, home_team_abbr: str) -> str:
        """Build NBA boxscore URL using Basketball-Reference pattern.

        Args:
            game_date: Game date in YYYY-MM-DD format
            home_team_abbr: Basketball-Reference home team abbreviation (e.g., "TOR")

        Returns:
            Complete URL for the game's boxscore page

        Example:
            build_boxscore_url("2025-10-24", "TOR")
            -> "https://www.basketball-reference.com/boxscores/202510240TOR.html"
        """
        date_str = game_date.replace("-", "")  # "2025-10-24" -> "20251024"
        return f"https://www.basketball-reference.com/boxscores/{date_str}0{home_team_abbr}.html"
