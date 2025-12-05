"""Configuration constants for Bundesliga stats scraping and analysis."""

from config import settings

# Current Bundesliga season
CURRENT_SEASON = settings['seasons']['bundesliga']

# FBRef competition ID for Bundesliga
FBREF_COMP_ID = 20

# Rate limiting for FBRef (uses global Sports-Reference rate limits)
FBREF_RATE_LIMIT_CALLS = settings['scraping']['sports_reference']['rate_limit_calls']
FBREF_RATE_LIMIT_PERIOD = settings['scraping']['sports_reference']['rate_limit_period']

# URLs
BUNDESLIGA_STATS_URL = "https://fbref.com/en/comps/20/Bundesliga-Stats"
TEAM_URL_PATTERN = "https://fbref.com/en/squads/{fbref_id}/{slug}"

# Ranking tables to extract (output_name: html_table_id)
RANKING_TABLES = {
    "standings": "results2025-2026201_overall",
    "standings_home_away": "results2025-2026201_home_away",
    "squad_standard": "stats_squads_standard_for",
    "squad_shooting": "stats_squads_shooting_for",
    "squad_pass_types": "stats_squads_passing_types_for",
    "squad_gca": "stats_squads_gca_for",
}

# Team profile tables to extract (output_name: html_table_id)
PROFILE_TABLES = {
    "fixtures": "matchlogs_for",
}

# Data folder paths
DATA_RANKINGS_DIR = "sports/futbol/bundesliga/data/rankings"
DATA_PROFILES_DIR = "sports/futbol/bundesliga/data/profiles"
