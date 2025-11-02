"""Repository for betting odds data access."""

import os
from typing import List, Optional
from shared.repositories.base_repository import BaseRepository
from shared.config import get_data_path, get_file_path


class OddsRepository(BaseRepository):
    """Repository for managing betting odds data."""

    def __init__(self, sport_code: str):
        """Initialize the odds repository.

        Args:
            sport_code: Sport identifier (e.g., 'nfl', 'nba')
        """
        self.sport_code = sport_code
        base_path = get_data_path(sport_code, "odds")
        super().__init__(base_path)

    def save_odds(
        self,
        game_date: str,
        away_abbr: str,
        home_abbr: str,
        odds_data: dict
    ) -> bool:
        """Save odds data.

        Args:
            game_date: Game date in YYYY-MM-DD format
            away_abbr: Away team abbreviation (lowercase)
            home_abbr: Home team abbreviation (lowercase)
            odds_data: Odds data dictionary

        Returns:
            True if successful, False otherwise
        """
        filepath = get_file_path(
            self.sport_code,
            "odds",
            "prediction_json",
            game_date=game_date,
            team_a_abbr=home_abbr,
            team_b_abbr=away_abbr
        )
        return self.save(filepath, odds_data)

    def load_odds(
        self,
        game_date: str,
        away_abbr: str,
        home_abbr: str
    ) -> Optional[dict]:
        """Load odds data.

        Args:
            game_date: Game date in YYYY-MM-DD format
            away_abbr: Away team abbreviation (lowercase)
            home_abbr: Home team abbreviation (lowercase)

        Returns:
            Odds data dictionary or None
        """
        filepath = get_file_path(
            self.sport_code,
            "odds",
            "prediction_json",
            game_date=game_date,
            team_a_abbr=home_abbr,
            team_b_abbr=away_abbr
        )
        return self.load(filepath)

    def list_odds_for_date(self, game_date: str) -> List[dict]:
        """List all odds for a specific date.

        Args:
            game_date: Game date in YYYY-MM-DD format

        Returns:
            List of odds data dictionaries
        """
        odds_dir = get_data_path(
            self.sport_code,
            "odds",
            game_date=game_date
        )

        if not os.path.exists(odds_dir):
            return []

        odds_list = []
        for filepath in self.list_all_files(odds_dir):
            odds_data = self.load(filepath)
            if odds_data:
                odds_list.append(odds_data)

        return odds_list

    def get_all_odds_dates(self) -> List[str]:
        """Get list of all dates with odds.

        Returns:
            Sorted list of dates in YYYY-MM-DD format (most recent first)
        """
        return sorted(
            self.list_subdirectories(self.base_path),
            reverse=True
        )

    def odds_exist(
        self,
        game_date: str,
        away_abbr: str,
        home_abbr: str
    ) -> bool:
        """Check if odds exist for a game.

        Args:
            game_date: Game date in YYYY-MM-DD format
            away_abbr: Away team abbreviation (lowercase)
            home_abbr: Home team abbreviation (lowercase)

        Returns:
            True if odds exist, False otherwise
        """
        filepath = get_file_path(
            self.sport_code,
            "odds",
            "prediction_json",
            game_date=game_date,
            team_a_abbr=home_abbr,
            team_b_abbr=away_abbr
        )
        return self.exists(filepath)
