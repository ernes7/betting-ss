"""
Bundesliga FBRef Table Configurations

This module defines all table configurations for FBRef scraping:
- Column mappings (raw column names -> clean names)
- Table IDs for each URL

Usage:
    from sports.futbol.bundesliga.tables import RANKINGS_TABLES, PROFILE_TABLES

    # Get column mapping for a table
    columns = RANKINGS_TABLES["standings"]["columns"]
"""

# =============================================================================
# COLUMN MAPPINGS - RANKINGS PAGE
# =============================================================================

STANDINGS_COLUMNS = {
    "Rk": "rank",
    "Squad": "squad",
    "MP": "matches_played",
    "W": "wins",
    "D": "draws",
    "L": "losses",
    "GF": "goals_for",
    "GA": "goals_against",
    "GD": "goal_diff",
    "Pts": "points",
    "Pts/MP": "points_per_match",
    "xG": "xg",
    "xGA": "xga",
    "xGD": "xg_diff",
    "xGD/90": "xg_diff_per90",
    "Last 5": "last_5",
    "Attendance": "attendance",
    "Top Team Scorer": "top_scorer",
    "Goalkeeper": "goalkeeper",
    "Notes": "notes",
}

# Multi-level columns for home/away standings
STANDINGS_HOME_AWAY_COLUMNS = {
    ("Unnamed: 0_level_0", "Rk"): "rank",
    ("Unnamed: 1_level_0", "Squad"): "squad",
    # Home stats
    ("Home", "MP"): "home_matches_played",
    ("Home", "W"): "home_wins",
    ("Home", "D"): "home_draws",
    ("Home", "L"): "home_losses",
    ("Home", "GF"): "home_goals_for",
    ("Home", "GA"): "home_goals_against",
    ("Home", "GD"): "home_goal_diff",
    ("Home", "Pts"): "home_points",
    ("Home", "Pts/MP"): "home_points_per_match",
    ("Home", "xG"): "home_xg",
    ("Home", "xGA"): "home_xga",
    ("Home", "xGD"): "home_xg_diff",
    ("Home", "xGD/90"): "home_xg_diff_per90",
    # Away stats
    ("Away", "MP"): "away_matches_played",
    ("Away", "W"): "away_wins",
    ("Away", "D"): "away_draws",
    ("Away", "L"): "away_losses",
    ("Away", "GF"): "away_goals_for",
    ("Away", "GA"): "away_goals_against",
    ("Away", "GD"): "away_goal_diff",
    ("Away", "Pts"): "away_points",
    ("Away", "Pts/MP"): "away_points_per_match",
    ("Away", "xG"): "away_xg",
    ("Away", "xGA"): "away_xga",
    ("Away", "xGD"): "away_xg_diff",
    ("Away", "xGD/90"): "away_xg_diff_per90",
}

# Multi-level columns: "Group | Column" -> "clean_name"
SQUAD_STANDARD_COLUMNS = {
    # Basic info
    ("Unnamed: 0_level_0", "Squad"): "squad",
    ("Unnamed: 1_level_0", "# Pl"): "num_players",
    ("Unnamed: 2_level_0", "Age"): "avg_age",
    ("Unnamed: 3_level_0", "Poss"): "possession",
    # Playing Time
    ("Playing Time", "MP"): "matches_played",
    ("Playing Time", "Starts"): "starts",
    ("Playing Time", "Min"): "minutes",
    ("Playing Time", "90s"): "minutes_90s",
    # Performance
    ("Performance", "Gls"): "goals",
    ("Performance", "Ast"): "assists",
    ("Performance", "G+A"): "goals_assists",
    ("Performance", "G-PK"): "goals_minus_pk",
    ("Performance", "PK"): "pk_goals",
    ("Performance", "PKatt"): "pk_attempts",
    ("Performance", "CrdY"): "yellow_cards",
    ("Performance", "CrdR"): "red_cards",
    # Expected
    ("Expected", "xG"): "xg",
    ("Expected", "npxG"): "npxg",
    ("Expected", "xAG"): "xag",
    ("Expected", "npxG+xAG"): "npxg_xag",
    # Progression
    ("Progression", "PrgC"): "progressive_carries",
    ("Progression", "PrgP"): "progressive_passes",
    # Per 90 Minutes
    ("Per 90 Minutes", "Gls"): "goals_per90",
    ("Per 90 Minutes", "Ast"): "assists_per90",
    ("Per 90 Minutes", "G+A"): "goals_assists_per90",
    ("Per 90 Minutes", "G-PK"): "goals_minus_pk_per90",
    ("Per 90 Minutes", "G+A-PK"): "goals_assists_minus_pk_per90",
    ("Per 90 Minutes", "xG"): "xg_per90",
    ("Per 90 Minutes", "xAG"): "xag_per90",
    ("Per 90 Minutes", "xG+xAG"): "xg_xag_per90",
    ("Per 90 Minutes", "npxG"): "npxg_per90",
    ("Per 90 Minutes", "npxG+xAG"): "npxg_xag_per90",
}

