"""Data optimization utilities to reduce token usage in predictions."""


def filter_passing_table(passing_data: dict, limit: int = 2) -> dict:
    """Filter passing table to keep only top N quarterbacks.

    Args:
        passing_data: Full passing table data with headers and data
        limit: Number of top QBs to keep (default: 2)

    Returns:
        Filtered passing table with same structure
    """
    if not passing_data or "data" not in passing_data:
        return passing_data

    # Sort by pass_yds (descending) to get top performers
    sorted_players = sorted(
        passing_data["data"],
        key=lambda x: float(x.get("pass_yds", 0) or 0),
        reverse=True
    )

    return {
        "table_name": passing_data.get("table_name"),
        "headers": passing_data.get("headers"),
        "data": sorted_players[:limit]
    }


def split_rushing_receiving_table(rushing_receiving_data: dict) -> dict:
    """Split rushing/receiving table into separate rushers and receivers lists.

    Args:
        rushing_receiving_data: Combined rushing and receiving table

    Returns:
        Dictionary with "rushers" (top 5 by rush_att) and "receivers" (top 5 by rec)
    """
    if not rushing_receiving_data or "data" not in rushing_receiving_data:
        return {"rushers": None, "receivers": None}

    players = rushing_receiving_data["data"]

    # Get top 5 rushers (sorted by rush attempts)
    rushers = sorted(
        [p for p in players if float(p.get("rush_att", 0) or 0) > 0],
        key=lambda x: float(x.get("rush_att", 0) or 0),
        reverse=True
    )[:5]

    # Get top 5 receivers (sorted by receptions)
    receivers = sorted(
        [p for p in players if float(p.get("rec", 0) or 0) > 0],
        key=lambda x: float(x.get("rec", 0) or 0),
        reverse=True
    )[:5]

    return {
        "rushers": {
            "table_name": "Top Rushers",
            "headers": rushing_receiving_data.get("headers"),
            "data": rushers
        } if rushers else None,
        "receivers": {
            "table_name": "Top Receivers",
            "headers": rushing_receiving_data.get("headers"),
            "data": receivers
        } if receivers else None
    }


def filter_defense_table(defense_data: dict, limit: int = 10) -> dict:
    """Filter defense table to keep only top N defenders by combined tackles.

    Args:
        defense_data: Full defense/fumbles table data
        limit: Number of top defenders to keep (default: 10)

    Returns:
        Filtered defense table with same structure
    """
    if not defense_data or "data" not in defense_data:
        return defense_data

    # Sort by combined tackles (descending)
    # Combined tackles field might be "tackles_combined", "def_tackles_combined", or similar
    def get_tackles(player):
        """Try multiple field names for combined tackles."""
        for field in ["tackles_combined", "def_tackles_combined", "tackles", "comb"]:
            value = player.get(field, 0)
            if value:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    pass
        return 0

    sorted_defenders = sorted(
        defense_data["data"],
        key=get_tackles,
        reverse=True
    )

    return {
        "table_name": defense_data.get("table_name"),
        "headers": defense_data.get("headers"),
        "data": sorted_defenders[:limit]
    }


def optimize_team_profile(profile: dict | None) -> dict | None:
    """Optimize team profile data to reduce token usage.

    Applies all filtering and removes unnecessary tables:
    - Remove scoring_summary (redundant with player stats)
    - Remove touchdown_log (redundant with player stats)
    - Filter passing to top 2 QBs
    - Split rushing_receiving into top 5 rushers + top 5 receivers
    - Filter defense to top 10 by combined tackles
    - Keep schedule_results, team_stats, injury_report as-is

    Args:
        profile: Full team profile dictionary with all tables

    Returns:
        Optimized profile dictionary, or None if input is None
    """
    if not profile:
        return None

    optimized = {}

    # Keep these tables as-is (needed for analysis)
    for table_name in ["schedule_results", "team_stats", "injury_report"]:
        if table_name in profile:
            optimized[table_name] = profile[table_name]

    # Filter passing table
    if "passing" in profile:
        optimized["passing"] = filter_passing_table(profile["passing"], limit=2)

    # Split rushing_receiving into separate tables
    if "rushing_receiving" in profile:
        split_data = split_rushing_receiving_table(profile["rushing_receiving"])
        if split_data["rushers"]:
            optimized["top_rushers"] = split_data["rushers"]
        if split_data["receivers"]:
            optimized["top_receivers"] = split_data["receivers"]

    # Filter defense table
    if "defense_fumbles" in profile:
        optimized["defense_fumbles"] = filter_defense_table(profile["defense_fumbles"], limit=10)

    # Explicitly skip scoring_summary and touchdown_log
    # (do not include them in optimized profile)

    return optimized
