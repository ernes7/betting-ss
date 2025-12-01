"""Unit tests for prediction service configuration."""

import pytest

from services.prediction import (
    PredictionServiceConfig,
    EVConfig,
    AIConfig,
    OddsFilterConfig,
    get_default_config,
    get_ev_only_config,
    get_aggressive_config,
    get_conservative_config,
)


class TestEVConfig:
    """Tests for EVConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = EVConfig()

        assert config.conservative_adjustment == 0.85
        assert config.min_ev_threshold == 0.0
        assert config.top_n_bets == 5
        assert config.deduplicate_players is True
        assert config.max_receivers_per_team == 1
        assert config.min_games_required == 3

    def test_custom_values(self):
        """Test custom configuration values."""
        config = EVConfig(
            conservative_adjustment=0.90,
            min_ev_threshold=2.0,
            top_n_bets=10,
        )

        assert config.conservative_adjustment == 0.90
        assert config.min_ev_threshold == 2.0
        assert config.top_n_bets == 10

    def test_frozen_config(self):
        """Test that config is immutable."""
        config = EVConfig()

        with pytest.raises(AttributeError):
            config.conservative_adjustment = 0.90


class TestAIConfig:
    """Tests for AIConfig dataclass."""

    def test_default_values(self):
        """Test default AI configuration values."""
        config = AIConfig()

        assert config.model == "claude-sonnet-4-5-20250929"
        assert config.max_tokens == 2048
        assert config.rate_limit_seconds == 60
        assert config.input_cost_per_million == 3.0
        assert config.output_cost_per_million == 15.0

    def test_custom_model(self):
        """Test custom model configuration."""
        config = AIConfig(model="claude-3-opus-20240229")

        assert config.model == "claude-3-opus-20240229"


class TestOddsFilterConfig:
    """Tests for OddsFilterConfig dataclass."""

    def test_default_values(self):
        """Test default odds filter values."""
        config = OddsFilterConfig()

        assert config.min_odds == -150
        assert config.max_odds == 199

    def test_custom_range(self):
        """Test custom odds range."""
        config = OddsFilterConfig(min_odds=-200, max_odds=300)

        assert config.min_odds == -200
        assert config.max_odds == 300


class TestPredictionServiceConfig:
    """Tests for PredictionServiceConfig dataclass."""

    def test_default_values(self):
        """Test default service configuration."""
        config = PredictionServiceConfig()

        assert isinstance(config.ev_config, EVConfig)
        assert isinstance(config.ai_config, AIConfig)
        assert isinstance(config.odds_filter, OddsFilterConfig)
        assert config.use_dual_predictions is True
        assert config.skip_existing is True

    def test_data_root_template(self):
        """Test data root path template."""
        config = PredictionServiceConfig()

        assert "{sport}" in config.data_root
        assert config.data_root.format(sport="nfl") == "nfl/data/predictions"


class TestConfigFactories:
    """Tests for configuration factory functions."""

    def test_get_default_config(self):
        """Test default config factory."""
        config = get_default_config()

        assert isinstance(config, PredictionServiceConfig)
        assert config.use_dual_predictions is True

    def test_get_ev_only_config(self):
        """Test EV-only config factory."""
        config = get_ev_only_config()

        assert config.use_dual_predictions is False

    def test_get_aggressive_config(self):
        """Test aggressive config factory."""
        config = get_aggressive_config()

        assert config.ev_config.conservative_adjustment == 0.90
        assert config.ev_config.min_ev_threshold == -2.0
        assert config.ev_config.top_n_bets == 10
        assert config.ev_config.max_receivers_per_team == 2

    def test_get_conservative_config(self):
        """Test conservative config factory."""
        config = get_conservative_config()

        assert config.ev_config.conservative_adjustment == 0.80
        assert config.ev_config.min_ev_threshold == 3.0
        assert config.ev_config.top_n_bets == 3
        assert config.ev_config.max_receivers_per_team == 1
