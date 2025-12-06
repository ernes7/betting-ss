"""Results fetcher for extracting game data from boxscore pages.

Fetches game results from sports reference sites using pandas-based scraping.
"""

from typing import Any, Optional

import pandas as pd

from services.results.config import ResultsServiceConfig, get_default_config
from services.results.parser import ResultsParser
from shared.logging import get_logger
from shared.errors import ResultsFetchError, ResultsParseError
from shared.scraping import Scraper


logger = get_logger("results")


class ResultsFetcher:
    """Fetcher for extracting game results from boxscore pages.

    Uses pandas to extract HTML tables from sports reference sites.

    Attributes:
        config: Results service configuration
        sport: Sport being fetched (nfl, nba)
        parser: Parser for extracting data from tables
        scraper: Scraper instance

    Example:
        fetcher = ResultsFetcher(sport="nfl")
        result = fetcher.fetch_boxscore(url)
    """

    def __init__(
        self,
        sport: str,
        config: Optional[ResultsServiceConfig] = None,
        parser: Optional[ResultsParser] = None,
        scraper: Optional[Scraper] = None,
    ):
        """Initialize the results fetcher.

        Args:
            sport: Sport to fetch (nfl, nba)
            config: Results service configuration
            parser: Parser instance (optional, created if not provided)
            scraper: Scraper instance (optional, created if not provided)
        """
        self.sport = sport.lower()
        self.config = config or get_default_config(self.sport)
        self.parser = parser or ResultsParser()
        self.scraper = scraper or Scraper(self.config.scraper_config)

    def fetch_boxscore(self, boxscore_url: str) -> dict[str, Any]:
        """Fetch and extract game results from a boxscore URL.

        Args:
            boxscore_url: URL to the boxscore page

        Returns:
            Dictionary with game result data:
            {
                "sport": str,
                "game_date": str,
                "teams": {"away": str, "home": str},
                "final_score": {"away": int, "home": int},
                "winner": str,
                "boxscore_url": str,
                "fetched_at": str,
                "tables": {...}
            }

        Raises:
            ResultsFetchError: If fetching fails
            ResultsParseError: If parsing fails
        """
        logger.info(f"Fetching boxscore from {boxscore_url}")

        result_data = self._initialize_result_data(boxscore_url)

        try:
            # Fetch HTML and extract all tables
            html = self.scraper.fetch_html(boxscore_url)
            all_tables = self.scraper.extract_tables(html, extract_comments=True)

            logger.info(f"Found {len(all_tables)} tables on page")

            # Extract configured tables by matching IDs/patterns
            tables_extracted, tables_missing = self._extract_tables_from_list(
                all_tables, html, result_data
            )

            # Split player_offense into passing/rushing/receiving for NFL
            if self.sport == "nfl" and "player_offense" in result_data["tables"]:
                self._split_player_offense(result_data)

            # Parse final score and teams from scoring table
            if "scoring" not in result_data["tables"]:
                raise ResultsParseError(
                    "Critical table 'scoring' not found",
                    context={"url": boxscore_url}
                )

            scoring_data = result_data["tables"]["scoring"]
            final_score = self.parser.parse_final_score(scoring_data)
            teams = self.parser.parse_team_names(scoring_data)
            winner = self.parser.determine_winner(final_score, teams)

            result_data["final_score"] = final_score
            result_data["teams"] = teams
            result_data["winner"] = winner

            logger.info(
                f"Extracted {tables_extracted}/{len(self.config.result_tables)} tables. "
                f"Score: {teams.get('away', 'AWAY')} {final_score['away']} - "
                f"{teams.get('home', 'HOME')} {final_score['home']}"
            )

            if tables_missing:
                logger.warning(f"Missing tables: {', '.join(tables_missing)}")

            return result_data

        except ResultsParseError:
            raise
        except Exception as e:
            raise ResultsFetchError(
                f"Failed to fetch boxscore: {e}",
                context={"url": boxscore_url, "error": str(e)}
            )

    def fetch_boxscore_from_file(self, file_path: str) -> dict[str, Any]:
        """Extract game results from a saved HTML file.

        Useful for testing and offline processing.

        Args:
            file_path: Path to saved HTML file

        Returns:
            Dictionary with game result data

        Raises:
            ResultsFetchError: If file not found
            ResultsParseError: If parsing fails
        """
        import os
        from pathlib import Path

        if not os.path.exists(file_path):
            raise ResultsFetchError(
                f"File not found: {file_path}",
                context={"file_path": file_path}
            )

        result_data = self._initialize_result_data(f"file://{file_path}")

        try:
            html = Path(file_path).read_text(encoding='utf-8')
            all_tables = self.scraper.extract_tables(html, extract_comments=True)

            tables_extracted, tables_missing = self._extract_tables_from_list(
                all_tables, html, result_data
            )

            if self.sport == "nfl" and "player_offense" in result_data["tables"]:
                self._split_player_offense(result_data)

            if "scoring" in result_data["tables"]:
                scoring_data = result_data["tables"]["scoring"]
                result_data["final_score"] = self.parser.parse_final_score(scoring_data)
                result_data["teams"] = self.parser.parse_team_names(scoring_data)
                result_data["winner"] = self.parser.determine_winner(
                    result_data["final_score"],
                    result_data["teams"]
                )

            return result_data

        except ResultsParseError:
            raise
        except Exception as e:
            raise ResultsFetchError(
                f"Failed to parse file: {e}",
                context={"file_path": file_path, "error": str(e)}
            )

    def _initialize_result_data(self, boxscore_url: str) -> dict[str, Any]:
        """Initialize the result data structure."""
        from shared.utils.timezone_utils import get_eastern_now

        return {
            "sport": self.sport,
            "game_date": None,
            "teams": {"away": None, "home": None},
            "final_score": {"away": None, "home": None},
            "winner": None,
            "boxscore_url": boxscore_url,
            "fetched_at": get_eastern_now().strftime("%Y-%m-%d %H:%M:%S"),
            "tables": {}
        }

    def _extract_tables_from_list(
        self,
        all_tables: list[pd.DataFrame],
        html: str,
        result_data: dict[str, Any]
    ) -> tuple[int, list[str]]:
        """Extract configured tables from the list of all tables.

        PFR tables have IDs but pandas.read_html doesn't preserve them.
        We identify tables by their column structure and content.

        Args:
            all_tables: List of all DataFrames from the page
            html: Raw HTML for ID lookup if needed
            result_data: Result data to populate with tables

        Returns:
            Tuple of (tables_extracted_count, list_of_missing_tables)
        """
        import re

        tables_extracted = 0
        tables_missing = []

        # Try to map tables by their ID in HTML
        # PFR format: <table ... id="scoring"> or <table ... id="player_offense">
        for table_name, table_id in self.config.result_tables.items():
            logger.debug(f"Looking for {table_name} (#{table_id})")

            # Find table in HTML by ID and extract its index
            table_pattern = rf'<table[^>]*id="{table_id}"[^>]*>'
            match = re.search(table_pattern, html)

            if match:
                # Count how many tables appear before this one
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

            # Fallback: try to find by column patterns
            table_data = self._find_table_by_columns(all_tables, table_name)
            if table_data:
                result_data["tables"][table_name] = table_data
                tables_extracted += 1
                logger.debug(f"Found {table_name} by column pattern")
            else:
                tables_missing.append(table_name)
                logger.debug(f"Table '{table_id}' not found")

        return tables_extracted, tables_missing

    def _find_table_by_columns(
        self,
        all_tables: list[pd.DataFrame],
        table_name: str
    ) -> Optional[dict[str, Any]]:
        """Try to identify a table by its column structure.

        Args:
            all_tables: List of all DataFrames
            table_name: Name of table to find

        Returns:
            Table data dict or None
        """
        # Column patterns for identifying tables
        column_patterns = {
            "scoring": ["1", "2", "3", "4", "Final"],  # Quarter columns
            "team_stats": ["Away", "Home"] if self.sport == "nfl" else None,
            "player_offense": ["Cmp", "Att", "Yds", "TD"],  # Passing columns
            "defense": ["Sk", "Int", "PD"],  # Defense columns
        }

        pattern = column_patterns.get(table_name)
        if not pattern:
            return None

        for df in all_tables:
            cols = [str(c) for c in df.columns.tolist()]
            if all(p in cols for p in pattern):
                return self._dataframe_to_dict(df, table_name)

        return None

    def _dataframe_to_dict(self, df: pd.DataFrame, table_name: str) -> dict[str, Any]:
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

    def _split_player_offense(self, result_data: dict[str, Any]) -> None:
        """Split player_offense table into passing/rushing/receiving.

        Args:
            result_data: Result data containing player_offense table
        """
        logger.debug("Splitting player_offense into passing/rushing/receiving")

        split_tables = self.parser.split_player_offense(
            result_data["tables"]["player_offense"]
        )

        del result_data["tables"]["player_offense"]

        if split_tables["passing"]:
            result_data["tables"]["passing"] = split_tables["passing"]
            logger.debug(f"Passing: {len(split_tables['passing']['data'])} players")

        if split_tables["rushing"]:
            result_data["tables"]["rushing"] = split_tables["rushing"]
            logger.debug(f"Rushing: {len(split_tables['rushing']['data'])} players")

        if split_tables["receiving"]:
            result_data["tables"]["receiving"] = split_tables["receiving"]
            logger.debug(f"Receiving: {len(split_tables['receiving']['data'])} players")
