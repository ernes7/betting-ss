"""Analysis service test fixtures."""

import pytest
from datetime import datetime

from services.analysis import (
    AnalysisServiceConfig,
    MatchingConfig,
    ProfitConfig,
)


@pytest.fixture
def matching_config() -> MatchingConfig:
    """Default matching configuration for tests."""
    return MatchingConfig(
        name_similarity_threshold=0.85,
        check_all_tables=True,
        normalize_names=True,
        use_nickname_mapping=True,
    )


@pytest.fixture
def profit_config() -> ProfitConfig:
    """Default profit configuration for tests."""
    return ProfitConfig(
        default_stake=100.0,
        default_odds=-110,
    )


@pytest.fixture
def test_analysis_config(tmp_path) -> AnalysisServiceConfig:
    """Test configuration with temp directory."""
    return AnalysisServiceConfig(
        matching_config=MatchingConfig(),
        profit_config=ProfitConfig(),
        data_root=str(tmp_path / "{sport}" / "data" / "analysis"),
        analysis_type="analysis",
        skip_existing=False,
    )


@pytest.fixture
def sample_prediction_data() -> dict:
    """Sample prediction data with bets array."""
    return {
        "sport": "nfl",
        "prediction_type": "ev_calculator",
        "teams": ["Giants", "Cowboys"],
        "home_team": "Cowboys",
        "date": "2024-11-24",
        "bets": [
            {
                "description": "Dak Prescott Over 275 Pass Yds",
                "market": "passing_yards",
                "player": "Dak Prescott",
                "line": 275.0,
                "side": "over",
                "odds": -110,
                "ev_percent": 5.2,
            },
            {
                "description": "CeeDee Lamb Over 85.5 Rec Yds",
                "market": "receiving_yards",
                "player": "CeeDee Lamb",
                "line": 85.5,
                "side": "over",
                "odds": -110,
                "ev_percent": 4.8,
            },
        ],
    }


@pytest.fixture
def sample_ai_prediction_data() -> dict:
    """Sample AI prediction data with free-text bets."""
    return {
        "sport": "nfl",
        "prediction_type": "ai_predictor",
        "teams": ["Giants", "Cowboys"],
        "home_team": "Cowboys",
        "date": "2024-11-24",
        "bets": [
            {
                "bet": "Dak Prescott Over 275 Passing Yards",
                "odds": -110,
                "expected_value": 5.2,
            },
            {
                "bet": "CeeDee Lamb Over 85.5 Receiving Yards",
                "odds": -110,
                "expected_value": 4.8,
            },
            {
                "bet": "Cowboys -3.5",
                "odds": -110,
                "expected_value": 3.5,
            },
        ],
    }


@pytest.fixture
def sample_result_data() -> dict:
    """Sample game result data."""
    return {
        "sport": "nfl",
        "teams": {
            "home": "Cowboys",
            "away": "Giants",
        },
        "final_score": {
            "home": 27,
            "away": 20,
        },
        "tables": {
            "passing": {
                "columns": ["player", "pass_yds", "pass_td", "int"],
                "data": [
                    {"player": "Dak Prescott", "pass_yds": 289, "pass_td": 3, "int": 0},
                    {"player": "Tommy DeVito", "pass_yds": 185, "pass_td": 1, "int": 2},
                ],
            },
            "rushing": {
                "columns": ["player", "rush_yds", "rush_td", "att"],
                "data": [
                    {"player": "Rico Dowdle", "rush_yds": 85, "rush_td": 1, "att": 18},
                    {"player": "Devin Singletary", "rush_yds": 42, "rush_td": 0, "att": 10},
                ],
            },
            "receiving": {
                "columns": ["player", "rec_yds", "rec_td", "rec"],
                "data": [
                    {"player": "CeeDee Lamb", "rec_yds": 112, "rec_td": 1, "rec": 8},
                    {"player": "Brandin Cooks", "rec_yds": 65, "rec_td": 0, "rec": 5},
                    {"player": "Darius Slayton", "rec_yds": 78, "rec_td": 1, "rec": 6},
                ],
            },
        },
    }


@pytest.fixture
def sample_result_data_losing() -> dict:
    """Sample game result data where bets would lose."""
    return {
        "sport": "nfl",
        "teams": {
            "home": "Cowboys",
            "away": "Giants",
        },
        "final_score": {
            "home": 17,
            "away": 24,  # Giants win
        },
        "tables": {
            "passing": {
                "columns": ["player", "pass_yds", "pass_td", "int"],
                "data": [
                    {"player": "Dak Prescott", "pass_yds": 210, "pass_td": 1, "int": 2},  # Under 275
                    {"player": "Tommy DeVito", "pass_yds": 245, "pass_td": 2, "int": 0},
                ],
            },
            "rushing": {
                "columns": ["player", "rush_yds", "rush_td", "att"],
                "data": [
                    {"player": "Rico Dowdle", "rush_yds": 45, "rush_td": 0, "att": 12},
                ],
            },
            "receiving": {
                "columns": ["player", "rec_yds", "rec_td", "rec"],
                "data": [
                    {"player": "CeeDee Lamb", "rec_yds": 65, "rec_td": 0, "rec": 5},  # Under 85.5
                    {"player": "Darius Slayton", "rec_yds": 98, "rec_td": 2, "rec": 7},
                ],
            },
        },
    }


@pytest.fixture
def sample_analysis_result() -> dict:
    """Sample analysis result."""
    return {
        "sport": "nfl",
        "game_date": "2024-11-24",
        "away_team": "Giants",
        "home_team": "Cowboys",
        "matchup": "Giants @ Cowboys",
        "prediction_type": "ev_calculator",
        "bet_results": [
            {
                "bet": "Dak Prescott Over 275 Pass Yds",
                "won": True,
                "actual": 289,
                "line": 275.0,
                "profit": 90.91,
            },
            {
                "bet": "CeeDee Lamb Over 85.5 Rec Yds",
                "won": True,
                "actual": 112,
                "line": 85.5,
                "profit": 90.91,
            },
        ],
        "summary": {
            "total_bets": 2,
            "bets_won": 2,
            "bets_lost": 0,
            "win_rate": 100.0,
            "total_profit": 181.82,
            "total_staked": 200.0,
            "roi_percent": 90.9,
        },
    }
