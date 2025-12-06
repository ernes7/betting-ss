"""Path utilities for data storage across sports.

This module provides centralized path management using templates
that can be dynamically populated based on sport and data type.
"""

import os
from typing import Optional


# Base data directory structure
DATA_DIR_TEMPLATE = "{sport}/data"

# Data subdirectory templates
PATH_TEMPLATES = {
    # Core data directories
    "rankings": "{sport}/data/rankings",
    "profiles": "{sport}/data/profiles",
    "odds": "{sport}/data/odds",
    "results": "{sport}/data/results",

    # Prediction directories
    "predictions": "{sport}/data/predictions",
    "predictions_ev": "{sport}/data/predictions_ev",

    # Analysis directories
    "analysis": "{sport}/data/analysis",
    "analysis_ev": "{sport}/data/analysis_ev",

    # Metadata files
    "profiles_metadata": "{sport}/data/profiles/.metadata.json",
    "predictions_metadata": "{sport}/data/predictions/.metadata.json",
    "predictions_ev_metadata": "{sport}/data/predictions_ev/.metadata.json",
    "odds_metadata": "{sport}/data/odds/.metadata.json",
    "results_metadata": "{sport}/data/results/.metadata.json",
    "analysis_metadata": "{sport}/data/analysis/.metadata.json",
    "analysis_ev_metadata": "{sport}/data/analysis_ev/.metadata.json",
}

# File naming templates
FILE_TEMPLATES = {
    # Original templates (backward compatibility)
    "prediction": "{team_a_abbr}_{team_b_abbr}.md",
    "prediction_json": "{team_a_abbr}_{team_b_abbr}.json",

    # Dual system templates with suffixes
    "prediction_ai": "{team_a_abbr}_{team_b_abbr}_ai.md",
    "prediction_ai_json": "{team_a_abbr}_{team_b_abbr}_ai.json",
    "prediction_ev": "{team_a_abbr}_{team_b_abbr}_ev.md",
    "prediction_ev_json": "{team_a_abbr}_{team_b_abbr}_ev.json",
    "prediction_comparison_json": "{team_a_abbr}_{team_b_abbr}_comparison.json",

    # Other templates
    "result": "{away_abbr}_at_{home_abbr}.json",
    "odds": "{away_abbr}_at_{home_abbr}.json",
    "analysis": "{team_a_abbr}_{team_b_abbr}.json",
}


def get_data_path(sport: str, data_type: str, **kwargs) -> str:
    """Get the full path for a specific data type.

    Args:
        sport: Sport identifier (e.g., 'nfl', 'nba')
        data_type: Type of data (e.g., 'rankings', 'predictions', 'profiles')
        **kwargs: Additional template variables (e.g., game_date for subdirectories)

    Returns:
        Full path string

    Examples:
        >>> get_data_path('nfl', 'rankings')
        'nfl/data/rankings'
        >>> get_data_path('nfl', 'predictions', game_date='2025-10-26')
        'nfl/data/predictions/2025-10-26'
    """
    if data_type not in PATH_TEMPLATES:
        raise ValueError(f"Unknown data type: {data_type}. Valid types: {list(PATH_TEMPLATES.keys())}")

    template = PATH_TEMPLATES[data_type]
    path = template.format(sport=sport, **kwargs)

    # Add game_date subdirectory if provided and it's a predictions/results/analysis/odds path
    if "game_date" in kwargs and data_type in ["predictions", "predictions_ev", "odds", "results", "analysis", "analysis_ev"]:
        path = os.path.join(path, kwargs["game_date"])

    return path


def get_file_path(sport: str, data_type: str, file_type: str, **kwargs) -> str:
    """Get the full file path including filename.

    Args:
        sport: Sport identifier (e.g., 'nfl', 'nba')
        data_type: Type of data (e.g., 'predictions', 'results')
        file_type: Type of file (e.g., 'prediction', 'result', 'odds')
        **kwargs: Template variables (game_date, team abbreviations, etc.)

    Returns:
        Full file path string

    Examples:
        >>> get_file_path('nfl', 'predictions', 'prediction_json',
        ...               game_date='2025-10-26', team_a_abbr='mia', team_b_abbr='buf')
        'nfl/data/predictions/2025-10-26/mia_buf.json'
    """
    # Get directory path
    dir_path = get_data_path(sport, data_type, **kwargs)

    # Get filename
    if file_type not in FILE_TEMPLATES:
        raise ValueError(f"Unknown file type: {file_type}. Valid types: {list(FILE_TEMPLATES.keys())}")

    filename_template = FILE_TEMPLATES[file_type]
    filename = filename_template.format(**kwargs)

    return os.path.join(dir_path, filename)


def ensure_directory(path: str) -> None:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to create
    """
    os.makedirs(path, exist_ok=True)


def ensure_parent_directory(file_path: str) -> None:
    """Ensure the parent directory of a file path exists.

    Args:
        file_path: File path whose parent directory should be created
    """
    parent_dir = os.path.dirname(file_path)
    if parent_dir:
        ensure_directory(parent_dir)


def get_metadata_path(sport: str, data_type: str) -> str:
    """Get the metadata file path for a specific data type.

    Args:
        sport: Sport identifier (e.g., 'nfl', 'nba')
        data_type: Type of data (e.g., 'profiles', 'predictions', 'predictions_ev')

    Returns:
        Metadata file path

    Examples:
        >>> get_metadata_path('nfl', 'profiles')
        'nfl/data/profiles/.metadata.json'
    """
    metadata_type = f"{data_type}_metadata"
    if metadata_type not in PATH_TEMPLATES:
        raise ValueError(f"Unknown metadata type: {metadata_type}")

    return PATH_TEMPLATES[metadata_type].format(sport=sport)
