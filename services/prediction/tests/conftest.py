"""Test fixtures for the PREDICTION service tests."""

import pytest
from unittest.mock import MagicMock, patch

from services.prediction import (
    PredictionService,
    PredictionServiceConfig,
    EVPredictor,
    AIPredictor,
    EVConfig,
    AIConfig,
    get_default_config,
)


@pytest.fixture
def ev_config():
    """Create an EV configuration for testing."""
    return EVConfig(
        conservative_adjustment=0.85,
        min_ev_threshold=0.0,
        top_n_bets=5,
        deduplicate_players=True,
        max_receivers_per_team=1,
    )


@pytest.fixture
def ai_config():
    """Create an AI configuration for testing."""
    return AIConfig(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2048,
        rate_limit_seconds=0,  # No rate limiting in tests
    )


@pytest.fixture
def test_prediction_config(ev_config, ai_config):
    """Create a test configuration for the PREDICTION service."""
    return PredictionServiceConfig(
        ev_config=ev_config,
        ai_config=ai_config,
        use_dual_predictions=True,
        skip_existing=False,
    )


@pytest.fixture
def sample_odds_data():
    """Sample odds data for testing."""
    return {
        "sport": "nfl",
        "source": "draftkings",
        "teams": {
            "away": {
                "name": "New York Giants",
                "abbr": "NYG",
                "pfr_abbr": "nyg",
            },
            "home": {
                "name": "Dallas Cowboys",
                "abbr": "DAL",
                "pfr_abbr": "dal",
            },
        },
        "game_lines": {
            "moneyline": {
                "home": -150,
                "away": 130,
            },
            "spread": {
                "home": -3.5,
                "home_odds": -110,
                "away": 3.5,
                "away_odds": -110,
            },
            "total": {
                "line": 47.5,
                "over": -110,
                "under": -110,
            },
        },
        "player_props": [
            {
                "player": "Dak Prescott",
                "team": "HOME",
                "position": "QB",
                "market": "passing_yards",
                "milestones": [
                    {"line": 250, "odds": -200},
                    {"line": 275, "odds": -110},
                    {"line": 300, "odds": 150},
                ],
            },
            {
                "player": "CeeDee Lamb",
                "team": "HOME",
                "position": "WR",
                "market": "receiving_yards",
                "milestones": [
                    {"line": 75, "odds": -150},
                    {"line": 100, "odds": 110},
                ],
            },
        ],
    }


@pytest.fixture
def sample_ev_result():
    """Sample EV prediction result."""
    return {
        "success": True,
        "bets": [
            {
                "description": "Dak Prescott Over 275.5 Pass Yds",
                "bet_type": "player_prop",
                "player": "Dak Prescott",
                "market": "passing_yards",
                "line": 275.5,
                "odds": -110,
                "decimal_odds": 1.91,
                "implied_prob": 52.4,
                "true_prob": 58.0,
                "adjusted_prob": 55.0,
                "ev_percent": 5.05,
                "reasoning": "Prescott averages 285 pass yards/game (last 5 games) vs #20 defense",
            },
            {
                "description": "CeeDee Lamb Over 85.5 Rec Yds",
                "bet_type": "player_prop",
                "player": "CeeDee Lamb",
                "market": "receiving_yards",
                "line": 85.5,
                "odds": -120,
                "decimal_odds": 1.83,
                "implied_prob": 54.5,
                "true_prob": 62.0,
                "adjusted_prob": 58.0,
                "ev_percent": 6.14,
                "reasoning": "Lamb averages 95 rec yards/game (last 5 games) vs #18 defense",
            },
        ],
        "total_analyzed": 45,
        "top_bets": 2,
        "config": {
            "conservative_adjustment": 0.85,
            "min_ev_threshold": 0.0,
            "deduplicate_players": True,
        },
    }


@pytest.fixture
def sample_ai_result():
    """Sample AI prediction result."""
    return {
        "success": True,
        "prediction": """# EV+ Singles Analysis: Giants @ Cowboys

## Bet 1: Dak Prescott Over 275 Pass Yds
**Bet**: Dak Prescott Over 275 Pass Yds
**Odds**: -110
**Implied Probability**: 52.4%
**True Probability**: 60.0%
**Expected Value**: +6.5%

## Bet 2: Cowboys -3.5
**Bet**: Cowboys -3.5
**Odds**: -110
**Implied Probability**: 52.4%
**True Probability**: 58.0%
**Expected Value**: +5.2%
""",
        "bets": [
            {
                "rank": 1,
                "bet": "Dak Prescott Over 275 Pass Yds",
                "odds": -110,
                "implied_probability": 52.4,
                "true_probability": 60.0,
                "expected_value": 6.5,
            },
            {
                "rank": 2,
                "bet": "Cowboys -3.5",
                "odds": -110,
                "implied_probability": 52.4,
                "true_probability": 58.0,
                "expected_value": 5.2,
            },
        ],
        "cost": 0.15,
        "model": "claude-sonnet-4-5-20250929",
        "tokens": {"input": 5000, "output": 500, "total": 5500},
    }


@pytest.fixture
def mock_sport_config():
    """Create a mock sport configuration."""
    config = MagicMock()
    config.sport_name = "nfl"
    config.data_rankings_dir = "nfl/data/rankings"
    config.data_profiles_dir = "nfl/data/profiles"
    config.prompt_components = {}
    return config


@pytest.fixture
def mock_ev_calculator():
    """Create a mock EV calculator."""
    calculator = MagicMock()
    calculator.calculate_all_ev.return_value = []
    calculator.get_top_n.return_value = []
    return calculator


@pytest.fixture
def mock_predictor():
    """Create a mock AI predictor."""
    predictor = MagicMock()
    predictor.generate_predictions.return_value = {
        "success": True,
        "prediction": "Test prediction",
        "cost": 0.10,
        "model": "claude-sonnet-4-5-20250929",
        "tokens": {"input": 1000, "output": 200, "total": 1200},
    }
    return predictor
