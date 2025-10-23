"""Configuration constants for NFL stats scraping and analysis."""

# Current NFL season year
CURRENT_YEAR = 2025

# Rate limiting for Pro-Football-Reference (to avoid HTTP 429 errors)
PFR_RATE_LIMIT_CALLS = 1  # Number of calls allowed
PFR_RATE_LIMIT_PERIOD = 5  # Time period in seconds

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

# Data folder paths
DATA_RANKINGS_DIR = "data/rankings"
DATA_PROFILES_DIR = "data/profiles"
