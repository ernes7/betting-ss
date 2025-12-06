"""Configuration for the ODDS service.

The odds service is a sport-agnostic black box that:
- Takes API URLs and market mappings as input
- Outputs CSV files (game_lines.csv, player_props.csv)

Sport-specific configurations should be defined in sports/{sport}/config.py
"""

from dataclasses import dataclass, field
from typing import Dict, Set

from shared.scraping import ScraperConfig, DRAFTKINGS_CONFIG


@dataclass(frozen=True)
class OddsServiceConfig:
    """Configuration for the ODDS service.

    This is a sport-agnostic configuration. All sport-specific details
    (API URLs, market mappings) must be provided explicitly.

    Attributes:
        api_url_template: API URL template with {event_id} placeholder
        league_url: League API URL for fetching schedule/upcoming games
        market_name_map: Mapping from DraftKings market names to prop names
        included_markets: Market types to include
        excluded_markets: Market types to explicitly exclude
        scraper_config: Scraping configuration (delays, timeouts)
        data_root: Root directory for odds data
        source: Odds source name (draftkings, etc.)

    Example:
        config = OddsServiceConfig(
            api_url_template="https://sportsbook.draftkings.com/api/.../events/{event_id}/categories",
            league_url="https://sportsbook.draftkings.com/api/.../leagues/88808",
            market_name_map={"Passing Yards Milestones": "passing_yards", ...},
            included_markets={"Moneyline", "Spread", "Total", ...},
        )
    """
    # API URL template - {event_id} placeholder
    api_url_template: str = ""

    # League API URL for schedule/upcoming games
    league_url: str = ""

    # Market name to prop name mapping
    market_name_map: Dict[str, str] = field(default_factory=dict)

    # Market filters
    included_markets: Set[str] = field(default_factory=set)
    excluded_markets: Set[str] = field(default_factory=set)

    # Market categories for parsing strategy
    player_prop_markets: Set[str] = field(default_factory=set)  # player-per-selection format
    milestone_markets: Set[str] = field(default_factory=set)    # milestone/line format
    game_prop_markets: Set[str] = field(default_factory=set)    # game-level props (BTTS, corners, etc.)

    # Scraper and storage config
    scraper_config: ScraperConfig = field(default_factory=lambda: DRAFTKINGS_CONFIG)
    data_root: str = "sports/{sport}/data/odds"
    source: str = "draftkings"

    def validate(self) -> None:
        """Validate that required fields are set.

        Raises:
            ValueError: If required fields are missing
        """
        if not self.api_url_template:
            raise ValueError("OddsServiceConfig requires api_url_template")
        if not self.market_name_map:
            raise ValueError("OddsServiceConfig requires market_name_map")
