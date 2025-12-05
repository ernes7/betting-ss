"""NFL Data Cleaner.

Cleans and filters data fetched from PFR and DraftKings.

Rules:
- Rankings: Convert ranks to int, percentages to float, normalize team names
- Profiles: Top 3 receivers, top 2 running backs, remove bench players
- Odds: Filter to -150 to +150 range, remove exotic props
"""

from typing import Any, Dict, List, Optional
import pandas as pd

from sports.nfl.tables import (
    RANKINGS_TABLES,
    DEFENSE_TABLES,
    PROFILE_TABLES,
)
from sports.nfl.teams import TEAM_ABBR_MAP, PFR_ABBR_TO_NAME
from shared.logging import get_logger

logger = get_logger("nfl_cleaner")


# Cleaning configuration
MAX_RECEIVERS = 3
MAX_RUNNING_BACKS = 2
MIN_ODDS = -150
MAX_ODDS = 150


def clean_rankings(rankings_data: Dict[str, Any]) -> Dict[str, Any]:
    """Clean rankings data.

    Applies column mappings, converts types, and normalizes team names.

    Args:
        rankings_data: Raw rankings data from StatsFetcher

    Returns:
        Cleaned rankings data
    """
    if "tables" not in rankings_data:
        return rankings_data

    cleaned = rankings_data.copy()
    cleaned["tables"] = {}

    for table_name, table_data in rankings_data["tables"].items():
        if not table_data or "data" not in table_data:
            continue

        # Get column mapping for this table
        table_config = RANKINGS_TABLES.get(table_name) or DEFENSE_TABLES.get(table_name)
        if not table_config:
            cleaned["tables"][table_name] = table_data
            continue

        column_map = table_config.get("columns", {})
        df = pd.DataFrame(table_data["data"])

        # Apply column mapping
        df = _apply_column_mapping(df, column_map)

        # Convert types
        df = _convert_ranking_types(df)

        # Normalize team names
        if "team" in df.columns:
            df["team"] = df["team"].apply(_normalize_team_name)

        # Remove aggregate rows (like "Avg Team" or "League Average")
        if "team" in df.columns:
            df = df[~df["team"].str.contains("Avg|Average|Total", case=False, na=False)]

        cleaned["tables"][table_name] = {
            "table_name": table_name,
            "columns": df.columns.tolist(),
            "data": df.to_dict(orient="records")
        }

    logger.info(f"Cleaned {len(cleaned['tables'])} ranking tables")
    return cleaned


