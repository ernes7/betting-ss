"""Repository for analysis data access."""

import os
from typing import List, Optional
from shared.repositories.base_repository import BaseRepository
from shared.utils.path_utils import get_data_path, get_file_path


class AnalysisRepository(BaseRepository):
    """Repository for managing analysis data."""

    def __init__(self, sport_code: str, analysis_type: str = "analysis"):
        """Initialize the analysis repository.

        Args:
            sport_code: Sport identifier (e.g., 'nfl', 'nba')
            analysis_type: Type of analysis ('analysis' or 'analysis_ev')
        """
        self.sport_code = sport_code
        self.analysis_type = analysis_type
        base_path = get_data_path(sport_code, analysis_type)
        super().__init__(base_path)

    def save_analysis(
        self,
        game_date: str,
        team_a_abbr: str,
        team_b_abbr: str,
        analysis_data: dict
    ) -> bool:
        """Save analysis data.

        Args:
            game_date: Game date in YYYY-MM-DD format
            team_a_abbr: First team abbreviation (lowercase)
            team_b_abbr: Second team abbreviation (lowercase)
            analysis_data: Analysis data dictionary

        Returns:
            True if successful, False otherwise
        """
        filepath = get_file_path(
            self.sport_code,
            self.analysis_type,
            "analysis",
            game_date=game_date,
            team_a_abbr=team_a_abbr,
            team_b_abbr=team_b_abbr
        )
        return self.save(filepath, analysis_data)

    def load_analysis(
        self,
        game_date: str,
        team_a_abbr: str,
        team_b_abbr: str
    ) -> Optional[dict]:
        """Load analysis data.

        Args:
            game_date: Game date in YYYY-MM-DD format
            team_a_abbr: First team abbreviation (lowercase)
            team_b_abbr: Second team abbreviation (lowercase)

        Returns:
            Analysis data dictionary or None
        """
        filepath = get_file_path(
            self.sport_code,
            self.analysis_type,
            "analysis",
            game_date=game_date,
            team_a_abbr=team_a_abbr,
            team_b_abbr=team_b_abbr
        )
        return self.load(filepath)

    def list_analyses_for_date(self, game_date: str) -> List[dict]:
        """List all analyses for a specific date.

        Args:
            game_date: Game date in YYYY-MM-DD format

        Returns:
            List of analysis data dictionaries
        """
        analysis_dir = get_data_path(
            self.sport_code,
            self.analysis_type,
            game_date=game_date
        )

        if not os.path.exists(analysis_dir):
            return []

        analyses = []
        for filepath in self.list_all_files(analysis_dir):
            analysis_data = self.load(filepath)
            if analysis_data:
                analyses.append(analysis_data)

        return analyses

    def get_all_analysis_dates(self) -> List[str]:
        """Get list of all dates with analyses.

        Returns:
            Sorted list of dates in YYYY-MM-DD format (most recent first)
        """
        return sorted(
            self.list_subdirectories(self.base_path),
            reverse=True
        )

    def analysis_exists(
        self,
        game_date: str,
        team_a_abbr: str,
        team_b_abbr: str
    ) -> bool:
        """Check if analysis exists for a game.

        Args:
            game_date: Game date in YYYY-MM-DD format
            team_a_abbr: First team abbreviation (lowercase)
            team_b_abbr: Second team abbreviation (lowercase)

        Returns:
            True if analysis exists, False otherwise
        """
        filepath = get_file_path(
            self.sport_code,
            self.analysis_type,
            "analysis",
            game_date=game_date,
            team_a_abbr=team_a_abbr,
            team_b_abbr=team_b_abbr
        )
        return self.exists(filepath)
