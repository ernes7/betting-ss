"""Repository for EV calculator results data access."""

from typing import Optional
from shared.repositories.base_repository import BaseRepository
from shared.utils.path_utils import get_data_path, get_file_path


class EVResultsRepository(BaseRepository):
    """Repository for managing EV calculator results."""

    def __init__(self, sport_code: str):
        """Initialize the EV results repository.

        Args:
            sport_code: Sport identifier (e.g., 'nfl', 'nba')
        """
        self.sport_code = sport_code
        base_path = get_data_path(sport_code, "predictions")
        super().__init__(base_path)

    def load_ev_results(
        self,
        game_date: str,
        team_a_abbr: str,
        team_b_abbr: str
    ) -> Optional[dict]:
        """Load EV calculator results.

        Args:
            game_date: Game date in YYYY-MM-DD format
            team_a_abbr: First team abbreviation (lowercase)
            team_b_abbr: Second team abbreviation (lowercase)

        Returns:
            EV results data dictionary or None
        """
        filepath = get_file_path(
            self.sport_code,
            "predictions",
            "prediction_ev_json",
            game_date=game_date,
            team_a_abbr=team_a_abbr,
            team_b_abbr=team_b_abbr
        )
        return self.load(filepath)
