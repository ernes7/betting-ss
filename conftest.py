"""Global pytest configuration and fixtures.

This file provides shared fixtures available to all tests.
Service-specific fixtures should be in services/*/tests/conftest.py
"""

import json
import pytest
from datetime import datetime
from pathlib import Path
from typing import Any

from shared.models import (
    Game, Team, GameStatus,
    Bet, BetType, BetOutcome,
    Odds, GameLines, PlayerProp,
    Prediction, PredictionSource, PredictionStatus,
    Result, GameScore, PlayerStats,
    Analysis, BetResult,
)
from shared.scraping import ScraperConfig
from shared.logging import LoggerFactory


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def test_config_dir(tmp_path_factory) -> Path:
    """Create a temporary config directory for tests."""
    return tmp_path_factory.mktemp("config")


@pytest.fixture
def scraper_config() -> ScraperConfig:
    """Default scraper configuration for tests."""
    return ScraperConfig(
        interval_seconds=0.1,  # Fast for tests
        timeout_ms=5000,
        max_retries=1,
        retry_delay_seconds=0.1,
        headless=True,
        wait_time_ms=100,
    )


# ============================================================================
# Model Fixtures
# ============================================================================

@pytest.fixture
def sample_team_home() -> Team:
    """Sample home team."""
    return Team(
        name="Dallas Cowboys",
        abbreviation="DAL",
        city="Dallas",
        nickname="Cowboys",
    )


@pytest.fixture
def sample_team_away() -> Team:
    """Sample away team."""
    return Team(
        name="New York Giants",
        abbreviation="NYG",
        city="New York",
        nickname="Giants",
    )


@pytest.fixture
def sample_game(sample_team_home, sample_team_away) -> Game:
    """Sample game fixture."""
    return Game(
        id="2024_week1_dal_nyg",
        sport="nfl",
        home_team=sample_team_home,
        away_team=sample_team_away,
        game_date=datetime(2024, 9, 8, 13, 0, 0),
        status=GameStatus.SCHEDULED,
        venue="AT&T Stadium",
    )


@pytest.fixture
def sample_bet() -> Bet:
    """Sample bet fixture."""
    return Bet(
        id="bet_001",
        player="Dak Prescott",
        team="DAL",
        market="passing_yards",
        line=275.5,
        odds=-110,
        ev_edge=0.05,
        recommended_stake=100.0,
        bet_type=BetType.PLAYER_PROP,
        description="Dak Prescott Over 275.5 Passing Yards",
    )


@pytest.fixture
def sample_game_lines() -> GameLines:
    """Sample game lines fixture."""
    return GameLines(
        moneyline_home=-150,
        moneyline_away=130,
        spread_home=-3.5,
        spread_home_odds=-110,
        spread_away=3.5,
        spread_away_odds=-110,
        total=47.5,
        over_odds=-110,
        under_odds=-110,
    )


@pytest.fixture
def sample_player_prop() -> PlayerProp:
    """Sample player prop fixture."""
    return PlayerProp(
        player="Dak Prescott",
        team="DAL",
        market="passing_yards",
        line=275.5,
        over_odds=-110,
        under_odds=-110,
        milestones=[
            {"threshold": 250, "odds": -200},
            {"threshold": 300, "odds": 150},
        ],
    )


@pytest.fixture
def sample_odds(sample_game_lines, sample_player_prop) -> Odds:
    """Sample odds fixture."""
    return Odds(
        sport="nfl",
        home_team="DAL",
        away_team="NYG",
        game_date=datetime(2024, 9, 8, 13, 0, 0),
        game_lines=sample_game_lines,
        player_props=[sample_player_prop],
        source="draftkings",
        fetched_at=datetime.now(),
    )


@pytest.fixture
def sample_prediction(sample_bet) -> Prediction:
    """Sample prediction fixture."""
    return Prediction(
        id="pred_001",
        sport="nfl",
        home_team="DAL",
        away_team="NYG",
        game_date=datetime(2024, 9, 8, 13, 0, 0),
        bets=[sample_bet],
        source=PredictionSource.AI,
        status=PredictionStatus.PENDING,
        confidence=0.75,
        analysis_summary="Dallas favored at home with strong passing attack.",
        model="claude-sonnet-4-5-20250929",
    )


@pytest.fixture
def sample_result() -> Result:
    """Sample result fixture."""
    return Result(
        sport="nfl",
        home_team="DAL",
        away_team="NYG",
        game_date=datetime(2024, 9, 8, 13, 0, 0),
        score=GameScore(home_score=28, away_score=17),
        player_stats=[
            PlayerStats(
                player="Dak Prescott",
                team="DAL",
                stats={"passing_yards": 289, "passing_tds": 3},
            ),
        ],
        source="pro-football-reference",
    )


@pytest.fixture
def sample_analysis() -> Analysis:
    """Sample analysis fixture."""
    return Analysis(
        sport="nfl",
        home_team="DAL",
        away_team="NYG",
        game_date=datetime(2024, 9, 8, 13, 0, 0),
        bet_results=[
            BetResult(
                bet_id="bet_001",
                player="Dak Prescott",
                market="passing_yards",
                line=275.5,
                odds=-110,
                predicted_value=280,
                actual_value=289,
                outcome=BetOutcome.WON,
                profit=90.91,
                stake=100.0,
            ),
        ],
        summary="1 bet placed, 1 won. ROI: 90.91%",
    )


# ============================================================================
# Data Fixtures
# ============================================================================

@pytest.fixture
def temp_data_dir(tmp_path) -> Path:
    """Create a temporary data directory structure."""
    data_dir = tmp_path / "nfl" / "data"
    (data_dir / "odds").mkdir(parents=True)
    (data_dir / "predictions").mkdir(parents=True)
    (data_dir / "results").mkdir(parents=True)
    (data_dir / "analysis").mkdir(parents=True)
    return data_dir


@pytest.fixture
def sample_odds_file(temp_data_dir, sample_odds) -> Path:
    """Create a sample odds JSON file."""
    date_dir = temp_data_dir / "odds" / "2024-09-08"
    date_dir.mkdir(parents=True, exist_ok=True)
    file_path = date_dir / "DAL_NYG.json"
    file_path.write_text(json.dumps(sample_odds.to_dict(), indent=2))
    return file_path


# ============================================================================
# Cleanup Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def reset_loggers():
    """Reset loggers between tests."""
    yield
    LoggerFactory.reset()


@pytest.fixture
def clean_error_file(tmp_path):
    """Ensure errors.json is cleaned up after test."""
    error_file = tmp_path / "errors.json"
    yield error_file
    if error_file.exists():
        error_file.unlink()
