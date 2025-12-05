"""Stats fetcher for extracting team rankings and profiles from PFR.

Fetches league-wide rankings and team-specific profiles using pandas-based scraping.
"""

from typing import Any, Optional, Dict, List
import pandas as pd

from services.stats.config import StatsServiceConfig, get_default_config
from shared.logging import get_logger
from shared.errors import StatsFetchError, StatsParseError
from shared.scraping import Scraper

logger = get_logger("stats")


# URLs
BASE_URL = "https://www.pro-football-reference.com"
NFL_RANKINGS_URL = f"{BASE_URL}/years/2025/"
NFL_DEFENSIVE_URL = f"{BASE_URL}/years/2025/opp.htm"


def get_team_profile_url(sport: str, team_abbr: str) -> str:
    """Get team profile URL for a given abbreviation.

    Args:
        sport: Sport name (nfl, nba)
        team_abbr: Team abbreviation (e.g., 'dal', 'buf')

    Returns:
        URL to team profile page
    """
    if sport.lower() == "nfl":
        return f"{BASE_URL}/teams/{team_abbr.lower()}/2025.htm"
    raise ValueError(f"Unknown sport: {sport}")


class StatsFetcher:
    """Fetcher for extracting stats from PFR pages.

    Uses pandas to extract HTML tables from pro-football-reference.

    Attributes:
        config: Stats service configuration
        sport: Sport being fetched (nfl, nba)
        scraper: Scraper instance

    Example:
        fetcher = StatsFetcher(sport="nfl")
        rankings = fetcher.fetch_rankings()
        profile = fetcher.fetch_team_profile("dal")
    """

    def __init__(
        self,
        sport: str,
        config: Optional[StatsServiceConfig] = None,
        scraper: Optional[Scraper] = None,
    ):
        """Initialize the stats fetcher.

        Args:
            sport: Sport to fetch (nfl, nba)
            config: Stats service configuration
            scraper: Scraper instance (optional, created if not provided)
        """
        self.sport = sport.lower()
        self.config = config or get_default_config(self.sport)
        self.scraper = scraper or Scraper(self.config.scraper_config)

    def fetch_rankings(self) -> Dict[str, Any]:
        """Fetch league-wide team rankings.

        Returns:
            Dictionary with rankings tables:
            {
                "sport": str,
                "url": str,
                "fetched_at": str,
                "tables": {
                    "team_offense": {...},
                    "passing_offense": {...},
                    ...
                }
            }

        Raises:
            StatsFetchError: If fetching fails
            StatsParseError: If parsing fails
        """
        logger.info(f"Fetching {self.sport.upper()} rankings")

        if self.sport == "nfl":
            url = NFL_RANKINGS_URL
        else:
            raise StatsFetchError(f"Unknown sport: {self.sport}")

        return self._fetch_tables_from_url(url, self.config.rankings_tables, "rankings")

    def fetch_defensive_stats(self) -> Dict[str, Any]:
        """Fetch defensive statistics.

        Returns:
            Dictionary with defensive tables

        Raises:
            StatsFetchError: If fetching fails
            StatsParseError: If parsing fails
        """
        logger.info(f"Fetching {self.sport.upper()} defensive stats")

        if self.sport == "nfl":
            url = NFL_DEFENSIVE_URL
        else:
            raise StatsFetchError(f"Unknown sport: {self.sport}")

        return self._fetch_tables_from_url(url, self.config.defensive_tables, "defensive")

    def fetch_team_profile(self, team_abbr: str) -> Dict[str, Any]:
        """Fetch team profile data.

        Args:
            team_abbr: Team abbreviation (e.g., 'dal', 'buf')

        Returns:
            Dictionary with team profile tables

        Raises:
            StatsFetchError: If fetching fails
            StatsParseError: If parsing fails
        """
        logger.info(f"Fetching {self.sport.upper()} profile for {team_abbr.upper()}")

        url = get_team_profile_url(self.sport, team_abbr)

        # Profile tables may have dynamic IDs based on team abbreviation
        tables_config = {}
        for table_name, table_id in self.config.profile_tables.items():
            if "{pfr_abbr}" in table_id:
                tables_config[table_name] = table_id.format(pfr_abbr=team_abbr.lower())
            else:
                tables_config[table_name] = table_id

        result = self._fetch_tables_from_url(url, tables_config, "profile")
        result["team"] = team_abbr.upper()
        return result

    def _fetch_tables_from_url(
        self,
        url: str,
        tables_config: Dict[str, str],
        data_type: str,
    ) -> Dict[str, Any]:
        """Fetch and extract tables from a URL.

        Args:
            url: URL to fetch
            tables_config: Dictionary mapping table names to HTML IDs
            data_type: Type of data being fetched (for logging)

        Returns:
            Dictionary with extracted tables

        Raises:
            StatsFetchError: If fetching fails
            StatsParseError: If parsing fails
        """
        from shared.utils.timezone_utils import get_eastern_now
        import re

        result_data = {
            "sport": self.sport,
            "url": url,
            "data_type": data_type,
            "fetched_at": get_eastern_now().strftime("%Y-%m-%d %H:%M:%S"),
            "tables": {}
        }

        try:
            # Fetch HTML and extract all tables
            html = self.scraper.fetch_html(url)
            all_tables = self.scraper.extract_tables(html, extract_comments=True)

            logger.info(f"Found {len(all_tables)} tables on {data_type} page")

            tables_extracted = 0
            tables_missing = []

            # Extract configured tables
            for table_name, table_id in tables_config.items():
                logger.debug(f"Looking for {table_name} (#{table_id})")

                # Find table in HTML by ID
                table_pattern = rf'<table[^>]*id="{table_id}"[^>]*>'
                match = re.search(table_pattern, html)

                if match:
                    # Count tables before this one
                    html_before = html[:match.start()]
                    tables_before = len(re.findall(r'<table[^>]*>', html_before))

                    # Also count tables in comments before this point
                    comments_before = re.findall(r'<!--(.+?)-->', html_before, re.DOTALL)
                    for comment in comments_before:
                        tables_before += len(re.findall(r'<table[^>]*>', comment))

                    if tables_before < len(all_tables):
                        df = all_tables[tables_before]
                        table_data = self._dataframe_to_dict(df, table_name)
                        result_data["tables"][table_name] = table_data
                        tables_extracted += 1
                        logger.debug(f"Extracted {len(table_data.get('data', []))} rows from {table_name}")
                        continue

                tables_missing.append(table_name)
                logger.debug(f"Table '{table_id}' not found")

            logger.info(
                f"Extracted {tables_extracted}/{len(tables_config)} {data_type} tables"
            )

            if tables_missing:
                logger.warning(f"Missing tables: {', '.join(tables_missing)}")

            return result_data

        except StatsParseError:
            raise
        except Exception as e:
            raise StatsFetchError(
                f"Failed to fetch {data_type}: {e}",
                context={"url": url, "error": str(e)}
            )

    def _dataframe_to_dict(self, df: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        """Convert DataFrame to standard table dict format.

        Args:
            df: DataFrame to convert
            table_name: Name for the table

        Returns:
            Dictionary with table_name, columns, and data
        """
        # Handle multi-level columns by flattening
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ['_'.join(str(c) for c in col).strip('_') for col in df.columns.values]

        # Clean column names
        df.columns = [str(c).strip() for c in df.columns]

        # Convert to records
        data = df.to_dict(orient='records')

        return {
            "table_name": table_name,
            "columns": df.columns.tolist(),
            "data": data
        }
