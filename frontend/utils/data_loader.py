"""Data loading utilities for the Streamlit dashboard.

Provides functions and classes for loading predictions and analyses
from the file system. Supports both legacy JSON format and new CSV format.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from frontend.config import DataPathConfig, StreamlitServiceConfig
from shared.utils.csv_storage import load_csv


def format_date(date_str: str) -> str:
    """Convert 'YYYY-MM-DD' to 'Mon-DD' format.

    Args:
        date_str: Date string in YYYY-MM-DD format

    Returns:
        Formatted date string like 'Oct-26'
    """
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%b-%d")
    except Exception:
        return date_str


class DataLoader:
    """Loads prediction and analysis data from the file system.

    This class provides methods for loading, grouping, and merging
    prediction and analysis data for display in the dashboard.

    Attributes:
        config: Service configuration
        base_dir: Base directory for data files
    """

    def __init__(
        self,
        config: Optional[StreamlitServiceConfig] = None,
        base_dir: Optional[Path] = None,
    ):
        """Initialize DataLoader.

        Args:
            config: Service configuration (uses default if not provided)
            base_dir: Base directory for data files (uses project root if not provided)
        """
        self.config = config or StreamlitServiceConfig()
        self.base_dir = base_dir or Path(__file__).parent.parent.parent.parent

    def load_predictions(self, sport: str = "nfl") -> List[Dict]:
        """Load and group AI/EV prediction files.

        Supports both new CSV format (in game directories) and legacy JSON format.
        Groups AI and EV predictions for the same game together.

        Args:
            sport: Sport code ('nfl' or 'nba')

        Returns:
            List of grouped prediction dictionaries with both systems
        """
        games = {}
        pred_dir = self.config.paths.get_predictions_dir(sport, self.base_dir)

        if not pred_dir.exists():
            return []

        # Load new CSV format: predictions/{date}/{teams}/prediction_{type}.csv
        for csv_file in pred_dir.rglob("prediction_*.csv"):
            try:
                data = load_csv(csv_file, as_dict=True)
                if data is None:
                    continue

                file_stem = csv_file.stem  # e.g., "prediction_ev"
                game_dir = csv_file.parent  # e.g., predictions/2024-11-24/nyg_dal
                teams = game_dir.name  # e.g., "nyg_dal"
                game_date = game_dir.parent.name  # e.g., "2024-11-24"

                # Determine prediction type from filename
                if file_stem == "prediction_ai" or file_stem.endswith("_ai"):
                    pred_type = "ai"
                elif file_stem == "prediction_ev" or file_stem.endswith("_ev"):
                    pred_type = "ev"
                elif file_stem == "prediction_dual" or file_stem.endswith("_dual"):
                    pred_type = "dual"
                else:
                    pred_type = "ev"  # Default

                game_id = f"{game_date}_{teams}"

                if game_id not in games:
                    games[game_id] = {
                        'game_key': teams,
                        'game_date': game_date,
                        'ai_prediction': None,
                        'ev_prediction': None,
                        'dual_prediction': None,
                        'has_both': False,
                        'sport': sport,
                    }

                data['file_path'] = str(csv_file)
                if pred_type == "ai":
                    games[game_id]['ai_prediction'] = data
                elif pred_type == "ev":
                    games[game_id]['ev_prediction'] = data
                elif pred_type == "dual":
                    games[game_id]['dual_prediction'] = data

            except Exception as e:
                print(f"Error loading {csv_file}: {e}")

        # Load legacy JSON format for backward compatibility
        for json_file in pred_dir.rglob("*.json"):
            # Skip metadata and comparison files
            if json_file.name in [".metadata.json", ".metadata.archive.json"]:
                continue
            if json_file.name.endswith("_comparison.json"):
                continue

            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                file_stem = json_file.stem
                game_date = json_file.parent.name

                # Determine prediction type
                if file_stem.endswith("_ai"):
                    base_key = file_stem[:-3]
                    pred_type = "ai"
                elif file_stem.endswith("_ev"):
                    base_key = file_stem[:-3]
                    pred_type = "ev"
                else:
                    base_key = file_stem
                    pred_type = "ai"  # Legacy format

                game_id = f"{game_date}_{base_key}"

                # Only add if not already loaded from CSV
                if game_id not in games:
                    games[game_id] = {
                        'game_key': base_key,
                        'game_date': game_date,
                        'ai_prediction': None,
                        'ev_prediction': None,
                        'has_both': False,
                        'sport': sport,
                    }

                # Only set if not already loaded from CSV
                data['file_path'] = str(json_file)
                if pred_type == "ai" and games[game_id]['ai_prediction'] is None:
                    games[game_id]['ai_prediction'] = data
                elif pred_type == "ev" and games[game_id]['ev_prediction'] is None:
                    games[game_id]['ev_prediction'] = data

            except Exception as e:
                print(f"Error loading {json_file}: {e}")

        # Load comparison files (JSON only for now)
        for json_file in pred_dir.rglob("*_comparison.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    comparison_data = json.load(f)

                file_stem = json_file.stem[:-11]  # Remove "_comparison"
                game_date = json_file.parent.name
                game_id = f"{game_date}_{file_stem}"

                if game_id in games:
                    games[game_id]['comparison'] = comparison_data
            except Exception:
                pass

        # Convert to list
        predictions = []
        for game_data in games.values():
            game_data['has_both'] = (
                game_data['ai_prediction'] is not None and
                game_data['ev_prediction'] is not None
            )
            predictions.append(game_data)

        return predictions

    def load_analyses(self, sport: str = "nfl") -> Dict[str, Dict]:
        """Load all analysis files.

        Args:
            sport: Sport code ('nfl' or 'nba')

        Returns:
            Dictionary mapping game_key to analysis data
        """
        analyses = {}
        analysis_dir = self.config.paths.get_analysis_dir(sport, self.base_dir)

        if not analysis_dir.exists():
            return analyses

        for json_file in analysis_dir.rglob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    game_key = json_file.stem
                    analyses[game_key] = data
            except Exception:
                pass

        return analyses

    def merge_predictions_analyses(
        self,
        predictions: List[Dict],
        analyses: Dict[str, Dict],
    ) -> List[Dict]:
        """Merge prediction data with analysis results.

        Args:
            predictions: List of prediction dictionaries
            analyses: Dictionary of analyses by game_key

        Returns:
            List of predictions with analysis data merged
        """
        for pred in predictions:
            game_key = pred.get('game_key')

            if game_key in analyses:
                analysis = analyses[game_key]
                pred['analysis'] = analysis

                # Extract team info from analysis
                if not pred.get('teams') and analysis.get('teams'):
                    pred['teams'] = [
                        analysis['teams'].get('away', ''),
                        analysis['teams'].get('home', '')
                    ]
                if not pred.get('final_score'):
                    pred['final_score'] = analysis.get('final_score')
            else:
                pred['analysis'] = None

            # Extract team info from predictions
            if not pred.get('teams'):
                if pred.get('ai_prediction') and pred['ai_prediction'].get('teams'):
                    pred['teams'] = pred['ai_prediction']['teams']
                elif pred.get('ev_prediction') and pred['ev_prediction'].get('teams'):
                    pred['teams'] = pred['ev_prediction']['teams']

            # Set generated_at timestamp
            generated_times = []
            if pred.get('ai_prediction') and pred['ai_prediction'].get('generated_at'):
                generated_times.append(pred['ai_prediction']['generated_at'])
            if pred.get('ev_prediction') and pred['ev_prediction'].get('generated_at'):
                generated_times.append(pred['ev_prediction']['generated_at'])
            if generated_times:
                pred['generated_at'] = max(generated_times)

        return predictions

    def load_all_data(self, sport: str = "nfl") -> List[Dict]:
        """Load predictions and merge with analyses.

        Args:
            sport: Sport code ('nfl' or 'nba')

        Returns:
            List of predictions with analysis data merged
        """
        predictions = self.load_predictions(sport)
        analyses = self.load_analyses(sport)
        return self.merge_predictions_analyses(predictions, analyses)


# Module-level functions for backward compatibility
_default_loader = None


def _get_loader() -> DataLoader:
    """Get or create default data loader."""
    global _default_loader
    if _default_loader is None:
        _default_loader = DataLoader()
    return _default_loader


def load_all_predictions(sport: str = "nfl") -> List[Dict]:
    """Load all predictions for a sport.

    Args:
        sport: Sport code ('nfl' or 'nba')

    Returns:
        List of grouped prediction dictionaries
    """
    return _get_loader().load_predictions(sport)


def load_all_analyses(sport: str = "nfl") -> Dict[str, Dict]:
    """Load all analyses for a sport.

    Args:
        sport: Sport code ('nfl' or 'nba')

    Returns:
        Dictionary mapping game_key to analysis data
    """
    return _get_loader().load_analyses(sport)


def merge_predictions_with_analyses(
    predictions: List[Dict],
    analyses: Dict[str, Dict],
) -> List[Dict]:
    """Merge predictions with analyses.

    Args:
        predictions: List of prediction dictionaries
        analyses: Dictionary of analyses by game_key

    Returns:
        List of predictions with analysis data merged
    """
    return _get_loader().merge_predictions_analyses(predictions, analyses)
