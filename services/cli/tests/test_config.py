"""Unit tests for CLI service configuration."""

import pytest

from services.cli import (
    CLIServiceConfig,
    WorkflowConfig,
    DisplayConfig,
    get_default_config,
    get_quiet_config,
    get_verbose_config,
)


class TestWorkflowConfig:
    """Tests for WorkflowConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = WorkflowConfig()

        assert config.skip_existing is True
        assert config.save_results is True
        assert config.show_progress is True
        assert config.confirm_actions is True

    def test_custom_values(self):
        """Test custom configuration values."""
        config = WorkflowConfig(
            skip_existing=False,
            confirm_actions=False,
        )

        assert config.skip_existing is False
        assert config.confirm_actions is False


class TestDisplayConfig:
    """Tests for DisplayConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = DisplayConfig()

        assert config.use_colors is True
        assert config.use_panels is True
        assert config.show_timestamps is True
        assert config.verbose is False

    def test_custom_values(self):
        """Test custom configuration values."""
        config = DisplayConfig(
            use_colors=False,
            verbose=True,
        )

        assert config.use_colors is False
        assert config.verbose is True


class TestCLIServiceConfig:
    """Tests for CLIServiceConfig dataclass."""

    def test_default_values(self):
        """Test default service configuration."""
        config = CLIServiceConfig()

        assert isinstance(config.workflow, WorkflowConfig)
        assert isinstance(config.display, DisplayConfig)
        assert config.default_sport == "nfl"
        assert "nfl" in config.enabled_sports
        assert "nba" in config.enabled_sports
        assert config.fixed_bet_amount == 100.0

    def test_custom_sport(self):
        """Test custom sport configuration."""
        config = CLIServiceConfig(default_sport="nba")

        assert config.default_sport == "nba"


class TestConfigFactories:
    """Tests for configuration factory functions."""

    def test_get_default_config(self):
        """Test default config factory."""
        config = get_default_config()

        assert isinstance(config, CLIServiceConfig)
        assert config.workflow.confirm_actions is True

    def test_get_quiet_config(self):
        """Test quiet config factory."""
        config = get_quiet_config()

        assert config.workflow.confirm_actions is False
        assert config.display.use_panels is False

    def test_get_verbose_config(self):
        """Test verbose config factory."""
        config = get_verbose_config()

        assert config.display.verbose is True
        assert config.display.show_timestamps is True
