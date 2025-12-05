"""
NFL Pro-Football-Reference Table Configurations

This module defines all table configurations for PFR scraping:
- Column mappings (raw column names -> clean names)
- Table indices for each URL
- Header fixes for misaligned tables

Usage:
    from sports.nfl.tables import RANKINGS_TABLES, PROFILE_TABLES

    # Get column mapping for a table
    columns = RANKINGS_TABLES["team_offense"]["columns"]

    # Check if table needs header fix
    if RANKINGS_TABLES["passing_offense"].get("needs_header_fix"):
        # Apply header fix
"""

# =============================================================================
# COLUMN MAPPINGS
# =============================================================================

TEAM_STATS_COLUMNS = {
    "Rk": "rank",
    "Tm": "team",
    "G": "games",
    "PF": "points_for",
    "PA": "points_against",
    "Yds": "total_yards",
    "Ply": "total_plays",
    "Y/P": "yards_per_play",
    "TO": "turnovers",
    "FL": "fumbles_lost",
    "1stD": "first_downs_total",
    "Cmp": "pass_completions",
    "Att": "pass_attempts",
    "Yds.1": "pass_yards",
    "TD": "pass_td",
    "Int": "interceptions",
    "NY/A": "net_yards_per_pass_att",
    "1stD.1": "first_downs_pass",
    "Att.1": "rush_attempts",
    "Yds.2": "rush_yards",
    "TD.1": "rush_td",
    "Y/A": "rush_yards_per_att",
    "1stD.2": "first_downs_rush",
    "Pen": "penalties",
    "Yds.3": "penalty_yards",
    "1stPy": "first_downs_penalty",
    "Sc%": "scoring_pct",
    "TO%": "turnover_pct",
    "EXP": "expected_points",
}

PASSING_COLUMNS = {
    "Rk": "rank",
    "Tm": "team",
    "G": "games",
    "Cmp": "completions",
    "Att": "attempts",
    "Cmp%": "completion_pct",
    "Yds": "pass_yards",
    "TD": "pass_td",
    "TD%": "td_pct",
    "Int": "interceptions",
    "Int%": "int_pct",
    "1D": "first_downs",
    "Y/A": "yards_per_att",
    "AY/A": "adj_yards_per_att",
    "Y/C": "yards_per_comp",
    "Y/G": "yards_per_game",
    "Rate": "passer_rating",
    "Sk": "sacks",
    "Yds.1": "sack_yards_lost",
    "Sk%": "sack_pct",
    "NY/A": "net_yards_per_att",
    "ANY/A": "adj_net_yards_per_att",
    "4QC": "fourth_qtr_comebacks",
    "GWD": "game_winning_drives",
    "EXP": "expected_points",
}

RUSHING_COLUMNS = {
    "Rk": "rank",
    "Tm": "team",
    "G": "games",
    "Att": "rush_attempts",
    "Yds": "rush_yards",
    "TD": "rush_td",
    "Lng": "longest_rush",
    "Y/A": "yards_per_att",
    "Y/G": "yards_per_game",
    "Fmb": "fumbles",
    "EXP": "expected_points",
}

SCORING_COLUMNS = {
    "Rk": "rank",
    "Tm": "team",
    "G": "games",
    "RshTD": "rush_td",
    "RecTD": "rec_td",
    "PRTD": "punt_return_td",
    "KRTD": "kick_return_td",
    "FRTD": "fumble_return_td",
    "IntTD": "int_return_td",
    "OthTD": "other_td",
    "AllTD": "total_td",
    "2PM": "two_pt_made",
    "2PA": "two_pt_att",
    "D2P": "def_two_pt",
    "XPM": "extra_points_made",
    "XPA": "extra_points_att",
    "FGM": "field_goals_made",
    "FGA": "field_goals_att",
    "Sfty": "safeties",
    "Pts": "total_points",
    "Pts/G": "points_per_game",
}

