"""CLI orchestrator service for betting workflows.

This module provides the CLIOrchestrator class for coordinating
CLI workflows across ODDS, PREDICTION, RESULTS, and ANALYSIS services.

Example usage:
    from services.cli import CLIOrchestrator, get_default_config

    config = get_default_config()
    orchestrator = CLIOrchestrator(sport="nfl", config=config)

    # Run full pipeline
    result = orchestrator.full_pipeline_workflow(
        game_date="2024-11-24",
        games=[{"away_team": "nyg", "home_team": "dal"}],
    )
"""

from services.cli.config import (
    CLIServiceConfig,
    WorkflowConfig,
    DisplayConfig,
    get_default_config,
    get_quiet_config,
    get_verbose_config,
)
from services.cli.orchestrator import CLIOrchestrator

__all__ = [
    # Service
    "CLIOrchestrator",
    # Configuration
    "CLIServiceConfig",
    "WorkflowConfig",
    "DisplayConfig",
    # Factory functions
    "get_default_config",
    "get_quiet_config",
    "get_verbose_config",
]
