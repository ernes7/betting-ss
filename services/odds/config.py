"""Configuration for the ODDS service."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Set

from shared.scraping import ScraperConfig, DRAFTKINGS_CONFIG


@dataclass(frozen=True)
class OddsServiceConfig:
    """Configuration for the ODDS service.

    Attributes:
        scraper_config: Scraping configuration (delays, timeouts)
        data_root: Root directory for odds data
        source: Odds source name (draftkings, etc.)
        included_markets: Market types to include
        excluded_markets: Market types to explicitly exclude
    """
    scraper_config: ScraperConfig = field(default_factory=lambda: DRAFTKINGS_CONFIG)
    data_root: str = "sports/{sport}/data/odds"
    source: str = "draftkings"
    included_markets: Set[str] = field(default_factory=set)
    excluded_markets: Set[str] = field(default_factory=set)


# Default NFL market configuration
NFL_INCLUDED_MARKETS = {
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
}

NFL_EXCLUDED_MARKETS = {
    "1st Quarter Moneyline",
    "1st Quarter Spread",
    "1st Quarter Total",
    "1st Half Moneyline",
    "1st Half Spread",
    "1st Half Total",
    "1st Drive Result",
    "DK Squares",
}

# Default NBA market configuration
NBA_INCLUDED_MARKETS = {
    # Game lines
    "Moneyline",
    "Spread",
    "Total",
    # Player props
    "Points Milestones",
    "Rebounds Milestones",
    "Assists Milestones",
    "3-Pointers Made Milestones",
    "Pts + Reb Milestones",
    "Pts + Ast Milestones",
    "Reb + Ast Milestones",
    "Pts + Reb + Ast Milestones",
    # Special
    "Double-Double",
    "Triple-Double",
    "First Basket",
}

NBA_EXCLUDED_MARKETS = {
    "1st Quarter Moneyline",
    "1st Quarter Spread",
    "1st Quarter Total",
    "1st Half Moneyline",
    "1st Half Spread",
    "1st Half Total",
}


def get_default_config(sport: str) -> OddsServiceConfig:
    """Get default configuration for a sport.

    Args:
        sport: Sport name (nfl, nba)

    Returns:
        OddsServiceConfig with sport-specific markets
    """
    if sport.lower() == "nfl":
        return OddsServiceConfig(
            included_markets=NFL_INCLUDED_MARKETS,
            excluded_markets=NFL_EXCLUDED_MARKETS,
        )
    elif sport.lower() == "nba":
        return OddsServiceConfig(
            included_markets=NBA_INCLUDED_MARKETS,
            excluded_markets=NBA_EXCLUDED_MARKETS,
        )
    else:
        return OddsServiceConfig()
