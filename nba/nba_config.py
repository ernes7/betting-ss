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