ADVANCED_DEFENSE_COLUMNS = {
    "Tm": "team",
    "G": "games",
    "Att": "pass_att_against",
    "Cmp": "completions_against",
    "Yds": "pass_yards_against",
    "TD": "pass_td_against",
    "TD%": "pass_td_pct",
    "YAC": "yards_after_catch",
    "YAC/Cmp": "yac_per_comp",
    "Drops": "drops",
    "Drop%": "drop_pct",
    "BadTh": "bad_throws",
    "Bad%": "bad_throw_pct",
    "Bltz": "blitzes",
    "Bltz%": "blitz_pct",
    "Hrry": "hurries",
    "Prss": "pressures",
    "Prss%": "pressure_pct",
    "MTkl": "missed_tackles",
}

SCHEDULE_COLUMNS = {
    "Week": "week",
    "Day": "day",
    "Date": "date",
    "Unnamed: 3": "time",
    "Unnamed: 4": "boxscore_link",
    "Unnamed: 5": "result",
    "OT": "overtime",
    "Rec": "record",
    "Unnamed: 8": "home_away",
    "Opp": "opponent",
    "Tm": "team_score",
    "Opp.1": "opp_score",
    "1stD": "team_first_downs",
    "TotYd": "team_total_yards",
    "PassY": "team_pass_yards",
    "RushY": "team_rush_yards",
    "TO": "team_turnovers",
    "1stD.1": "opp_first_downs",
    "TotYd.1": "opp_total_yards",
    "PassY.1": "opp_pass_yards",
    "RushY.1": "opp_rush_yards",
    "TO.1": "opp_turnovers",
    "Offense": "off_epa",
    "Defense": "def_epa",
    "Sp. Tms": "special_teams_epa",
}

PROFILE_PASSING_COLUMNS = {
    "Rk": "rank",
    "Player": "player",
    "Age": "age",
    "Pos": "position",
    "G": "games",
    "GS": "games_started",
    "QBrec": "qb_record",
    "Cmp": "completions",
    "Att": "attempts",
    "Cmp%": "completion_pct",
    "Yds": "pass_yards",
    "TD": "pass_td",
    "TD%": "td_pct",
    "Int": "interceptions",
    "Int%": "int_pct",
    "1D": "first_downs",
    "Succ%": "success_pct",
    "Lng": "longest_pass",
    "Y/A": "yards_per_att",
    "AY/A": "adj_yards_per_att",
    "Y/C": "yards_per_comp",
    "Y/G": "yards_per_game",
    "Rate": "passer_rating",
    "QBR": "qbr",
    "Sk": "sacks",
    "Yds.1": "sack_yards_lost",
    "NY/A": "net_yards_per_att",
    "ANY/A": "adj_net_yards_per_att",
    "Sk%": "sack_pct",
    "4QC": "fourth_qtr_comebacks",
    "GWD": "game_winning_drives",
    "Awards": "awards",
}

RUSHING_RECEIVING_COLUMNS = {
    "Rk": "rank",
    "Player": "player",
    "Age": "age",
    "Pos": "position",
    "G": "games",
    "GS": "games_started",
    "Att": "rush_attempts",
    "Yds": "rush_yards",
    "TD": "rush_td",
    "1D": "rush_first_downs",
    "Succ%": "rush_success_pct",
    "Lng": "rush_longest",
    "Y/A": "rush_yards_per_att",
    "Y/G": "rush_yards_per_game",
    "A/G": "rush_att_per_game",
    "Tgt": "targets",
    "Rec": "receptions",
    "Yds.1": "rec_yards",
    "Y/R": "yards_per_rec",
    "TD.1": "rec_td",
    "1D.1": "rec_first_downs",
    "Succ%.1": "rec_success_pct",
    "Lng.1": "rec_longest",
    "R/G": "rec_per_game",
    "Y/G.1": "rec_yards_per_game",
    "Ctch%": "catch_pct",
    "Y/Tgt": "yards_per_target",
    "Touch": "total_touches",
    "Y/Tch": "yards_per_touch",
    "YScm": "yards_from_scrimmage",
    "RRTD": "total_td",
    "Fmb": "fumbles",
    "Awards": "awards",
}

