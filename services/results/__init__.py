"""RESULTS service for fetching game results.

This service fetches game results from sports reference sites
(Pro-Football-Reference, Basketball-Reference) and extracts
structured data from boxscore pages.

Example:
    from services.results import ResultsService

    service = ResultsService(sport="nfl")
    result = service.fetch_game_result(date="20241124", home_abbr="dal")
"""

from services.results.config import (
    ResultsServiceConfig,
    get_default_config,
    build_boxscore_url,
    NFL_RESULT_TABLES,
    NBA_RESULT_TABLES,
    BOXSCORE_URL_TEMPLATES,
)
from services.results.parser import ResultsParser
from services.results.fetcher import ResultsFetcher
from services.results.service import ResultsService


__all__ = [
    # Main service
    "ResultsService",
    # Components
    "ResultsFetcher",
    "ResultsParser",
    # Configuration
    "ResultsServiceConfig",
    "get_default_config",
    "build_boxscore_url",
    # Constants
    "NFL_RESULT_TABLES",
    "NBA_RESULT_TABLES",
    "BOXSCORE_URL_TEMPLATES",
]