SQUAD_SHOOTING_COLUMNS = {
    ("Unnamed: 0_level_0", "Squad"): "squad",
    ("Unnamed: 1_level_0", "# Pl"): "num_players",
    ("Unnamed: 2_level_0", "90s"): "minutes_90s",
    # Standard
    ("Standard", "Gls"): "goals",
    ("Standard", "Sh"): "shots",
    ("Standard", "SoT"): "shots_on_target",
    ("Standard", "SoT%"): "shots_on_target_pct",
    ("Standard", "Sh/90"): "shots_per90",
    ("Standard", "SoT/90"): "shots_on_target_per90",
    ("Standard", "G/Sh"): "goals_per_shot",
    ("Standard", "G/SoT"): "goals_per_shot_on_target",
    ("Standard", "Dist"): "avg_shot_distance",
    ("Standard", "FK"): "free_kick_shots",
    ("Standard", "PK"): "pk_goals",
    ("Standard", "PKatt"): "pk_attempts",
    # Expected
    ("Expected", "xG"): "xg",
    ("Expected", "npxG"): "npxg",
    ("Expected", "npxG/Sh"): "npxg_per_shot",
    ("Expected", "G-xG"): "goals_minus_xg",
    ("Expected", "np:G-xG"): "np_goals_minus_xg",
}

SQUAD_PASSING_COLUMNS = {
    ("Unnamed: 0_level_0", "Squad"): "squad",
    ("Unnamed: 1_level_0", "# Pl"): "num_players",
    ("Unnamed: 2_level_0", "90s"): "minutes_90s",
    # Total
    ("Total", "Cmp"): "passes_completed",
    ("Total", "Att"): "passes_attempted",
    ("Total", "Cmp%"): "pass_completion_pct",
    ("Total", "TotDist"): "total_pass_distance",
    ("Total", "PrgDist"): "progressive_pass_distance",
    # Short
    ("Short", "Cmp"): "short_passes_completed",
    ("Short", "Att"): "short_passes_attempted",
    ("Short", "Cmp%"): "short_pass_completion_pct",
    # Medium
    ("Medium", "Cmp"): "medium_passes_completed",
    ("Medium", "Att"): "medium_passes_attempted",
    ("Medium", "Cmp%"): "medium_pass_completion_pct",
    # Long
    ("Long", "Cmp"): "long_passes_completed",
    ("Long", "Att"): "long_passes_attempted",
    ("Long", "Cmp%"): "long_pass_completion_pct",
    # Other
    ("Unnamed: 17_level_0", "Ast"): "assists",
    ("Unnamed: 18_level_0", "xAG"): "xag",
    ("Expected", "xA"): "xa",
    ("Expected", "A-xAG"): "assists_minus_xag",
    ("Unnamed: 21_level_0", "KP"): "key_passes",
    ("Unnamed: 22_level_0", "1/3"): "passes_into_final_third",
    ("Unnamed: 23_level_0", "PPA"): "passes_into_penalty_area",
    ("Unnamed: 24_level_0", "CrsPA"): "crosses_into_penalty_area",
    ("Unnamed: 25_level_0", "PrgP"): "progressive_passes",
}

