"""Configuration for the CLI orchestrator service."""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass(frozen=True)
class WorkflowConfig:
    """Configuration for CLI workflows.

    Attributes:
        skip_existing: Whether to skip already processed items
        save_results: Whether to save results to disk
        show_progress: Whether to show progress indicators
        confirm_actions: Whether to confirm before actions
    """
    skip_existing: bool = True
    save_results: bool = True
    show_progress: bool = True
    confirm_actions: bool = True


@dataclass(frozen=True)
class DisplayConfig:
    """Configuration for CLI display.

    Attributes:
        use_colors: Whether to use colored output
        use_panels: Whether to use rich panels
        show_timestamps: Whether to show timestamps
        verbose: Whether to show verbose output
    """
    use_colors: bool = True
    use_panels: bool = True
    show_timestamps: bool = True
    verbose: bool = False


@dataclass(frozen=True)
class CLIServiceConfig:
    """Main configuration for the CLI orchestrator service.

    Attributes:
        workflow: Workflow settings
        display: Display settings
        default_sport: Default sport ('nfl' or 'nba')
        enabled_sports: List of enabled sports
        fixed_bet_amount: Fixed amount per bet for calculations
    """
    workflow: WorkflowConfig = field(default_factory=WorkflowConfig)
    display: DisplayConfig = field(default_factory=DisplayConfig)
    default_sport: str = "nfl"
    enabled_sports: tuple = ("nfl", "nba")
    fixed_bet_amount: float = 100.0


def get_default_config() -> CLIServiceConfig:
    """Get default CLI service configuration.

    Returns:
        CLIServiceConfig with default settings
    """
    return CLIServiceConfig()


def get_quiet_config() -> CLIServiceConfig:
    """Get configuration for quiet/non-interactive mode.

    Returns:
        CLIServiceConfig with minimal output
    """
    return CLIServiceConfig(
        workflow=WorkflowConfig(confirm_actions=False),
        display=DisplayConfig(use_panels=False, verbose=False),
    )


def get_verbose_config() -> CLIServiceConfig:
    """Get configuration for verbose output.

    Returns:
        CLIServiceConfig with verbose output
    """
    return CLIServiceConfig(
        display=DisplayConfig(verbose=True, show_timestamps=True),
    )
