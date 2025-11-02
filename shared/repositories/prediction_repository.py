"""Repository for prediction data access."""

import os
from typing import Dict, List, Optional
from shared.repositories.base_repository import BaseRepository
from shared.config import get_data_path, get_file_path


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

    def save_prediction(
        self,
        game_date: str,
        team_a_abbr: str,
        team_b_abbr: str,
        prediction_data: dict,
        file_format: str = "json"
    ) -> bool:
        """Save prediction data.

        Args:
            game_date: Game date in YYYY-MM-DD format
            team_a_abbr: First team abbreviation (lowercase)
            team_b_abbr: Second team abbreviation (lowercase)
            prediction_data: Prediction data dictionary
            file_format: File format ('json' or 'md')

        Returns:
            True if successful, False otherwise
        """
        file_type = "prediction_json" if file_format == "json" else "prediction"
        filepath = get_file_path(
            self.sport_code,
            self.prediction_type,
            file_type,
            game_date=game_date,
            team_a_abbr=team_a_abbr,
            team_b_abbr=team_b_abbr
        )

        if file_format == "json":
            return self.save(filepath, prediction_data)
        else:
            # For markdown files, prediction_data should be a string
            try:
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(prediction_data)
                return True
            except Exception as e:
                print(f"Error saving markdown file {filepath}: {str(e)}")
                return False

    def load_prediction(
        self,
        game_date: str,
        team_a_abbr: str,
        team_b_abbr: str
    ) -> Optional[dict]:
        """Load prediction data.

        Args:
            game_date: Game date in YYYY-MM-DD format
            team_a_abbr: First team abbreviation (lowercase)
            team_b_abbr: Second team abbreviation (lowercase)

        Returns:
            Prediction data dictionary or None
        """
        filepath = get_file_path(
            self.sport_code,
            self.prediction_type,
            "prediction_json",
            game_date=game_date,
            team_a_abbr=team_a_abbr,
            team_b_abbr=team_b_abbr
        )
        return self.load(filepath)

    def list_predictions_for_date(self, game_date: str) -> List[dict]:
        """List all predictions for a specific date.

        Args:
            game_date: Game date in YYYY-MM-DD format

        Returns:
            List of prediction data dictionaries
        """
        predictions_dir = get_data_path(
            self.sport_code,
            self.prediction_type,
            game_date=game_date
        )

        if not os.path.exists(predictions_dir):
            return []

        predictions = []
        for filepath in self.list_all_files(predictions_dir):
            prediction_data = self.load(filepath)
            if prediction_data:
                predictions.append(prediction_data)

        return predictions

    def get_all_prediction_dates(self) -> List[str]:
        """Get list of all dates with predictions.

        Returns:
            Sorted list of dates in YYYY-MM-DD format (most recent first)
        """
        return sorted(
            self.list_subdirectories(self.base_path),
            reverse=True
        )

    def get_latest_prediction(self) -> Optional[dict]:
        """Get the most recent prediction.

        Returns:
            Latest prediction data dictionary or None
        """
        dates = self.get_all_prediction_dates()
        if not dates:
            return None

        # Get predictions from most recent date
        latest_predictions = self.list_predictions_for_date(dates[0])
        return latest_predictions[0] if latest_predictions else None
