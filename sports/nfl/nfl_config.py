"""NFL-specific configuration implementing SportConfig interface."""

from shared.base.sport_config import SportConfig
from config import settings
from sports.nfl.tables import (
    PROFILE_TABLES,
    RESULT_TABLES,
    BASE_URL,
    RANKINGS_URL,
    DEFENSE_URL,
)
from sports.nfl.prompt_components import NFLPromptComponents
from services.stats.config import StatsServiceConfig
from services.odds.config import OddsServiceConfig


class NFLConfig(SportConfig):
    """NFL-specific configuration."""

    @property
    def sport_name(self) -> str:
        return "nfl"

    @property
    def profile_tables(self) -> dict:
        return PROFILE_TABLES

    @property
    def result_tables(self) -> dict[str, str]:
        return RESULT_TABLES

    @property
    def rate_limit_calls(self) -> int:
        return settings['scraping']['sports_reference']['rate_limit_calls']

    @property
    def rate_limit_period(self) -> int:
        return settings['scraping']['sports_reference']['rate_limit_period']

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
    def results_dir(self) -> str:
        return "sports/nfl/data/results"

    @property
    def analysis_dir(self) -> str:
        return "sports/nfl/data/analysis"

    @property
    def prompt_components(self) -> NFLPromptComponents:
        return NFLPromptComponents()

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


def get_nfl_stats_config() -> StatsServiceConfig:
    """Get NFL-specific stats service configuration.

    Returns:
        StatsServiceConfig with NFL URLs and table mappings for PFR scraping.

    Example:
        from sports.nfl.nfl_config import get_nfl_stats_config
        from services.stats import StatsService

        config = get_nfl_stats_config()
        service = StatsService(sport="nfl", config=config)
        rankings = service.fetch_rankings()
    """
    return StatsServiceConfig(
        base_url=BASE_URL,
        rankings_url=RANKINGS_URL,
        defensive_url=DEFENSE_URL,
        team_profile_url_template=f"{BASE_URL}/teams/{{team}}/2025.htm",
        rankings_tables={
            "team_offense": "team_stats",
            "passing_offense": "passing",
            "rushing_offense": "rushing",
            "scoring_offense": "team_scoring",
            "afc_standings": "AFC",
            "nfc_standings": "NFC",
        },
        defensive_tables={
            "team_defense": "team_stats",
            "advanced_defense": "advanced_defense",
            "passing_defense": "passing",
            "rushing_defense": "rushing",
            "scoring_defense": "team_scoring",
        },
        profile_tables={
            "injury_report": "{team}_injury_report",
            "team_stats": "team_stats",
            "schedule_results": "games",
            "passing": "passing",
            "rushing_receiving": "rushing_and_receiving",
            "defense_fumbles": "defense",
            "scoring_summary": "scoring",
            "touchdown_log": "team_td_log",
        },
    )


def get_nfl_odds_config() -> OddsServiceConfig:
    """Get NFL-specific odds service configuration.

    Returns:
        OddsServiceConfig with NFL market mappings for DraftKings scraping.

    Example:
        from sports.nfl.nfl_config import get_nfl_odds_config
        from services.odds import OddsService

        config = get_nfl_odds_config()
        service = OddsService(sport="nfl", config=config)
        odds = service.fetch_from_url(draftkings_url)
    """
    return OddsServiceConfig(
        api_url_template="https://sportsbook-nash.draftkings.com/api/sportscontent/dkusnj/v1/events/{event_id}/categories",
        league_url="https://sportsbook-nash.draftkings.com/api/sportscontent/dkusnj/v1/leagues/88808",
        market_name_map={
            # Passing
            "Passing Yards Milestones": "passing_yards",
            "Passing Touchdowns Milestones": "passing_tds",
            "Pass Completions Milestones": "pass_completions",
            "Pass Attempts Milestones": "pass_attempts",
            # Rushing
            "Rushing Yards Milestones": "rushing_yards",
            "Rushing Attempts Milestones": "rush_attempts",
            # Receiving
            "Receiving Yards Milestones": "receiving_yards",
            "Receptions Milestones": "receptions",
            "Rushing + Receiving Yards Milestones": "rush_rec_yards",
            "Rushing and Receiving Yards Milestones": "rush_rec_yards",
            # Defense
            "Sacks Milestones": "sacks",
            "Tackles + Assists Milestones": "tackles_assists",
            "Interceptions Milestones": "interceptions",
        },
        included_markets={
            # Game lines
            "Moneyline",
            "Spread",
            "Total",
            # Player props - Passing
            "Passing Yards Milestones",
            "Passing Touchdowns Milestones",
            "Pass Completions Milestones",
            "Pass Attempts Milestones",
            # Player props - Rushing
            "Rushing Yards Milestones",
            "Rushing Attempts Milestones",
            # Player props - Receiving
            "Receiving Yards Milestones",
            "Receptions Milestones",
            "Rushing + Receiving Yards Milestones",
            # TD scorers
            "Anytime Touchdown Scorer",
            # Defensive props
            "Sacks Milestones",
            "Tackles + Assists Milestones",
            "Interceptions Milestones",
        },
        excluded_markets={
            "1st Quarter Moneyline",
            "1st Quarter Spread",
            "1st Quarter Total",
            "1st Half Moneyline",
            "1st Half Spread",
            "1st Half Total",
            "1st Drive Result",
            "DK Squares",
        },
        # Market categories for parsing strategy
        player_prop_markets={
            "Anytime Touchdown Scorer",
        },
        milestone_markets={
            "Passing Yards Milestones",
            "Passing Touchdowns Milestones",
            "Pass Completions Milestones",
            "Pass Attempts Milestones",
            "Rushing Yards Milestones",
            "Rushing Attempts Milestones",
            "Receiving Yards Milestones",
            "Receptions Milestones",
            "Rushing + Receiving Yards Milestones",
            "Rushing and Receiving Yards Milestones",
            "Sacks Milestones",
            "Tackles + Assists Milestones",
            "Interceptions Milestones",
        },
    )
