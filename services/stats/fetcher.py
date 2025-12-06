"""Stats fetcher for extracting team rankings and profiles.

Sport-agnostic fetcher that extracts HTML tables from sports reference sites.
All URLs and table configurations come from the StatsServiceConfig.
"""

from typing import Any, Optional, Dict
import pandas as pd

from services.stats.config import StatsServiceConfig
from shared.logging import get_logger
from shared.errors import StatsFetchError, StatsParseError
from shared.scraping import Scraper

logger = get_logger("stats")


class StatsFetcher:
    """Sport-agnostic fetcher for extracting stats from sports reference sites.

    This is a black box that:
    - Takes URLs and table configs from StatsServiceConfig
    - Fetches HTML from those URLs
    - Extracts tables by their HTML IDs
    - Returns structured data

    The fetcher has no knowledge of specific sports - all sport-specific
    details come from the config.

    Attributes:
        config: Stats service configuration with URLs and table mappings
        sport: Sport identifier (for logging and data paths)
        scraper: Scraper instance for HTTP requests

    Example:
        from sports.nfl.nfl_config import get_nfl_stats_config

        config = get_nfl_stats_config()
        fetcher = StatsFetcher(sport="nfl", config=config)
        rankings = fetcher.fetch_rankings()
    """

    def __init__(
        self,
        sport: str,
        config: StatsServiceConfig,
        scraper: Optional[Scraper] = None,
    ):
        """Initialize the stats fetcher.

        Args:
            sport: Sport identifier (for logging/paths, e.g., 'nfl', 'bundesliga')
            config: Stats service configuration with URLs and table mappings
            scraper: Scraper instance (optional, created if not provided)

        Raises:
            ValueError: If config is missing required URLs
        """
        self.sport = sport.lower()
        self.config = config

        # Validate config
        if not config.rankings_url:
            raise ValueError("StatsServiceConfig must provide rankings_url")

        self.scraper = scraper or Scraper(config.scraper_config)

    def fetch_rankings(self) -> Dict[str, Any]:
        """Fetch league-wide team rankings.

        Uses rankings_url and rankings_tables from config.

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
        logger.info(f"Fetching {self.sport.upper()} rankings from {self.config.rankings_url}")

        return self._fetch_tables_from_url(
            self.config.rankings_url,
            self.config.rankings_tables,
            "rankings"
        )

    def fetch_defensive_stats(self) -> Dict[str, Any]:
        """Fetch defensive statistics.

        Uses defensive_url and defensive_tables from config.

        Returns:
            Dictionary with defensive tables

        Raises:
            StatsFetchError: If fetching fails or defensive_url not configured
            StatsParseError: If parsing fails
        """
        if not self.config.defensive_url:
            raise StatsFetchError(
                "Defensive stats URL not configured",
                context={"sport": self.sport}
            )

        logger.info(f"Fetching {self.sport.upper()} defensive stats from {self.config.defensive_url}")

        return self._fetch_tables_from_url(
            self.config.defensive_url,
            self.config.defensive_tables,
            "defensive"
        )

    def fetch_team_profile(self, team_abbr: str) -> Dict[str, Any]:
        """Fetch team profile data.

        Uses team_profile_url_template and profile_tables from config.

        Args:
            team_abbr: Team abbreviation (e.g., 'dal', 'buf')

        Returns:
            Dictionary with team profile tables

        Raises:
            StatsFetchError: If fetching fails or URL template not configured
            StatsParseError: If parsing fails
        """
        if not self.config.team_profile_url_template:
            raise StatsFetchError(
                "Team profile URL template not configured",
                context={"sport": self.sport}
            )

        # Build URL from template (don't lowercase - FBRef URLs are case-sensitive)
        url = self.config.team_profile_url_template.format(team=team_abbr)

        logger.info(f"Fetching {self.sport.upper()} profile for {team_abbr.upper()} from {url}")

        # Profile tables may have dynamic IDs based on team abbreviation
        tables_config = {}
        for table_name, table_id in self.config.profile_tables.items():
            if "{team}" in table_id:
                tables_config[table_name] = table_id.format(team=team_abbr.lower())
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
            new_cols = []
            for col in df.columns.values:
                # Filter out "Unnamed" levels (FBRef uses these for uncategorized columns)
                parts = [str(c) for c in col if not str(c).startswith('Unnamed:')]
                new_cols.append('_'.join(parts) if parts else str(col[-1]))
            df.columns = new_cols

        # Clean column names
        df.columns = [str(c).strip() for c in df.columns]

        # Convert to records
        data = df.to_dict(orient='records')

        return {
            "table_name": table_name,
            "columns": df.columns.tolist(),
            "data": data
        }
