"""Repository for game results data access."""

import os
from typing import List, Optional
from shared.repositories.base_repository import BaseRepository
from shared.utils.path_utils import get_data_path, get_file_path


class ResultsRepository(BaseRepository):
    """Repository for managing game results data."""

    def __init__(self, sport_code: str):
        """Initialize the results repository.

        Args:
            sport_code: Sport identifier (e.g., 'nfl', 'nba')
        """
        self.sport_code = sport_code
        base_path = get_data_path(sport_code, "results")
        super().__init__(base_path)

    def load_result(
        self,
        game_date: str,
        away_abbr: str,
        home_abbr: str
    ) -> Optional[dict]:
        """Load game result data.

        Args:
            game_date: Game date in YYYY-MM-DD format
            away_abbr: Away team abbreviation (lowercase)
            home_abbr: Home team abbreviation (lowercase)

        Returns:
            Result data dictionary or None
        """
        filepath = get_file_path(
            self.sport_code,
            "results",
            "result",
            game_date=game_date,
            away_abbr=away_abbr,
            home_abbr=home_abbr
        )
        return self.load(filepath)

    def list_results_for_date(self, game_date: str) -> List[dict]:
        """List all results for a specific date.

        Args:
            game_date: Game date in YYYY-MM-DD format

        Returns:
            List of result data dictionaries
        """
        results_dir = get_data_path(
            self.sport_code,
            "results",
            game_date=game_date
        )

        if not os.path.exists(results_dir):
            return []

        results = []
        for filepath in self.list_all_files(results_dir):
            result_data = self.load(filepath)
            if result_data:
                results.append(result_data)

        return results

    def get_all_result_dates(self) -> List[str]:
        """Get list of all dates with results.

        Returns:
            Sorted list of dates in YYYY-MM-DD format (most recent first)
        """
        return sorted(
            self.list_subdirectories(self.base_path),
            reverse=True
        )
