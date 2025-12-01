"""Results service for fetching and managing game results.

Main entry point for the RESULTS service. Coordinates fetching boxscore
data and saving results.
"""

import json
import os
from typing import Any, Optional

from services.results.config import (
    ResultsServiceConfig,
    get_default_config,
    build_boxscore_url,
)
from services.results.fetcher import ResultsFetcher
from services.results.parser import ResultsParser
from shared.logging import get_logger
from shared.errors import ErrorHandler, create_error_handler, ResultsFetchError


logger = get_logger("results")


class ResultsService:
    """Service for fetching and managing game results.

    Orchestrates the results fetching workflow:
    1. Build boxscore URLs for games
    2. Fetch results from sports reference sites
    3. Save results to JSON files
    4. Track which results have been fetched

    Attributes:
        sport: Sport being processed (nfl, nba)
        config: Results service configuration
        fetcher: Results fetcher instance
        error_handler: Error handler for the service

    Example:
        service = ResultsService(sport="nfl")
        result = service.fetch_game_result(date="20241124", home_abbr="dal")
        service.save_result(result, game_key="2024-11-24_nyg_dal")
    """

    def __init__(
        self,
        sport: str,
        config: Optional[ResultsServiceConfig] = None,
        fetcher: Optional[ResultsFetcher] = None,
        error_handler: Optional[ErrorHandler] = None,
    ):
        """Initialize the results service.

        Args:
            sport: Sport to process (nfl, nba)
            config: Results service configuration
            fetcher: Results fetcher instance (optional)
            error_handler: Error handler (optional)
        """
        self.sport = sport.lower()
        self.config = config or get_default_config(self.sport)
        self.fetcher = fetcher or ResultsFetcher(
            sport=self.sport,
            config=self.config,
        )
        self.error_handler = error_handler or create_error_handler("results")
        self._results_dir = self.config.data_root.format(sport=self.sport)

    @property
    def results_dir(self) -> str:
        """Get the results data directory path."""
        return self._results_dir

    def fetch_game_result(
        self,
        boxscore_url: Optional[str] = None,
        date: Optional[str] = None,
        home_abbr: Optional[str] = None,
        game_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Fetch result for a single game.

        Provide either boxscore_url directly, or the parameters needed
        to build the URL (date + home_abbr for NFL, game_id for NBA).

        Args:
            boxscore_url: Direct URL to boxscore page
            date: Game date in YYYYMMDD format (NFL)
            home_abbr: Home team abbreviation (NFL)
            game_id: Game ID (NBA)

        Returns:
            Dictionary with game result data

        Raises:
            ResultsFetchError: If URL cannot be built or fetch fails
        """
        if boxscore_url is None:
            boxscore_url = self._build_url(date, home_abbr, game_id)

        logger.info(f"Fetching game result from {boxscore_url}")

        try:
            return self.fetcher.fetch_boxscore(boxscore_url)
        except Exception as e:
            self.error_handler.handle(e, context={"url": boxscore_url})

    def fetch_game_result_from_file(self, file_path: str) -> dict[str, Any]:
        """Fetch result from a saved HTML file.

        Useful for testing and offline processing.

        Args:
            file_path: Path to saved HTML file

        Returns:
            Dictionary with game result data
        """
        logger.info(f"Fetching game result from file {file_path}")

        try:
            return self.fetcher.fetch_boxscore_from_file(file_path)
        except Exception as e:
            self.error_handler.handle(e, context={"file_path": file_path})

    def save_result(
        self,
        result_data: dict[str, Any],
        game_key: str,
        game_date: Optional[str] = None,
    ) -> str:
        """Save game result to JSON file.

        Args:
            result_data: Game result dictionary
            game_key: Unique game identifier (e.g., "2024-11-24_nyg_dal")
            game_date: Optional date override (YYYY-MM-DD format)

        Returns:
            Path to saved file
        """
        if game_date is None:
            # Extract date from game_key (e.g., "2024-11-24_nyg_dal" -> "2024-11-24")
            game_date = game_key.split("_")[0]

        # Create results directory structure
        date_dir = os.path.join(self._results_dir, game_date)
        os.makedirs(date_dir, exist_ok=True)

        # Extract filename from game_key
        filename = "_".join(game_key.split("_")[1:]) + ".json"
        filepath = os.path.join(date_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved result to {filepath}")
        return filepath

    def load_result(self, game_key: str, game_date: Optional[str] = None) -> Optional[dict[str, Any]]:
        """Load a saved game result.

        Args:
            game_key: Unique game identifier
            game_date: Optional date override

        Returns:
            Game result dictionary or None if not found
        """
        if game_date is None:
            game_date = game_key.split("_")[0]

        filename = "_".join(game_key.split("_")[1:]) + ".json"
        filepath = os.path.join(self._results_dir, game_date, filename)

        if not os.path.exists(filepath):
            return None

        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_results(self, game_date: str) -> list[str]:
        """List all saved results for a date.

        Args:
            game_date: Date in YYYY-MM-DD format

        Returns:
            List of game keys
        """
        date_dir = os.path.join(self._results_dir, game_date)

        if not os.path.exists(date_dir):
            return []

        results = []
        for filename in os.listdir(date_dir):
            if filename.endswith(".json"):
                # Convert filename back to game_key
                game_key = f"{game_date}_{filename[:-5]}"
                results.append(game_key)

        return results

    def fetch_results_for_date(
        self,
        target_date: str,
        games: list[dict[str, str]],
    ) -> dict[str, Any]:
        """Fetch results for multiple games on a date.

        Args:
            target_date: Date in YYYY-MM-DD format
            games: List of game info dicts with keys needed to build URLs:
                   NFL: {"home_abbr": "dal", "away_abbr": "nyg"}
                   NBA: {"game_id": "202411240DAL"}

        Returns:
            Summary dictionary:
            {
                "fetched_count": int,
                "failed_count": int,
                "skipped_count": int,
                "results": [...],
                "errors": [...]
            }
        """
        summary = {
            "fetched_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "results": [],
            "errors": [],
        }

        date_formatted = target_date.replace("-", "")

        for game in games:
            try:
                # Build URL based on sport
                if self.sport == "nfl":
                    url = build_boxscore_url(
                        self.sport,
                        date=date_formatted,
                        home_abbr=game["home_abbr"].lower(),
                    )
                    game_key = f"{target_date}_{game.get('away_abbr', 'away').lower()}_{game['home_abbr'].lower()}"
                else:
                    url = build_boxscore_url(
                        self.sport,
                        game_id=game["game_id"],
                    )
                    game_key = f"{target_date}_{game['game_id']}"

                # Check if already fetched
                existing = self.load_result(game_key)
                if existing:
                    logger.info(f"Skipping {game_key} - already fetched")
                    summary["skipped_count"] += 1
                    continue

                # Fetch and save
                result = self.fetcher.fetch_boxscore(url)
                self.save_result(result, game_key, target_date)

                summary["fetched_count"] += 1
                summary["results"].append({
                    "game_key": game_key,
                    "winner": result.get("winner"),
                    "final_score": result.get("final_score"),
                })

            except Exception as e:
                summary["failed_count"] += 1
                summary["errors"].append({
                    "game": game,
                    "error": str(e),
                })
                logger.error(f"Failed to fetch game: {e}")

        logger.info(
            f"Fetch complete: {summary['fetched_count']} fetched, "
            f"{summary['failed_count']} failed, {summary['skipped_count']} skipped"
        )

        return summary

    def _build_url(
        self,
        date: Optional[str],
        home_abbr: Optional[str],
        game_id: Optional[str],
    ) -> str:
        """Build boxscore URL from parameters.

        Args:
            date: Game date (NFL)
            home_abbr: Home team abbreviation (NFL)
            game_id: Game ID (NBA)

        Returns:
            Formatted boxscore URL

        Raises:
            ResultsFetchError: If required parameters missing
        """
        if self.sport == "nfl":
            if not date or not home_abbr:
                raise ResultsFetchError(
                    "NFL boxscore URL requires date and home_abbr",
                    context={"date": date, "home_abbr": home_abbr}
                )
            return build_boxscore_url(self.sport, date=date, home_abbr=home_abbr.lower())

        elif self.sport == "nba":
            if not game_id:
                raise ResultsFetchError(
                    "NBA boxscore URL requires game_id",
                    context={"game_id": game_id}
                )
            return build_boxscore_url(self.sport, game_id=game_id)

        else:
            raise ResultsFetchError(
                f"Unknown sport: {self.sport}",
                context={"sport": self.sport}
            )
