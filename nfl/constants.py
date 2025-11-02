"""Configuration constants for NFL stats scraping and analysis."""

from global_constants import (
    SPORTS_REFERENCE_RATE_LIMIT_CALLS,
    SPORTS_REFERENCE_RATE_LIMIT_PERIOD,
)

# Current NFL season year
CURRENT_YEAR = 2025

# Fixed bet amount for P&L calculations (in dollars)
FIXED_BET_AMOUNT = 100

# Rate limiting for Pro-Football-Reference (uses global Sports-Reference rate limits)
PFR_RATE_LIMIT_CALLS = SPORTS_REFERENCE_RATE_LIMIT_CALLS
PFR_RATE_LIMIT_PERIOD = SPORTS_REFERENCE_RATE_LIMIT_PERIOD

# URLs
NFL_STATS_URL = f"https://www.pro-football-reference.com/years/{CURRENT_YEAR}/"

# Ranking tables to extract (table_name: html_table_id)
# These are aggregate tables with all 32 teams
RANKING_TABLES = {
    "team_offense": "team_stats",
    "passing_offense": "passing",
    "rushing_offense": "rushing",
    "scoring_offense": "team_scoring",
    "afc_standings": "AFC",
    "nfc_standings": "NFC",
}

# Team profile tables to extract
# Note: injury_report requires team abbreviation (e.g., 'crd_injury_report' for Arizona)
TEAM_PROFILE_TABLES = {
    "injury_report": "{pfr_abbr}_injury_report",  # Dynamic: uses team abbreviation
    "team_stats": "team_stats",
    "schedule_results": "games",
    "passing": "passing",
    "rushing_receiving": "rushing_and_receiving",
    "defense_fumbles": "defense",
    "scoring_summary": "scoring",
    "touchdown_log": "team_td_log",
}

# Result tables to extract from boxscore pages
# These are extracted after a game has been played
# Note: player_offense is a combined table that will be split into passing/rushing/receiving
RESULT_TABLES = {
    "scoring": "scoring",
    "game_info": "game_info",
    "team_stats": "team_stats",
    "player_offense": "player_offense",  # Combined offensive stats (split later into passing/rushing/receiving)
    "defense": "player_defense",
    "home_starters": "home_starters",
    "away_starters": "vis_starters",
}

# Data folder paths
DATA_RANKINGS_DIR = "nfl/data/rankings"
DATA_PROFILES_DIR = "nfl/data/profiles"
DATA_ODDS_DIR = "nfl/data/odds"

# Odds market types (for DraftKings scraping)
ODDS_MARKET_TYPES = {
    # Game lines
    "game_lines": ["Moneyline", "Spread", "Total"],
    # Player props - Passing
    "passing_props": [
        "Passing Yards Milestones",
        "Passing Touchdowns Milestones",
        "Pass Completions Milestones",
        "Pass Attempts Milestones",
    ],
    # Player props - Rushing
    "rushing_props": [
        "Rushing Yards Milestones",
        "Rushing Attempts Milestones",
        "Rushing + Receiving Yards Milestones",
    ],
    # Player props - Receiving
    "receiving_props": [
        "Receiving Yards Milestones",
        "Receptions Milestones",
    ],
    # Touchdown scorers
    "touchdown_props": ["Anytime Touchdown Scorer"],
    # Defensive props
    "defensive_props": [
        "Sacks Milestones",
        "Tackles + Assists Milestones",
        "Interceptions Milestones",
    ],
}
