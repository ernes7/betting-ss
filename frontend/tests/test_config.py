"""Unit tests for streamlit service configuration."""

import pytest
from pathlib import Path

from frontend import (
    StreamlitServiceConfig,
    DisplayConfig,
    DataPathConfig,
    ThemeConfig,
    get_default_config,
)
from frontend.config import get_nfl_only_config, get_nba_only_config


class TestDisplayConfig:
    """Tests for DisplayConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = DisplayConfig()

        assert config.page_title == "Sports Betting Analytics"
        assert config.page_icon == "🎯"
        assert config.layout == "wide"
        assert config.cards_per_row == 3
        assert config.fixed_bet_amount == 100.0

    def test_custom_values(self):
        """Test custom configuration values."""
        config = DisplayConfig(
            page_title="My Dashboard",
            cards_per_row=4,
            fixed_bet_amount=50.0,
        )

        assert config.page_title == "My Dashboard"
        assert config.cards_per_row == 4
        assert config.fixed_bet_amount == 50.0


class TestDataPathConfig:
    """Tests for DataPathConfig dataclass."""

    def test_default_values(self):
        """Test default path templates."""
        config = DataPathConfig()

        assert "{sport}" in config.predictions_path
        assert "{sport}" in config.analysis_path
        assert "{sport}" in config.results_path

    def test_get_predictions_dir(self, tmp_path):
        """Test predictions directory path generation."""
        config = DataPathConfig()

        path = config.get_predictions_dir("nfl", tmp_path)

        assert "nfl" in str(path)
        assert "predictions" in str(path)

    def test_get_analysis_dir(self, tmp_path):
        """Test analysis directory path generation."""
        config = DataPathConfig()

        path = config.get_analysis_dir("nba", tmp_path)

        assert "nba" in str(path)
        assert "analysis" in str(path)


class TestThemeConfig:
    """Tests for ThemeConfig dataclass."""

    def test_default_values(self):
        """Test default theme values."""
        config = ThemeConfig()

        assert "#8B5CF6" in config.ai_border_color
        assert "#22C55E" in config.ev_border_color
        assert "#22C55E" in config.profit_positive
        assert "#EF4444" in config.profit_negative


class TestStreamlitServiceConfig:
    """Tests for StreamlitServiceConfig dataclass."""

    def test_default_values(self):
        """Test default service configuration."""
        config = StreamlitServiceConfig()

        assert isinstance(config.display, DisplayConfig)
        assert isinstance(config.paths, DataPathConfig)
        assert isinstance(config.theme, ThemeConfig)
        assert config.default_sport == "nfl"
        assert config.enable_nba is True
        assert config.enable_nfl is True


class TestConfigFactories:
    """Tests for configuration factory functions."""

    def test_get_default_config(self):
        """Test default config factory."""
        config = get_default_config()

        assert isinstance(config, StreamlitServiceConfig)
        assert config.enable_nfl is True
        assert config.enable_nba is True

    def test_get_nfl_only_config(self):
        """Test NFL-only config factory."""
        config = get_nfl_only_config()

        assert config.default_sport == "nfl"
        assert config.enable_nfl is True
        assert config.enable_nba is False

    def test_get_nba_only_config(self):
        """Test NBA-only config factory."""
        config = get_nba_only_config()

        assert config.default_sport == "nba"
        assert config.enable_nfl is False
        assert config.enable_nba is True
