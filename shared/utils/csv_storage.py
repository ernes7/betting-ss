"""CSV storage utilities for standardized data persistence.

This module provides common CSV I/O functions used across services
to ensure consistent data storage patterns.
"""

import json
from pathlib import Path
from typing import Any, Optional, Union

import pandas as pd

from shared.logging import get_logger

logger = get_logger("csv_storage")


def _serialize_value(value: Any) -> Any:
    """Serialize complex values (dicts, lists) to JSON strings for CSV storage."""
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    return value


def _deserialize_value(value: Any) -> Any:
    """Deserialize JSON strings back to dicts/lists."""
    if isinstance(value, str):
        # Try to parse as JSON if it looks like JSON
        if (value.startswith('{') and value.endswith('}')) or \
           (value.startswith('[') and value.endswith(']')):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
    return value


def ensure_directory(path: Path) -> Path:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure exists

    Returns:
        The same path for chaining
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_game_dir(
    base_path: Path,
    game_date: str,
    home_team: str,
    away_team: str,
) -> Path:
    """Build standardized game directory path.

    Args:
        base_path: Base data directory
        game_date: Game date in YYYY-MM-DD format
        home_team: Home team abbreviation
        away_team: Away team abbreviation

    Returns:
        Path to game directory: base_path/game_date/home_away/
    """
    home_team = home_team.lower()
    away_team = away_team.lower()
    return base_path / game_date / f"{home_team}_{away_team}"


def save_csv(
    filepath: Path,
    data: Union[dict, list[dict], pd.DataFrame],
    index: bool = False,
) -> Path:
    """Save data to a CSV file.

    Nested dicts and lists are automatically serialized to JSON strings.

    Args:
        filepath: Full path to save file
        data: Data to save (dict, list of dicts, or DataFrame)
        index: Whether to include index in CSV

    Returns:
        Path to saved file
    """
    ensure_directory(filepath.parent)

    if isinstance(data, pd.DataFrame):
        df = data
    elif isinstance(data, dict):
        # Serialize nested structures to JSON strings
        serialized = {k: _serialize_value(v) for k, v in data.items()}
        df = pd.DataFrame([serialized])
    else:
        # List of dicts
        serialized = [{k: _serialize_value(v) for k, v in row.items()} for row in data]
        df = pd.DataFrame(serialized)

    df.to_csv(filepath, index=index)
    logger.debug(f"Saved CSV to {filepath}")
    return filepath


def load_csv(
    filepath: Path,
    as_dict: bool = False,
) -> Optional[Union[pd.DataFrame, dict, list[dict]]]:
    """Load data from a CSV file.

    JSON strings are automatically deserialized back to dicts/lists.

    Args:
        filepath: Full path to load file
        as_dict: If True, return as dict (single row) or list of dicts (multiple rows)

    Returns:
        DataFrame, dict, list of dicts, or None if file doesn't exist
    """
    if not filepath.exists():
        return None

    df = pd.read_csv(filepath)

    if as_dict:
        if len(df) == 1:
            row = df.iloc[0].to_dict()
            # Deserialize JSON strings back to dicts/lists
            return {k: _deserialize_value(v) for k, v in row.items()}
        records = df.to_dict(orient="records")
        return [{k: _deserialize_value(v) for k, v in row.items()} for row in records]

    return df


def csv_exists(filepath: Path) -> bool:
    """Check if a CSV file exists.

    Args:
        filepath: Full path to check

    Returns:
        True if file exists
    """
    return filepath.exists()


def list_game_dirs(
    base_path: Path,
    game_date: str,
) -> list[Path]:
    """List all game directories for a specific date.

    Args:
        base_path: Base data directory
        game_date: Game date in YYYY-MM-DD format

    Returns:
        List of game directory paths
    """
    date_dir = base_path / game_date

    if not date_dir.exists():
        return []

    return sorted([
        d for d in date_dir.iterdir()
        if d.is_dir()
    ])


def list_dates(base_path: Path) -> list[str]:
    """List all available dates in a data directory.

    Args:
        base_path: Base data directory

    Returns:
        Sorted list of dates (most recent first)
    """
    if not base_path.exists():
        return []

    dates = [
        d.name for d in base_path.iterdir()
        if d.is_dir() and len(d.name.split("-")) == 3
    ]

    return sorted(dates, reverse=True)


def safe_int(value: Any) -> Optional[int]:
    """Safely convert value to int, returning None for NaN/None.

    Args:
        value: Value to convert

    Returns:
        Integer or None
    """
    if pd.isna(value):
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def safe_float(value: Any) -> Optional[float]:
    """Safely convert value to float, returning None for NaN/None.

    Args:
        value: Value to convert

    Returns:
        Float or None
    """
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None
