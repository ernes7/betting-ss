"""CLI service test fixtures."""

import pytest

from services.cli import (
    CLIServiceConfig,
    WorkflowConfig,
    DisplayConfig,
)


@pytest.fixture
def workflow_config() -> WorkflowConfig:
    """Default workflow configuration for tests."""
    return WorkflowConfig(
        skip_existing=True,
        save_results=True,
        show_progress=False,
        confirm_actions=False,
    )


@pytest.fixture
def display_config() -> DisplayConfig:
    """Default display configuration for tests."""
    return DisplayConfig(
        use_colors=False,
        use_panels=False,
        show_timestamps=False,
        verbose=False,
    )


@pytest.fixture
def test_cli_config(workflow_config, display_config) -> CLIServiceConfig:
    """Test CLI configuration."""
    return CLIServiceConfig(
        workflow=workflow_config,
        display=display_config,
        default_sport="nfl",
        fixed_bet_amount=100.0,
    )


@pytest.fixture
def sample_games() -> list:
    """Sample list of games."""
    return [
        {"away_team": "nyg", "home_team": "dal"},
        {"away_team": "phi", "home_team": "was"},
    ]


@pytest.fixture
def sample_workflow_result() -> dict:
    """Sample workflow result."""
    return {
        "success": True,
        "game_date": "2024-11-24",
        "games_processed": 2,
        "games_skipped": 0,
        "games_failed": 0,
        "details": [
            {"game": {"away_team": "nyg", "home_team": "dal"}, "status": "success"},
            {"game": {"away_team": "phi", "home_team": "was"}, "status": "success"},
        ],
    }