PROFILE_SCORING_COLUMNS = {
    "Rk": "rank",
    "Player": "player",
    "Age": "age",
    "Pos": "position",
    "G": "games",
    "GS": "games_started",
    "RshTD": "rush_td",
    "RecTD": "rec_td",
    "PRTD": "punt_return_td",
    "KRTD": "kick_return_td",
    "FRTD": "fumble_return_td",
    "IntTD": "int_return_td",
    "OthTD": "other_td",
    "AllTD": "total_td",
    "2PM": "two_pt_made",
    "D2P": "def_two_pt",
    "XPM": "extra_points_made",
    "XPA": "extra_points_att",
    "FGM": "field_goals_made",
    "FGA": "field_goals_att",
    "Sfty": "safeties",
    "Pts": "total_points",
    "Pts/G": "points_per_game",
    "Awards": "awards",
}


# =============================================================================
# TABLE CONFIGURATIONS
# =============================================================================

# Rankings page: /years/2025/
RANKINGS_TABLES = {
    "team_offense": {"index": 0, "columns": TEAM_STATS_COLUMNS},
    "team_defense": {"index": 1, "columns": TEAM_STATS_COLUMNS},
    "passing_offense": {"index": 2, "columns": PASSING_COLUMNS, "needs_header_fix": True},
    "passing_defense": {"index": 3, "columns": PASSING_COLUMNS, "needs_header_fix": True},
    "rushing_offense": {"index": 4, "columns": RUSHING_COLUMNS, "needs_header_fix": True},
    "rushing_defense": {"index": 5, "columns": RUSHING_COLUMNS, "needs_header_fix": True},
}

# Defensive stats page: /years/2025/opp.htm
DEFENSE_TABLES = {
    "scoring_offense": {"index": 0, "columns": SCORING_COLUMNS, "needs_header_fix": True},
    "advanced_defense": {"index": 1, "columns": ADVANCED_DEFENSE_COLUMNS, "needs_header_fix": True},
}

# Team profile page: /teams/{abbr}/2025.htm
PROFILE_TABLES = {
    "schedule": {"index": 0, "columns": SCHEDULE_COLUMNS},
    "team_stats": {"index": 1, "columns": TEAM_STATS_COLUMNS},
    "passing": {"index": 2, "columns": PROFILE_PASSING_COLUMNS, "needs_header_fix": True},
    "rushing_receiving": {"index": 3, "columns": RUSHING_RECEIVING_COLUMNS},
    "scoring": {"index": 5, "columns": PROFILE_SCORING_COLUMNS},
}

# Boxscore/Result tables (extracted after games are played)
# Note: player_offense is combined table that gets split into passing/rushing/receiving
RESULT_TABLES = {
    "scoring": "scoring",
    "game_info": "game_info",
    "team_stats": "team_stats",
    "player_offense": "player_offense",
    "defense": "player_defense",
    "home_starters": "home_starters",
    "away_starters": "vis_starters",
}


# =============================================================================
# URLS
# =============================================================================

BASE_URL = "https://www.pro-football-reference.com"
RANKINGS_URL = f"{BASE_URL}/years/2025/"
DEFENSE_URL = f"{BASE_URL}/years/2025/opp.htm"


def get_team_url(abbr: str) -> str:
    """Get team profile URL for a given abbreviation."""
    return f"{BASE_URL}/teams/{abbr.lower()}/2025.htm"


# =============================================================================
# TEAMS
# =============================================================================

TEAMS = [
    "atl", "rav", "buf", "car", "chi", "cin", "cle", "dal",
    "den", "det", "gnb", "htx", "clt", "jax", "kan", "sdg",
    "ram", "mia", "min", "nwe", "nor", "nyg", "nyj", "rai",
    "phi", "pit", "sfo", "sea", "tam", "oti", "was", "crd",
]
