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
    """Load and group AI/EV prediction JSON files from NFL data directory.

    Groups AI (_ai.json) and EV (_ev.json) predictions for the same game together.
    Also loads comparison data if available.

    Returns:
        List of grouped prediction dictionaries with both systems
    """
    games = {}  # Group by base game_key
    base_dir = Path(__file__).parent.parent.parent  # Go up from streamlit/utils/ to project root

    # Scan NFL predictions
    nfl_dir = base_dir / "nfl" / "data" / "predictions"
    if nfl_dir.exists():
        for json_file in nfl_dir.rglob("*.json"):
            # Skip metadata and comparison files
            if json_file.name in [".metadata.json", ".metadata.archive.json"]:
                continue
            if json_file.name.endswith("_comparison.json"):
                continue

            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Determine game key and prediction type
                file_stem = json_file.stem
                game_date = json_file.parent.name

                # Check if it's AI or EV prediction
                if file_stem.endswith("_ai"):
                    base_key = file_stem[:-3]  # Remove "_ai"
                    pred_type = "ai"
                elif file_stem.endswith("_ev"):
                    base_key = file_stem[:-3]  # Remove "_ev"
                    pred_type = "ev"
                else:
                    # Legacy prediction without suffix - treat as AI
                    base_key = file_stem
                    pred_type = "ai"

                # Create unique game identifier
                game_id = f"{game_date}_{base_key}"

                # Initialize game entry if not exists
                if game_id not in games:
                    games[game_id] = {
                        'game_key': base_key,
                        'game_date': game_date,
                        'ai_prediction': None,
                        'ev_prediction': None,
                        'has_both': False
                    }

                # Add prediction data
                data['file_path'] = str(json_file)
                if pred_type == "ai":
                    games[game_id]['ai_prediction'] = data
                else:
                    games[game_id]['ev_prediction'] = data

            except Exception as e:
                print(f"Error loading {json_file}: {e}")

    # Load comparison files
    for json_file in nfl_dir.rglob("*_comparison.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                comparison_data = json.load(f)

            # Extract base key from comparison filename
            file_stem = json_file.stem[:-11]  # Remove "_comparison"
            game_date = json_file.parent.name
            game_id = f"{game_date}_{file_stem}"

            if game_id in games:
                games[game_id]['comparison'] = comparison_data
        except Exception as e:
            print(f"Error loading comparison {json_file}: {e}")

    # Convert to list and mark games with both predictions
    predictions = []
    for game_id, game_data in games.items():
        game_data['has_both'] = (
            game_data['ai_prediction'] is not None and
            game_data['ev_prediction'] is not None
        )
        predictions.append(game_data)

    return predictions


def load_all_analyses() -> dict:
    """Load all analysis JSON files (P/L data from Claude AI) and create lookup by game key.

    Returns:
        Dictionary mapping game_key to analysis data (including P/L)
    """
    analyses = {}
    base_dir = Path(__file__).parent.parent.parent  # Go up from streamlit/utils/ to project root

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
    """Merge grouped prediction data with dual analysis results (P/L data).

    Args:
        predictions: List of grouped prediction dictionaries (with ai/ev predictions)
        analyses: Dictionary of analyses by game_key (with dual system P/L data)

    Returns:
        List of predictions with analysis data merged
    """
    for pred in predictions:
        game_key = pred.get('game_key')

        # Merge analysis (P/L data from Claude AI - may contain ai_system and/or ev_system)
        if game_key in analyses:
            analysis = analyses[game_key]
            pred['analysis'] = analysis

            # Extract team info and metadata from analysis if not in prediction
            if not pred.get('teams') and analysis.get('teams'):
                pred['teams'] = [
                    analysis['teams'].get('away', ''),
                    analysis['teams'].get('home', '')
                ]
            if not pred.get('final_score'):
                pred['final_score'] = analysis.get('final_score')
        else:
            pred['analysis'] = None

        # Extract team info from predictions if not yet set
        if not pred.get('teams'):
            # Try AI prediction first, then EV
            if pred.get('ai_prediction') and pred['ai_prediction'].get('teams'):
                pred['teams'] = pred['ai_prediction']['teams']
            elif pred.get('ev_prediction') and pred['ev_prediction'].get('teams'):
                pred['teams'] = pred['ev_prediction']['teams']

        # Set generated_at timestamp (use latest from either system)
        generated_times = []
        if pred.get('ai_prediction') and pred['ai_prediction'].get('generated_at'):
            generated_times.append(pred['ai_prediction']['generated_at'])
        if pred.get('ev_prediction') and pred['ev_prediction'].get('generated_at'):
            generated_times.append(pred['ev_prediction']['generated_at'])
        if generated_times:
            pred['generated_at'] = max(generated_times)

    return predictions