SQUAD_GCA_COLUMNS = {
    ("Unnamed: 0_level_0", "Squad"): "squad",
    ("Unnamed: 1_level_0", "# Pl"): "num_players",
    ("Unnamed: 2_level_0", "90s"): "minutes_90s",
    # SCA (Shot Creating Actions)
    ("SCA", "SCA"): "sca",
    ("SCA", "SCA90"): "sca_per90",
    # SCA Types
    ("SCA Types", "PassLive"): "sca_pass_live",
    ("SCA Types", "PassDead"): "sca_pass_dead",
    ("SCA Types", "TO"): "sca_take_on",
    ("SCA Types", "Sh"): "sca_shot",
    ("SCA Types", "Fld"): "sca_fouled",
    ("SCA Types", "Def"): "sca_defensive",
    # GCA (Goal Creating Actions)
    ("GCA", "GCA"): "gca",
    ("GCA", "GCA90"): "gca_per90",
    # GCA Types
    ("GCA Types", "PassLive"): "gca_pass_live",
    ("GCA Types", "PassDead"): "gca_pass_dead",
    ("GCA Types", "TO"): "gca_take_on",
    ("GCA Types", "Sh"): "gca_shot",
    ("GCA Types", "Fld"): "gca_fouled",
    ("GCA Types", "Def"): "gca_defensive",
}

SQUAD_DEFENSE_COLUMNS = {
    ("Unnamed: 0_level_0", "Squad"): "squad",
    ("Unnamed: 1_level_0", "# Pl"): "num_players",
    ("Unnamed: 2_level_0", "90s"): "minutes_90s",
    # Tackles
    ("Tackles", "Tkl"): "tackles",
    ("Tackles", "TklW"): "tackles_won",
    ("Tackles", "Def 3rd"): "tackles_def_third",
    ("Tackles", "Mid 3rd"): "tackles_mid_third",
    ("Tackles", "Att 3rd"): "tackles_att_third",
    # Challenges
    ("Challenges", "Tkl"): "dribblers_tackled",
    ("Challenges", "Att"): "dribbler_challenges",
    ("Challenges", "Tkl%"): "dribbler_tackle_pct",
    ("Challenges", "Lost"): "challenges_lost",
    # Blocks
    ("Blocks", "Blocks"): "blocks",
    ("Blocks", "Sh"): "shots_blocked",
    ("Blocks", "Pass"): "passes_blocked",
    # Other
    ("Unnamed: 15_level_0", "Int"): "interceptions",
    ("Unnamed: 16_level_0", "Tkl+Int"): "tackles_interceptions",
    ("Unnamed: 17_level_0", "Clr"): "clearances",
    ("Unnamed: 18_level_0", "Err"): "errors",
}

# =============================================================================
# COLUMN MAPPINGS - PROFILE PAGE (Team)
# =============================================================================

FIXTURES_COLUMNS = {
    "Date": "date",
    "Time": "time",
    "Comp": "competition",
    "Round": "round",
    "Day": "day",
    "Venue": "venue",
    "Result": "result",
    "GF": "goals_for",
    "GA": "goals_against",
    "Opponent": "opponent",
    "xG": "xg",
    "xGA": "xga",
    "Poss": "possession",
    "Attendance": "attendance",
    "Captain": "captain",
    "Formation": "formation",
    "Opp Formation": "opp_formation",
    "Referee": "referee",
    "Match Report": "match_report",
    "Notes": "notes",
}

