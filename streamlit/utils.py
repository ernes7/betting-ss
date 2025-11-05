"""Utility functions for data loading and processing."""

import json
from pathlib import Path
from datetime import datetime


def format_date(date_str: str) -> str:
    """Convert '2025-10-26' to 'Oct-26' format.

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


def load_all_predictions() -> list[dict]:
    """Load all EV+ singles prediction JSON files from NFL data directory.

    Returns:
        List of prediction dictionaries with file paths
    """
    predictions = []
    base_dir = Path(__file__).parent.parent  # Go up from streamlit/ to project root

    # Scan NFL predictions (EV+ singles only)
    nfl_dir = base_dir / "nfl" / "data" / "predictions"
    if nfl_dir.exists():
        for json_file in nfl_dir.rglob("*.json"):
            # Skip metadata files
            if json_file.name in [".metadata.json", ".metadata.archive.json"]:
                continue
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['file_path'] = str(json_file)
                    data['game_key'] = json_file.stem
                    data['game_date'] = json_file.parent.name
                    predictions.append(data)
            except Exception as e:
                print(f"Error loading {json_file}: {e}")

    return predictions


def load_all_analyses() -> dict:
    """Load all analysis JSON files (P/L data from Claude AI) and create lookup by game key.

    Returns:
        Dictionary mapping game_key to analysis data (including P/L)
    """
    analyses = {}
    base_dir = Path(__file__).parent.parent  # Go up from streamlit/ to project root

    # Scan NFL analyses (EV+ singles only)
    nfl_dir = base_dir / "nfl" / "data" / "analysis"
    if nfl_dir.exists():
        for json_file in nfl_dir.rglob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    game_key = json_file.stem
                    analyses[game_key] = data
            except Exception:
                pass  # Silently skip errors

    return analyses


def merge_predictions_with_analyses(predictions: list[dict], analyses: dict) -> list[dict]:
    """Merge prediction data with analysis results (P/L data).

    Args:
        predictions: List of prediction dictionaries
        analyses: Dictionary of analyses by game_key (with P/L data from Claude AI)

    Returns:
        List of predictions with analysis data merged
    """
    for pred in predictions:
        game_key = pred.get('game_key')

        # Merge analysis (P/L data from Claude AI)
        if game_key in analyses:
            pred['analysis'] = analyses[game_key]
        else:
            pred['analysis'] = None

    return predictions
