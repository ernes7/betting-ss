"""Configuration for the STATS service.

The stats service is a sport-agnostic black box that:
- Takes URLs and table mappings as input
- Outputs CSV files

Sport-specific configurations should be defined in sports/{sport}/config.py
"""

from dataclasses import dataclass, field
from typing import Dict, Optional

from shared.scraping import ScraperConfig, PFR_CONFIG


@dataclass(frozen=True)
class StatsServiceConfig:
    """Configuration for the STATS service.

    This is a sport-agnostic configuration. All sport-specific details
    (URLs, table mappings) must be provided explicitly.

    Attributes:
        base_url: Base URL for the sports reference site
        rankings_url: URL for league-wide rankings page
        defensive_url: URL for defensive stats page (optional)
        team_profile_url_template: URL template for team profiles
            Use {team} as placeholder for team abbreviation
        rankings_tables: Tables to extract from rankings page
        defensive_tables: Tables to extract from defensive stats page
        profile_tables: Tables to extract from team profile page
        scraper_config: Scraping configuration (delays, timeouts)
        data_root: Root directory for stats data

    Example:
        config = StatsServiceConfig(
            base_url="https://www.pro-football-reference.com",
            rankings_url="https://www.pro-football-reference.com/years/2025/",
            team_profile_url_template="https://www.pro-football-reference.com/teams/{team}/2025.htm",
            rankings_tables={"team_offense": "team_stats", ...},
        )
    """
    # URLs - must be provided by sport config
    base_url: str = ""
    rankings_url: str = ""
    defensive_url: str = ""
    team_profile_url_template: str = ""

    # Table mappings - must be provided by sport config
    rankings_tables: Dict[str, str] = field(default_factory=dict)
    defensive_tables: Dict[str, str] = field(default_factory=dict)
    profile_tables: Dict[str, str] = field(default_factory=dict)

    # Scraper and storage config
    scraper_config: ScraperConfig = field(default_factory=lambda: PFR_CONFIG)
    data_root: str = "sports/{sport}/data"

    def validate(self) -> None:
        """Validate that required fields are set.

        Raises:
            ValueError: If required URLs are missing
        """
        if not self.rankings_url:
            raise ValueError("StatsServiceConfig requires rankings_url")
        if not self.rankings_tables:
            raise ValueError("StatsServiceConfig requires rankings_tables")