PLAYER_STANDARD_COLUMNS = {
    ("Unnamed: 0_level_0", "Player"): "player",
    ("Unnamed: 1_level_0", "Nation"): "nation",
    ("Unnamed: 2_level_0", "Pos"): "position",
    ("Unnamed: 3_level_0", "Age"): "age",
    # Playing Time
    ("Playing Time", "MP"): "matches_played",
    ("Playing Time", "Starts"): "starts",
    ("Playing Time", "Min"): "minutes",
    ("Playing Time", "90s"): "minutes_90s",
    # Performance
    ("Performance", "Gls"): "goals",
    ("Performance", "Ast"): "assists",
    ("Performance", "G+A"): "goals_assists",
    ("Performance", "G-PK"): "goals_minus_pk",
    ("Performance", "PK"): "pk_goals",
    ("Performance", "PKatt"): "pk_attempts",
    ("Performance", "CrdY"): "yellow_cards",
    ("Performance", "CrdR"): "red_cards",
    # Expected
    ("Expected", "xG"): "xg",
    ("Expected", "npxG"): "npxg",
    ("Expected", "xAG"): "xag",
    ("Expected", "npxG+xAG"): "npxg_xag",
    # Progression
    ("Progression", "PrgC"): "progressive_carries",
    ("Progression", "PrgP"): "progressive_passes",
    ("Progression", "PrgR"): "progressive_receptions",
    # Per 90 Minutes
    ("Per 90 Minutes", "Gls"): "goals_per90",
    ("Per 90 Minutes", "Ast"): "assists_per90",
    ("Per 90 Minutes", "G+A"): "goals_assists_per90",
    ("Per 90 Minutes", "G-PK"): "goals_minus_pk_per90",
    ("Per 90 Minutes", "G+A-PK"): "goals_assists_minus_pk_per90",
    ("Per 90 Minutes", "xG"): "xg_per90",
    ("Per 90 Minutes", "xAG"): "xag_per90",
    ("Per 90 Minutes", "xG+xAG"): "xg_xag_per90",
    ("Per 90 Minutes", "npxG"): "npxg_per90",
    ("Per 90 Minutes", "npxG+xAG"): "npxg_xag_per90",
    ("Unnamed: 33_level_0", "Matches"): "matches",
}

PLAYER_SHOOTING_COLUMNS = {
    ("Unnamed: 0_level_0", "Player"): "player",
    ("Unnamed: 1_level_0", "Nation"): "nation",
    ("Unnamed: 2_level_0", "Pos"): "position",
    ("Unnamed: 3_level_0", "Age"): "age",
    ("Unnamed: 4_level_0", "90s"): "minutes_90s",
    # Standard
    ("Standard", "Gls"): "goals",
    ("Standard", "Sh"): "shots",
    ("Standard", "SoT"): "shots_on_target",
    ("Standard", "SoT%"): "shots_on_target_pct",
    ("Standard", "Sh/90"): "shots_per90",
    ("Standard", "SoT/90"): "shots_on_target_per90",
    ("Standard", "G/Sh"): "goals_per_shot",
    ("Standard", "G/SoT"): "goals_per_shot_on_target",
    ("Standard", "Dist"): "avg_shot_distance",
    ("Standard", "FK"): "free_kick_shots",
    ("Standard", "PK"): "pk_goals",
    ("Standard", "PKatt"): "pk_attempts",
    # Expected
    ("Expected", "xG"): "xg",
    ("Expected", "npxG"): "npxg",
    ("Expected", "npxG/Sh"): "npxg_per_shot",
    ("Expected", "G-xG"): "goals_minus_xg",
    ("Expected", "np:G-xG"): "np_goals_minus_xg",
    ("Unnamed: 22_level_0", "Matches"): "matches",
}

# =============================================================================
# TABLE CONFIGURATIONS
# =============================================================================

