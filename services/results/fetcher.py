"""Results fetcher for extracting game data from boxscore pages.

Fetches game results from sports reference sites using web scraping.
"""

from typing import Any, Optional

from services.results.config import ResultsServiceConfig, get_default_config
from services.results.parser import ResultsParser
from shared.logging import get_logger
from shared.errors import ResultsFetchError, ResultsParseError
from shared.scraping import WebScraper


logger = get_logger("results")


class ResultsFetcher:
    """Fetcher for extracting game results from boxscore pages.

    Uses Playwright to navigate to boxscore pages and extract structured
    data from HTML tables.

    Attributes:
        config: Results service configuration
        sport: Sport being fetched (nfl, nba)
        parser: Parser for extracting data from tables
        scraper: Web scraper instance

    Example:
        fetcher = ResultsFetcher(sport="nfl")
        result = fetcher.fetch_boxscore(url)
    """

    def __init__(
        self,
        sport: str,
        config: Optional[ResultsServiceConfig] = None,
        parser: Optional[ResultsParser] = None,
        scraper: Optional[WebScraper] = None,
    ):
        """Initialize the results fetcher.

        Args:
            sport: Sport to fetch (nfl, nba)
            config: Results service configuration
            parser: Parser instance (optional, created if not provided)
            scraper: Web scraper instance (optional, created if not provided)
        """
        self.sport = sport.lower()
        self.config = config or get_default_config(self.sport)
        self.parser = parser or ResultsParser()
        self._scraper = scraper

    @property
    def scraper(self) -> WebScraper:
        """Get or create web scraper instance."""
        if self._scraper is None:
            self._scraper = WebScraper(config=self.config.scraper_config)
        return self._scraper

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

        with self.scraper.launch() as page:
            response = self.scraper.navigate_and_wait(page, boxscore_url)

            self._check_response_status(response, boxscore_url)

            # Extract all configured tables
            tables_extracted, tables_missing = self._extract_tables(page, result_data)

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

        if not os.path.exists(file_path):
            raise ResultsFetchError(
                f"File not found: {file_path}",
                context={"file_path": file_path}
            )

        result_data = self._initialize_result_data(f"file://{file_path}")

        with self.scraper.launch() as page:
            page.goto(f"file://{file_path}")
            page.wait_for_load_state("domcontentloaded")

            tables_extracted, tables_missing = self._extract_tables(page, result_data)

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

    def _initialize_result_data(self, boxscore_url: str) -> dict[str, Any]:
        """Initialize the result data structure.

        Args:
            boxscore_url: URL being fetched

        Returns:
            Initialized result data dictionary
        """
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

    def _check_response_status(self, response: Any, url: str) -> None:
        """Check HTTP response status and raise appropriate errors.

        Args:
            response: Playwright response object
            url: URL that was fetched

        Raises:
            ResultsFetchError: If response indicates an error
        """
        if response is None:
            return

        if response.status == 404:
            raise ResultsFetchError(
                "Game not found (HTTP 404) - may not have been played yet",
                context={"url": url, "status": 404}
            )
        elif response.status == 429:
            raise ResultsFetchError(
                "Rate limited (HTTP 429) - please wait and try again",
                context={"url": url, "status": 429}
            )
        elif response.status != 200:
            raise ResultsFetchError(
                f"HTTP {response.status} error",
                context={"url": url, "status": response.status}
            )

    def _extract_tables(
        self,
        page: Any,
        result_data: dict[str, Any]
    ) -> tuple[int, list[str]]:
        """Extract all configured tables from the page.

        Args:
            page: Playwright page object
            result_data: Result data to populate with tables

        Returns:
            Tuple of (tables_extracted_count, list_of_missing_tables)
        """
        from shared.scraping import TableExtractor

        tables_extracted = 0
        tables_missing = []

        for table_name, table_id in self.config.result_tables.items():
            logger.debug(f"Extracting {table_name} (#{table_id})")

            table_data = TableExtractor.extract(page, table_id)

            if table_data:
                result_data["tables"][table_name] = table_data
                tables_extracted += 1
                logger.debug(f"Extracted {len(table_data.get('data', []))} rows from {table_name}")
            else:
                tables_missing.append(table_name)
                logger.debug(f"Table '{table_id}' not found")

        return tables_extracted, tables_missing

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
