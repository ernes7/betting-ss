"""Bundesliga-specific configuration implementing SportConfig interface."""

from typing import Callable

from shared.base.sport_config import SportConfig
from services.odds.config import OddsServiceConfig
from services.stats.config import StatsServiceConfig
from shared.scraping import FBREF_CONFIG
from sports.futbol.bundesliga.constants import (
    FBREF_RATE_LIMIT_CALLS,
    FBREF_RATE_LIMIT_PERIOD,
    PROFILE_TABLES,
    RANKING_TABLES,
    DATA_RANKINGS_DIR,
    DATA_PROFILES_DIR,
    BUNDESLIGA_STATS_URL,
    TEAM_URL_PATTERN,
)
from sports.futbol.bundesliga.prompt_components import BundesligaPromptComponents
from sports.futbol.bundesliga.prompt_builder import build_bundesliga_prompt


class BundesligaConfig(SportConfig):
    """Bundesliga-specific configuration."""

    @property
    def sport_name(self) -> str:
        return "bundesliga"

    @property
    def profile_tables(self) -> dict[str, str]:
        return PROFILE_TABLES

    @property
    def result_tables(self) -> dict[str, str]:
        # Not implemented yet (no odds/results scraping)
        return {}

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
    def prompt_components(self):
        return
        # return BundesligaPromptComponents()

    @property
    def prompt_builder(self) -> Callable:
        """Return Bundesliga-specific prompt builder."""
        return build_bundesliga_prompt

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


def get_bundesliga_odds_config() -> OddsServiceConfig:
    """Get Bundesliga-specific odds service configuration.

    Returns:
        OddsServiceConfig with DraftKings endpoints for Bundesliga.
        Includes game lines and soccer-specific markets.

    Example:
        from sports.futbol.bundesliga.bundesliga_config import get_bundesliga_odds_config
        from services.odds import OddsService

        config = get_bundesliga_odds_config()
        service = OddsService(sport="bundesliga", config=config)
        schedule = service.fetch_schedule()
    """
    return OddsServiceConfig(
        api_url_template="https://sportsbook-nash.draftkings.com/api/sportscontent/dkusnj/v1/events/{event_id}/categories",
        league_url="https://sportsbook-nash.draftkings.com/api/sportscontent/dkusnj/v1/leagues/40481",
        data_root="sports/futbol/bundesliga/data/odds",
        market_name_map={
            # Game props - Yes/No
            "Both Teams to Score": "btts",
            # Game props - 3-way
            "Double Chance": "double_chance",
            "Tie No Bet": "tie_no_bet",
            # Game props - Over/Under
            "Total Goals": "total_goals",
            "Team Total Goals": "team_total_goals",
            "Total Corners": "total_corners",
            "Team Total Corners": "team_total_corners",
            # Other game props
            "Asian Handicap": "asian_handicap",
            "Moneyline 1st Half": "moneyline_1h",
            # Player props - goalscorer
            "1st Goalscorer": "first_goalscorer",
            "Anytime Goalscorer": "anytime_goalscorer",
            "To Score 2 or More Goalscorer": "two_plus_goals",
            # Player props - milestones
            "Player Shots on Target": "shots_on_target",
        },
        included_markets={
            # Game lines
            "Moneyline", "Total", "Spread",
            # Game props
            "Both Teams to Score", "Double Chance", "Tie No Bet",
            "Total Goals", "Team Total Goals",
            "Total Corners", "Team Total Corners",
            # Player props - goalscorer
            "1st Goalscorer", "Anytime Goalscorer",
            "To Score 2 or More Goalscorer",
            # Player props - milestones
            "Player Shots on Target",
        },
        excluded_markets=set(),
        # Market categories for parsing strategy
        player_prop_markets={
            "Anytime Goalscorer",
            "1st Goalscorer",
            "To Score 2 or More Goalscorer",
        },
        milestone_markets={
            "Player Shots on Target",
        },
        game_prop_markets={
            "Both Teams to Score",
            "Double Chance",
            "Total Goals",
            "Team Total Goals",
            "Total Corners",
            "Team Total Corners",
        },
    )


def get_bundesliga_stats_config() -> StatsServiceConfig:
    """Get Bundesliga-specific stats service configuration.

    Returns:
        StatsServiceConfig with FBRef URLs and table mappings.

    Example:
        from sports.futbol.bundesliga.bundesliga_config import get_bundesliga_stats_config
        from services.stats import StatsService

        config = get_bundesliga_stats_config()
        service = StatsService(sport="bundesliga", config=config)
        rankings = service.fetch_rankings()
    """
    return StatsServiceConfig(
        base_url="https://fbref.com",
        rankings_url=BUNDESLIGA_STATS_URL,
        team_profile_url_template=TEAM_URL_PATTERN,
        rankings_tables=RANKING_TABLES,
        profile_tables=PROFILE_TABLES,
        data_root="sports/futbol/bundesliga/data",
        scraper_config=FBREF_CONFIG,  # Use cloudscraper for Cloudflare bypass
    )
