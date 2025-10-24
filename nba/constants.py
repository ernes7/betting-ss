"""Configuration constants for NBA stats scraping and analysis."""

from global_constants import (
    SPORTS_REFERENCE_RATE_LIMIT_CALLS,
    SPORTS_REFERENCE_RATE_LIMIT_PERIOD,
)

# Current NBA season year
CURRENT_YEAR = 2026

# Rate limiting for Basketball-Reference (uses global Sports-Reference rate limits)
BBR_RATE_LIMIT_CALLS = SPORTS_REFERENCE_RATE_LIMIT_CALLS
BBR_RATE_LIMIT_PERIOD = SPORTS_REFERENCE_RATE_LIMIT_PERIOD

# URLs
# TODO: Add specific Basketball-Reference URLs
NBA_STATS_URL = f"https://www.basketball-reference.com/leagues/NBA_{CURRENT_YEAR}.html"

# Ranking tables to extract (table_name: html_table_id)
# TODO: Add specific table IDs after inspecting Basketball-Reference
RANKING_TABLES = {
    # "team_stats": "team_stats",
    # "advanced_stats": "advanced",
    # "eastern_standings": "confs_standings_E",
    # "western_standings": "confs_standings_W",
}

# Team profile tables to extract
# TODO: Add specific table IDs after inspecting team pages
TEAM_PROFILE_TABLES = {
    # "team_stats": "team_stats",
    # "schedule_results": "games",
    # "roster": "roster",
}

# Data folder paths
DATA_RANKINGS_DIR = "nba/data/rankings"
DATA_PROFILES_DIR = "nba/data/profiles"
