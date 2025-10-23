"""Configuration constants for NFL stats scraping and analysis."""

# Current NFL season year
CURRENT_YEAR = 2025

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

# Data folder paths
DATA_RANKINGS_DIR = "data/rankings"
DATA_PROFILES_DIR = "data/profiles"
