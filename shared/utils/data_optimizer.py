"""Data optimization utilities to reduce token usage in predictions."""


def split_player_offense_result(player_offense_data: dict) -> dict:
    """Split combined player_offense table from boxscore into passing, rushing, and receiving.

    This is for RESULT data (boxscore pages), not team profiles.
    On Pro-Football-Reference boxscores, offensive stats are in one table.
    We extract the ENTIRE table (no filtering) and split by player role.

    Args:
        player_offense_data: Combined offensive player stats table from boxscore

    Returns:
        Dictionary with "passing", "rushing", and "receiving" tables
    """
    if not player_offense_data or "data" not in player_offense_data:
        return {"passing": None, "rushing": None, "receiving": None}

    players = player_offense_data["data"]
    headers = player_offense_data.get("headers", [])

    # Separate players by role based on their stats (no filtering, keep all)
    passers = [p for p in players if float(p.get("pass_att", 0) or 0) > 0]
    rushers = [p for p in players if float(p.get("rush_att", 0) or 0) > 0]
    receivers = [p for p in players if float(p.get("rec", 0) or 0) > 0]

    return {
        "passing": {
            "table_name": "Passing Stats",
            "headers": headers,
            "data": passers
        } if passers else None,
        "rushing": {
            "table_name": "Rushing Stats",
            "headers": headers,
            "data": rushers
        } if rushers else None,
        "receiving": {
            "table_name": "Receiving Stats",
            "headers": headers,
            "data": receivers
        } if receivers else None
    }


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


# Stats where LOWER values are BETTER (rank 1 should be lowest)
LOWER_IS_BETTER = {
    # Turnovers & mistakes
    "turnovers", "to", "int", "interceptions", "fumbles", "fum", "fum_lost",
    # Defense allowed stats
    "sacks_allowed", "sacked", "qb_hits_allowed", "pressures_allowed",
    "points_allowed", "pts_allowed", "pa", "opp_pts",
    "yards_allowed", "yds_allowed", "ya", "opp_yds",
    "pass_yards_allowed", "pass_yds_allowed", "opp_pass_yds",
    "rush_yards_allowed", "rush_yds_allowed", "opp_rush_yds",
    "first_downs_allowed", "opp_first_downs",
    # Penalties
    "penalties", "pen", "penalty_yards", "pen_yds",
    # Time of possession (lower = worse for offense, but context matters)
    # Excluded as it's situational
    # Negative efficiency metrics
    "sack_rate", "int_rate", "fumble_rate",
    # Opponent scoring
    "touchdowns_allowed", "td_allowed", "opp_td",
}


def optimize_rankings(rankings: dict, team_a: str, team_b: str) -> dict:
    """Optimize rankings data to reduce token usage while preserving context.

    Extracts only the 2 relevant teams from each ranking table and adds
    rank annotations ({field}_rank, {field}_percentile) for league context.

    This reduces a 32-team table from ~1400 tokens to ~100 tokens while
    preserving information like "3rd best in rushing" via percentile scores.

    Args:
        rankings: Full rankings dictionary with all teams
        team_a: First team name to extract
        team_b: Second team name to extract

    Returns:
        Optimized rankings dictionary with only 2 teams + rank annotations
    """
    if not rankings:
        return rankings

    optimized = {}

    for table_name, table_content in rankings.items():
        if not table_content or "data" not in table_content:
            continue

        # Get all teams for rank calculation
        all_teams = table_content["data"]
        if not all_teams:
            continue

        # Find the 2 relevant teams
        team_a_data = None
        team_b_data = None

        for team in all_teams:
            team_name = team.get("team", "")
            if team_name.lower() == team_a.lower():
                team_a_data = team.copy()
            elif team_name.lower() == team_b.lower():
                team_b_data = team.copy()

        # Skip this table if we didn't find both teams
        if not team_a_data or not team_b_data:
            continue

        # Calculate ranks for each numeric field
        headers = table_content.get("headers", [])

        for field in headers:
            if field == "team":
                continue

            # Extract all values for this field (filter out None/empty)
            values = []
            for team in all_teams:
                try:
                    value = team.get(field)
                    if value is not None and value != "":
                        numeric_value = float(value)
                        values.append((numeric_value, team.get("team")))
                except (ValueError, TypeError):
                    pass

            if len(values) < 2:
                continue

            # Determine if lower is better for this stat
            field_normalized = field.lower().replace("_", "")
            is_reverse_stat = any(
                reverse_field.replace("_", "") in field_normalized
                for reverse_field in LOWER_IS_BETTER
            )

            # Sort: ascending if lower is better, descending if higher is better
            if is_reverse_stat:
                values_sorted = sorted(values, key=lambda x: x[0])  # Ascending
            else:
                values_sorted = sorted(values, key=lambda x: x[0], reverse=True)  # Descending

            # Build rank lookup (rank 1 = best)
            rank_lookup = {}
            for rank, (value, team_name) in enumerate(values_sorted, start=1):
                rank_lookup[team_name] = rank

            # Calculate total teams for percentile
            total_teams = len(values_sorted)

            # Add rank and percentile to our 2 teams
            for team_data in [team_a_data, team_b_data]:
                team_name = team_data.get("team")
                if team_name in rank_lookup:
                    rank = rank_lookup[team_name]
                    # Percentile: rank 1 = 100%, rank 32 = 3.1% (for 32 teams)
                    percentile = round(((total_teams - rank + 1) / total_teams) * 100, 1)

                    team_data[f"{field}_rank"] = rank
                    team_data[f"{field}_percentile"] = percentile

        # Update headers to include rank/percentile fields
        updated_headers = headers.copy()
        for field in headers:
            if field != "team":
                if f"{field}_rank" not in updated_headers:
                    updated_headers.append(f"{field}_rank")
                if f"{field}_percentile" not in updated_headers:
                    updated_headers.append(f"{field}_percentile")

        # Store optimized table with only 2 teams
        optimized[table_name] = {
            "table_name": table_content.get("table_name"),
            "headers": updated_headers,
            "data": [team_a_data, team_b_data]
        }

    return optimized
