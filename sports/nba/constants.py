"""Configuration constants for NBA stats scraping and analysis."""

from config import settings

# Current NBA season year
CURRENT_YEAR = settings['seasons']['nba']

# Rate limiting for Basketball-Reference (uses global Sports-Reference rate limits)
BBR_RATE_LIMIT_CALLS = settings['scraping']['sports_reference']['rate_limit_calls']
BBR_RATE_LIMIT_PERIOD = settings['scraping']['sports_reference']['rate_limit_period']

# URLs
NBA_STATS_URL = f"https://www.basketball-reference.com/leagues/NBA_{CURRENT_YEAR}.html"
NBA_TEAM_URL_PATTERN = f"https://www.basketball-reference.com/teams/{{pbr_abbr}}/{CURRENT_YEAR}.html"

# Ranking tables to extract (table_name: html_table_id)
RANKING_TABLES = {
    "eastern_conference": "confs_standings_E",
    "western_conference": "confs_standings_W",
    "per_game_stats": "per_game-team",
    "total_stats": "totals-team",
    "advanced_stats": "advanced-team",
    "shooting_stats": "shooting-team",
}

# Team profile tables to extract
TEAM_PROFILE_TABLES = {
    "injuries": "injuries",
    "per_game_stats": "per_game_stats",
    "totals_stats": "totals_stats",
    "team_and_opponent": "team_and_opponent",
    "adj_shooting": "adj_shooting",
    "shooting": "shooting",
}

# Data folder paths
DATA_RANKINGS_DIR = "sports/nba/data/rankings"
DATA_PROFILES_DIR = "sports/nba/data/profiles"
