"""Repository for prediction data access."""

from typing import Optional
from shared.repositories.base_repository import BaseRepository
from shared.utils.path_utils import get_data_path, get_file_path


class PredictionRepository(BaseRepository):
    """Repository for managing prediction data."""

    def __init__(self, sport_code: str, prediction_type: str = "predictions"):
        """Initialize the prediction repository.

        Args:
            sport_code: Sport identifier (e.g., 'nfl', 'nba')
            prediction_type: Type of predictions ('predictions' or 'predictions_ev')
        """
        self.sport_code = sport_code
        self.prediction_type = prediction_type
        base_path = get_data_path(sport_code, prediction_type)
        super().__init__(base_path)

    def load_prediction(
        self,
        game_date: str,
        team_a_abbr: str,
        team_b_abbr: str
    ) -> Optional[dict]:
        """Load prediction data with backward compatibility.

        Tries to load with _ai suffix first, falls back to original format.

        Args:
            game_date: Game date in YYYY-MM-DD format
            team_a_abbr: First team abbreviation (lowercase)
            team_b_abbr: Second team abbreviation (lowercase)

        Returns:
            Prediction data dictionary or None
        """
        # Try _ai suffix first (new format)
        filepath_ai = get_file_path(
            self.sport_code,
            self.prediction_type,
            "prediction_ai_json",
            game_date=game_date,
            team_a_abbr=team_a_abbr,
            team_b_abbr=team_b_abbr
        )

        data = self.load(filepath_ai)
        if data:
            return data

        # Fall back to original format (backward compatibility)
        filepath_original = get_file_path(
            self.sport_code,
            self.prediction_type,
            "prediction_json",
            game_date=game_date,
            team_a_abbr=team_a_abbr,
            team_b_abbr=team_b_abbr
        )
        return self.load(filepath_original)
