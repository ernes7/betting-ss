"""Repository for comparison data between EV calculator and AI predictions."""

import os
from typing import Dict, List, Optional
from shared.repositories.base_repository import BaseRepository
from shared.config import get_data_path, get_file_path


class ComparisonRepository(BaseRepository):
    """Repository for managing comparison data between prediction systems."""

    def __init__(self, sport_code: str):
        """Initialize the comparison repository.

        Args:
            sport_code: Sport identifier (e.g., 'nfl', 'nba')
        """
        self.sport_code = sport_code
        base_path = get_data_path(sport_code, "predictions")  # Same base as predictions
        super().__init__(base_path)

    def save_comparison(
        self,
        game_date: str,
        team_a_abbr: str,
        team_b_abbr: str,
        comparison_data: dict
    ) -> bool:
        """Save comparison data.

        Args:
            game_date: Game date in YYYY-MM-DD format
            team_a_abbr: First team abbreviation (lowercase)
            team_b_abbr: Second team abbreviation (lowercase)
            comparison_data: Comparison data dictionary

        Returns:
            True if successful, False otherwise
        """
        filepath = get_file_path(
            self.sport_code,
            "predictions",
            "prediction_comparison_json",
            game_date=game_date,
            team_a_abbr=team_a_abbr,
            team_b_abbr=team_b_abbr
        )

        return self.save(filepath, comparison_data)

    def load_comparison(
        self,
        game_date: str,
        team_a_abbr: str,
        team_b_abbr: str
    ) -> Optional[dict]:
        """Load comparison data.

        Args:
            game_date: Game date in YYYY-MM-DD format
            team_a_abbr: First team abbreviation (lowercase)
            team_b_abbr: Second team abbreviation (lowercase)

        Returns:
            Comparison data dictionary or None
        """
        filepath = get_file_path(
            self.sport_code,
            "predictions",
            "prediction_comparison_json",
            game_date=game_date,
            team_a_abbr=team_a_abbr,
            team_b_abbr=team_b_abbr
        )
        return self.load(filepath)

    def list_comparisons_for_date(self, game_date: str) -> List[dict]:
        """List all comparisons for a specific date.

        Args:
            game_date: Game date in YYYY-MM-DD format

        Returns:
            List of comparison data dictionaries
        """
        comparisons_dir = get_data_path(
            self.sport_code,
            "predictions",
            game_date=game_date
        )

        if not os.path.exists(comparisons_dir):
            return []

        comparisons = []
        for filename in os.listdir(comparisons_dir):
            # Only load files with _comparison.json suffix
            if filename.endswith("_comparison.json"):
                filepath = os.path.join(comparisons_dir, filename)
                comparison_data = self.load(filepath)
                if comparison_data:
                    comparisons.append(comparison_data)

        return comparisons

    def comparison_exists(
        self,
        game_date: str,
        team_a_abbr: str,
        team_b_abbr: str
    ) -> bool:
        """Check if a comparison exists for a specific game.

        Args:
            game_date: Game date in YYYY-MM-DD format
            team_a_abbr: First team abbreviation (lowercase)
            team_b_abbr: Second team abbreviation (lowercase)

        Returns:
            True if comparison file exists, False otherwise
        """
        filepath = get_file_path(
            self.sport_code,
            "predictions",
            "prediction_comparison_json",
            game_date=game_date,
            team_a_abbr=team_a_abbr,
            team_b_abbr=team_b_abbr
        )
        return os.path.exists(filepath)
