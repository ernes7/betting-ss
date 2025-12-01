"""Test fixtures for the RESULTS service tests."""

import pytest
from unittest.mock import MagicMock

from services.results import (
    ResultsService,
    ResultsFetcher,
    ResultsParser,
    ResultsServiceConfig,
    get_default_config,
)
from shared.scraping import ScraperConfig


@pytest.fixture
def parser():
    """Create a ResultsParser instance."""
    return ResultsParser()


@pytest.fixture
def test_results_config():
    """Create a test configuration for the RESULTS service."""
    return ResultsServiceConfig(
        scraper_config=ScraperConfig(
            interval_seconds=1.0,
            timeout_ms=5000,
            headless=True,
        ),
        result_tables={
            "scoring": "scoring",
            "game_info": "game_info",
            "team_stats": "team_stats",
            "player_offense": "player_offense",
            "defense": "player_defense",
        },
    )


@pytest.fixture
def sample_scoring_data():
    """Sample scoring table data for NFL games."""
    return {
        "table_name": "scoring",
        "headers": ["quarter", "time", "team", "detail", "vis_team_score", "home_team_score"],
        "data": [
            {
                "quarter": "1",
                "time": "10:25",
                "team": "Giants",
                "detail": "FG 45 yards",
                "vis_team_score": "3",
                "home_team_score": "0",
            },
            {
                "quarter": "1",
                "time": "5:12",
                "team": "Cowboys",
                "detail": "TD pass 15 yards",
                "vis_team_score": "3",
                "home_team_score": "7",
            },
            {
                "quarter": "2",
                "time": "12:30",
                "team": "Giants",
                "detail": "TD run 5 yards",
                "vis_team_score": "10",
                "home_team_score": "7",
            },
            {
                "quarter": "4",
                "time": "0:00",
                "team": "",
                "detail": "End of Game",
                "vis_team_score": "24",
                "home_team_score": "21",
            },
        ],
    }


@pytest.fixture
def sample_player_offense_data():
    """Sample player_offense table data for NFL games."""
    return {
        "table_name": "player_offense",
        "headers": ["player", "team", "pass_cmp", "pass_att", "pass_yds", "pass_td", "rush_att", "rush_yds", "rush_td", "targets", "rec", "rec_yds", "rec_td"],
        "data": [
            # Quarterback - has passing stats
            {
                "player": "Dak Prescott",
                "team": "DAL",
                "pass_cmp": "25",
                "pass_att": "35",
                "pass_yds": "280",
                "pass_td": "2",
                "rush_att": "3",
                "rush_yds": "15",
                "rush_td": "0",
                "targets": "0",
                "rec": "0",
                "rec_yds": "0",
                "rec_td": "0",
            },
            # Running back - has rushing and receiving stats
            {
                "player": "Tony Pollard",
                "team": "DAL",
                "pass_cmp": "0",
                "pass_att": "0",
                "pass_yds": "0",
                "pass_td": "0",
                "rush_att": "18",
                "rush_yds": "95",
                "rush_td": "1",
                "targets": "4",
                "rec": "3",
                "rec_yds": "25",
                "rec_td": "0",
            },
            # Wide receiver - has receiving stats only
            {
                "player": "CeeDee Lamb",
                "team": "DAL",
                "pass_cmp": "0",
                "pass_att": "0",
                "pass_yds": "0",
                "pass_td": "0",
                "rush_att": "0",
                "rush_yds": "0",
                "rush_td": "0",
                "targets": "12",
                "rec": "8",
                "rec_yds": "120",
                "rec_td": "1",
            },
            # Player with no stats (bench player)
            {
                "player": "Cooper Rush",
                "team": "DAL",
                "pass_cmp": "0",
                "pass_att": "0",
                "pass_yds": "0",
                "pass_td": "0",
                "rush_att": "0",
                "rush_yds": "0",
                "rush_td": "0",
                "targets": "0",
                "rec": "0",
                "rec_yds": "0",
                "rec_td": "0",
            },
        ],
    }


@pytest.fixture
def sample_result_data():
    """Sample complete result data."""
    return {
        "sport": "nfl",
        "game_date": "2024-11-24",
        "teams": {"away": "Giants", "home": "Cowboys"},
        "final_score": {"away": 24, "home": 21},
        "winner": "Giants",
        "boxscore_url": "https://www.pro-football-reference.com/boxscores/202411240dal.htm",
        "fetched_at": "2024-11-24 20:00:00",
        "tables": {
            "scoring": {
                "table_name": "scoring",
                "data": [
                    {"vis_team_score": "24", "home_team_score": "21"},
                ],
            },
            "passing": {"table_name": "Passing", "data": []},
            "rushing": {"table_name": "Rushing", "data": []},
            "receiving": {"table_name": "Receiving", "data": []},
        },
    }


@pytest.fixture
def mock_scraper():
    """Create a mock web scraper."""
    scraper = MagicMock()
    page = MagicMock()
    response = MagicMock()
    response.status = 200

    scraper.launch.return_value.__enter__ = MagicMock(return_value=page)
    scraper.launch.return_value.__exit__ = MagicMock(return_value=False)
    scraper.navigate_and_wait.return_value = response

    return scraper, page, response


@pytest.fixture
def mock_fetcher(test_results_config, mock_scraper):
    """Create a results fetcher with mock scraper."""
    scraper, page, response = mock_scraper
    fetcher = ResultsFetcher(
        sport="nfl",
        config=test_results_config,
        scraper=scraper,
    )
    return fetcher