# Rankings page: /en/comps/20/Bundesliga-Stats
RANKINGS_TABLES = {
    "standings": {
        "id": "results2025-2026201_overall",
        "columns": STANDINGS_COLUMNS,
    },
    "standings_home_away": {
        "id": "results2025-2026201_home_away",
        "columns": STANDINGS_HOME_AWAY_COLUMNS,
        "multi_level_header": True,
    },
    "squad_standard": {
        "id": "stats_squads_standard_for",
        "columns": SQUAD_STANDARD_COLUMNS,
        "multi_level_header": True,
    },
    "squad_standard_against": {
        "id": "stats_squads_standard_against",
        "columns": SQUAD_STANDARD_COLUMNS,
        "multi_level_header": True,
    },
    "squad_shooting": {
        "id": "stats_squads_shooting_for",
        "columns": SQUAD_SHOOTING_COLUMNS,
        "multi_level_header": True,
    },
    "squad_shooting_against": {
        "id": "stats_squads_shooting_against",
        "columns": SQUAD_SHOOTING_COLUMNS,
        "multi_level_header": True,
    },
    "squad_passing": {
        "id": "stats_squads_passing_for",
        "columns": SQUAD_PASSING_COLUMNS,
        "multi_level_header": True,
    },
    "squad_passing_against": {
        "id": "stats_squads_passing_against",
        "columns": SQUAD_PASSING_COLUMNS,
        "multi_level_header": True,
    },
    "squad_gca": {
        "id": "stats_squads_gca_for",
        "columns": SQUAD_GCA_COLUMNS,
        "multi_level_header": True,
    },
    "squad_gca_against": {
        "id": "stats_squads_gca_against",
        "columns": SQUAD_GCA_COLUMNS,
        "multi_level_header": True,
    },
    "squad_defense": {
        "id": "stats_squads_defense_for",
        "columns": SQUAD_DEFENSE_COLUMNS,
        "multi_level_header": True,
    },
    "squad_defense_against": {
        "id": "stats_squads_defense_against",
        "columns": SQUAD_DEFENSE_COLUMNS,
        "multi_level_header": True,
    },
}

# Team profile page: /en/squads/{fbref_id}/{slug}
PROFILE_TABLES = {
    "fixtures": {
        "id": "matchlogs_for",
        "columns": FIXTURES_COLUMNS,
    },
    "player_standard": {
        "id": "stats_standard_20",
        "columns": PLAYER_STANDARD_COLUMNS,
        "multi_level_header": True,
    },
    "player_shooting": {
        "id": "stats_shooting_20",
        "columns": PLAYER_SHOOTING_COLUMNS,
        "multi_level_header": True,
    },
}

# =============================================================================
# URLs
# =============================================================================

BASE_URL = "https://fbref.com"
RANKINGS_URL = f"{BASE_URL}/en/comps/20/Bundesliga-Stats"


def get_team_url(fbref_id: str, slug: str) -> str:
    """Get team profile URL for a given FBRef ID and slug."""
    return f"{BASE_URL}/en/squads/{fbref_id}/{slug}"


# =============================================================================
# ALL TABLE IDS (for reference)
# =============================================================================

# Rankings page tables (25 total):
ALL_RANKINGS_TABLE_IDS = [
    "nations",
    "results2025-2026201_home_away",
    "results2025-2026201_overall",
    "stats_squads_defense_against",
    "stats_squads_defense_for",
    "stats_squads_gca_against",
    "stats_squads_gca_for",
    "stats_squads_keeper_adv_against",
    "stats_squads_keeper_adv_for",
    "stats_squads_keeper_against",
    "stats_squads_keeper_for",
    "stats_squads_misc_against",
    "stats_squads_misc_for",
    "stats_squads_passing_against",
    "stats_squads_passing_for",
    "stats_squads_passing_types_against",
    "stats_squads_passing_types_for",
    "stats_squads_playing_time_against",
    "stats_squads_playing_time_for",
    "stats_squads_possession_against",
    "stats_squads_possession_for",
    "stats_squads_shooting_against",
    "stats_squads_shooting_for",
    "stats_squads_standard_against",
    "stats_squads_standard_for",
]

# Profile page tables (14 total):
ALL_PROFILE_TABLE_IDS = [
    "matchlogs_for",
    "results2025-2026201_home_away",
    "results2025-2026201_overall",
    "stats_defense_20",
    "stats_gca_20",
    "stats_keeper_20",
    "stats_keeper_adv_20",
    "stats_misc_20",
    "stats_passing_20",
    "stats_passing_types_20",
    "stats_playing_time_20",
    "stats_possession_20",
    "stats_shooting_20",
    "stats_standard_20",
]