def clean_profile(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """Clean team profile data.

    Filters to top players by position and removes irrelevant data.

    Args:
        profile_data: Raw profile data from StatsFetcher

    Returns:
        Cleaned profile data with top players only
    """
    if "tables" not in profile_data:
        return profile_data

    cleaned = profile_data.copy()
    cleaned["tables"] = {}

    for table_name, table_data in profile_data["tables"].items():
        if not table_data or "data" not in table_data:
            continue

        # Get column mapping for this table
        table_config = PROFILE_TABLES.get(table_name)
        if not table_config:
            cleaned["tables"][table_name] = table_data
            continue

        column_map = table_config.get("columns", {})
        df = pd.DataFrame(table_data["data"])

        # Apply column mapping
        df = _apply_column_mapping(df, column_map)

        # Filter by position for rushing_receiving table
        if table_name == "rushing_receiving":
            df = _filter_top_players(df)

        # Remove empty rows
        if "player" in df.columns:
            df = df[df["player"].notna() & (df["player"] != "")]

        cleaned["tables"][table_name] = {
            "table_name": table_name,
            "columns": df.columns.tolist(),
            "data": df.to_dict(orient="records")
        }

    logger.info(f"Cleaned {len(cleaned['tables'])} profile tables")
    return cleaned


def clean_odds(odds_data: Dict[str, Any]) -> Dict[str, Any]:
    """Clean odds data.

    Filters to standard odds range and removes exotic props.

    Args:
        odds_data: Raw odds data from OddsService

    Returns:
        Cleaned odds data with filtered props
    """
    cleaned = odds_data.copy()

    # Filter player props
    if "player_props" in cleaned:
        cleaned["player_props"] = _filter_player_props(cleaned["player_props"])

    logger.info(f"Cleaned odds data for {cleaned.get('teams', {}).get('home', {}).get('name', 'Unknown')}")
    return cleaned


def _apply_column_mapping(df: pd.DataFrame, column_map: Dict[str, str]) -> pd.DataFrame:
    """Apply column name mapping to DataFrame.

    Args:
        df: DataFrame to transform
        column_map: Mapping from raw column names to clean names

    Returns:
        DataFrame with renamed columns
    """
    # Build rename dict for columns that exist
    rename_dict = {
        col: clean_name
        for col, clean_name in column_map.items()
        if col in df.columns
    }

    if rename_dict:
        df = df.rename(columns=rename_dict)

    return df


def _convert_ranking_types(df: pd.DataFrame) -> pd.DataFrame:
    """Convert ranking DataFrame column types.

    Args:
        df: DataFrame to convert

    Returns:
        DataFrame with converted types
    """
    # Rank columns -> int
    rank_cols = [col for col in df.columns if col == "rank" or col.endswith("_rank")]
    for col in rank_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # Percentage columns -> float
    pct_cols = [col for col in df.columns if "pct" in col.lower() or col.endswith("%")]
    for col in pct_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Integer columns
    int_cols = ["games", "attempts", "completions", "yards", "touchdowns",
                "interceptions", "fumbles", "sacks", "first_downs"]
    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    return df


def _normalize_team_name(name: str) -> str:
    """Normalize team name to standard format.

    Args:
        name: Raw team name

    Returns:
        Normalized team name
    """
    if not name or not isinstance(name, str):
        return name

    # Remove common suffixes
    clean_name = name.strip()

    # Check if it's a PFR abbreviation
    if clean_name.lower() in PFR_ABBR_TO_NAME:
        return PFR_ABBR_TO_NAME[clean_name.lower()]

    # Check if it's a standard abbreviation
    if clean_name.upper() in TEAM_ABBR_MAP:
        return TEAM_ABBR_MAP[clean_name.upper()]

    return clean_name


def _filter_top_players(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to top players by position.

    Args:
        df: DataFrame with player data

    Returns:
        Filtered DataFrame with top receivers and running backs
    """
    if "position" not in df.columns:
        return df

    # Identify receivers (WR, TE)
    receivers = df[df["position"].isin(["WR", "TE"])]
    if "rec_yards" in df.columns:
        receivers = receivers.sort_values("rec_yards", ascending=False).head(MAX_RECEIVERS)
    elif "targets" in df.columns:
        receivers = receivers.sort_values("targets", ascending=False).head(MAX_RECEIVERS)
    else:
        receivers = receivers.head(MAX_RECEIVERS)

    # Identify running backs (RB, FB)
    running_backs = df[df["position"].isin(["RB", "FB"])]
    if "rush_yards" in df.columns:
        running_backs = running_backs.sort_values("rush_yards", ascending=False).head(MAX_RUNNING_BACKS)
    elif "rush_attempts" in df.columns:
        running_backs = running_backs.sort_values("rush_attempts", ascending=False).head(MAX_RUNNING_BACKS)
    else:
        running_backs = running_backs.head(MAX_RUNNING_BACKS)

    # Keep quarterbacks (QB)
    quarterbacks = df[df["position"] == "QB"]

    # Combine all
    result = pd.concat([quarterbacks, running_backs, receivers], ignore_index=True)

    logger.debug(f"Filtered to {len(result)} players: {len(quarterbacks)} QB, {len(running_backs)} RB, {len(receivers)} WR/TE")

    return result


def _filter_player_props(props: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter player props to standard odds range.

    Args:
        props: List of player prop dictionaries

    Returns:
        Filtered props within odds range
    """
    filtered_props = []

    for player_prop in props:
        filtered_player_props = []

        for prop in player_prop.get("props", []):
            # Filter milestones by odds range
            if "milestones" in prop:
                filtered_milestones = [
                    m for m in prop["milestones"]
                    if MIN_ODDS <= m.get("odds", 0) <= MAX_ODDS
                ]
                if filtered_milestones:
                    filtered_prop = prop.copy()
                    filtered_prop["milestones"] = filtered_milestones
                    filtered_player_props.append(filtered_prop)

            # Filter over/under by odds range
            elif "over" in prop or "under" in prop:
                over_odds = prop.get("over", 0)
                under_odds = prop.get("under", 0)
                if MIN_ODDS <= over_odds <= MAX_ODDS or MIN_ODDS <= under_odds <= MAX_ODDS:
                    filtered_player_props.append(prop)

        if filtered_player_props:
            filtered_player = player_prop.copy()
            filtered_player["props"] = filtered_player_props
            filtered_props.append(filtered_player)

    logger.debug(f"Filtered to {len(filtered_props)} players with props in range [{MIN_ODDS}, {MAX_ODDS}]")

    return filtered_props


def clean_all_data(
    rankings_data: Optional[Dict[str, Any]] = None,
    defensive_data: Optional[Dict[str, Any]] = None,
    profile_data: Optional[Dict[str, Any]] = None,
    odds_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Clean all data types at once.

    Args:
        rankings_data: Raw rankings data
        defensive_data: Raw defensive stats data
        profile_data: Raw profile data
        odds_data: Raw odds data

    Returns:
        Dictionary with all cleaned data
    """
    result = {}

    if rankings_data:
        result["rankings"] = clean_rankings(rankings_data)

    if defensive_data:
        result["defensive"] = clean_rankings(defensive_data)  # Same cleaning logic

    if profile_data:
        result["profile"] = clean_profile(profile_data)

    if odds_data:
        result["odds"] = clean_odds(odds_data)

    return result
