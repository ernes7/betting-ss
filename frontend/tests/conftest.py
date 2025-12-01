"""Streamlit service test fixtures."""

import pytest
import json
import tempfile
from pathlib import Path

from frontend import (
    StreamlitServiceConfig,
    DataPathConfig,
    DisplayConfig,
    ThemeConfig,
)


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create temporary data directory structure."""
    # NFL predictions
    nfl_pred_dir = tmp_path / "sports" / "nfl" / "data" / "predictions" / "2024-11-24"
    nfl_pred_dir.mkdir(parents=True)

    # NFL analysis
    nfl_analysis_dir = tmp_path / "sports" / "nfl" / "data" / "analysis" / "2024-11-24"
    nfl_analysis_dir.mkdir(parents=True)

    return tmp_path


@pytest.fixture
def sample_ai_prediction():
    """Sample AI prediction data."""
    return {
        "sport": "nfl",
        "prediction_type": "ai_predictor",
        "teams": ["Giants", "Cowboys"],
        "home_team": "Cowboys",
        "generated_at": "2024-11-24T10:00:00",
        "bets": [
            {
                "bet": "Dak Prescott Over 275 Passing Yards",
                "odds": -110,
                "expected_value": 5.2,
            },
        ],
    }


@pytest.fixture
def sample_ev_prediction():
    """Sample EV prediction data."""
    return {
        "sport": "nfl",
        "prediction_type": "ev_calculator",
        "teams": ["Giants", "Cowboys"],
        "home_team": "Cowboys",
        "generated_at": "2024-11-24T10:30:00",
        "bets": [
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
def sample_analysis_dual():
    """Sample dual-system analysis data."""
    return {
        "ai_system": {
            "bet_results": [
                {"bet": "Dak Prescott Over 275 Pass Yds", "won": True, "profit": 90.91},
            ],
            "summary": {
                "total_bets": 1,
                "bets_won": 1,
                "bets_lost": 0,
                "win_rate": 100.0,
                "total_profit": 90.91,
            },
        },
        "ev_system": {
            "bet_results": [
                {"bet": "CeeDee Lamb Over 85.5 Rec Yds", "won": True, "profit": 90.91},
            ],
            "summary": {
                "total_bets": 1,
                "bets_won": 1,
                "bets_lost": 0,
                "win_rate": 100.0,
                "total_profit": 90.91,
            },
        },
    }


@pytest.fixture
def sample_analysis_legacy():
    """Sample legacy single-system analysis data."""
    return {
        "bet_results": [
            {"bet": "Dak Prescott Over 275 Pass Yds", "won": True, "profit": 90.91},
        ],
        "summary": {
            "total_bets": 1,
            "bets_won": 1,
            "bets_lost": 0,
            "win_rate": 100.0,
            "total_profit": 90.91,
        },
    }


@pytest.fixture
def populated_data_dir(temp_data_dir, sample_ai_prediction, sample_ev_prediction, sample_analysis_dual):
    """Create populated data directory with sample files."""
    # Create predictions
    pred_dir = temp_data_dir / "sports" / "nfl" / "data" / "predictions" / "2024-11-24"

    with open(pred_dir / "nyg_dal_ai.json", "w") as f:
        json.dump(sample_ai_prediction, f)

    with open(pred_dir / "nyg_dal_ev.json", "w") as f:
        json.dump(sample_ev_prediction, f)

    # Create analysis
    analysis_dir = temp_data_dir / "sports" / "nfl" / "data" / "analysis" / "2024-11-24"

    with open(analysis_dir / "nyg_dal.json", "w") as f:
        json.dump(sample_analysis_dual, f)

    return temp_data_dir


@pytest.fixture
def test_config(temp_data_dir):
    """Test configuration with temp directory."""
    return StreamlitServiceConfig(
        paths=DataPathConfig(),
        display=DisplayConfig(),
        theme=ThemeConfig(),
    )
