"""Bundesliga-specific configuration implementing SportConfig interface."""

from shared.base.sport_config import SportConfig
from sports.futbol.bundesliga.teams import TEAMS, NAME_TO_FBREF_ID, NAME_TO_SLUG
from sports.futbol.bundesliga.constants import (
    FBREF_RATE_LIMIT_CALLS,
    FBREF_RATE_LIMIT_PERIOD,
    BUNDESLIGA_STATS_URL,
    TEAM_URL_PATTERN,
    RANKING_TABLES,
    PROFILE_TABLES,
    DATA_RANKINGS_DIR,
    DATA_PROFILES_DIR,
)
from sports.futbol.bundesliga.prompt_components import BundesligaPromptComponents


class BundesligaConfig(SportConfig):
    """Bundesliga-specific configuration."""

    @property
    def sport_name(self) -> str:
        return "bundesliga"

    @property
    def teams(self) -> list[dict]:
        return TEAMS

    @property
    def ranking_tables(self) -> dict[str, str]:
        return RANKING_TABLES

    @property
    def profile_tables(self) -> dict[str, str]:
        return PROFILE_TABLES

    @property
    def result_tables(self) -> dict[str, str]:
        # Not implemented yet (no odds/results scraping)
        return {}

    @property
    def stats_url(self) -> str:
        return BUNDESLIGA_STATS_URL

    @property
    def rate_limit_calls(self) -> int:
        return FBREF_RATE_LIMIT_CALLS

    @property
    def rate_limit_period(self) -> int:
        return FBREF_RATE_LIMIT_PERIOD

    @property
    def data_rankings_dir(self) -> str:
        return DATA_RANKINGS_DIR

    @property
    def data_profiles_dir(self) -> str:
        return DATA_PROFILES_DIR

    @property
    def predictions_dir(self) -> str:
        return "sports/futbol/bundesliga/data/predictions"

    @property
    def results_dir(self) -> str:
        return "sports/futbol/bundesliga/data/results"

    @property
    def analysis_dir(self) -> str:
        return "sports/futbol/bundesliga/data/analysis"

    @property
    def prompt_components(self) -> BundesligaPromptComponents:
        return BundesligaPromptComponents()

    def build_team_url(self, team_name: str) -> str:
        """Build Bundesliga team URL using FBRef pattern.

        Args:
            team_name: Full team name (e.g., "Bayern Munich")

        Returns:
            Complete URL for the team's page
        """
        fbref_id = NAME_TO_FBREF_ID.get(team_name)
        slug = NAME_TO_SLUG.get(team_name)

        if not fbref_id or not slug:
            raise ValueError(f"Team '{team_name}' not found in Bundesliga teams")

        return TEAM_URL_PATTERN.format(fbref_id=fbref_id, slug=slug)

    def build_boxscore_url(self, game_date: str, home_team_abbr: str) -> str:
        """Build URL for match boxscore/results page.

        Note: Not implemented yet for Bundesliga.

        Args:
            game_date: Game date in YYYY-MM-DD format
            home_team_abbr: Home team abbreviation

        Returns:
            Placeholder - raises NotImplementedError
        """
        raise NotImplementedError("Boxscore URL not implemented for Bundesliga yet")
