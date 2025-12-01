"""Unit tests for analysis service configuration."""

import pytest

from services.analysis import (
    AnalysisServiceConfig,
    MatchingConfig,
    ProfitConfig,
    get_default_config,
    get_strict_matching_config,
    get_lenient_matching_config,
    get_ev_analysis_config,
)


class TestMatchingConfig:
    """Tests for MatchingConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = MatchingConfig()

        assert config.name_similarity_threshold == 0.85
        assert config.check_all_tables is True
        assert config.normalize_names is True
        assert config.use_nickname_mapping is True

    def test_custom_values(self):
        """Test custom configuration values."""
        config = MatchingConfig(
            name_similarity_threshold=0.90,
            check_all_tables=False,
            normalize_names=False,
            use_nickname_mapping=False,
        )

        assert config.name_similarity_threshold == 0.90
        assert config.check_all_tables is False
        assert config.normalize_names is False
        assert config.use_nickname_mapping is False

    def test_frozen_config(self):
        """Test that config is immutable."""
        config = MatchingConfig()

        with pytest.raises(AttributeError):
            config.name_similarity_threshold = 0.90


class TestProfitConfig:
    """Tests for ProfitConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ProfitConfig()

        assert config.default_stake == 100.0
        assert config.default_odds == -110

    def test_custom_values(self):
        """Test custom configuration values."""
        config = ProfitConfig(
            default_stake=50.0,
            default_odds=-115,
        )

        assert config.default_stake == 50.0
        assert config.default_odds == -115

    def test_frozen_config(self):
        """Test that config is immutable."""
        config = ProfitConfig()

        with pytest.raises(AttributeError):
            config.default_stake = 50.0


class TestAnalysisServiceConfig:
    """Tests for AnalysisServiceConfig dataclass."""

    def test_default_values(self):
        """Test default service configuration."""
        config = AnalysisServiceConfig()

        assert isinstance(config.matching_config, MatchingConfig)
        assert isinstance(config.profit_config, ProfitConfig)
        assert "{sport}" in config.data_root
        assert config.analysis_type == "analysis"
        assert config.skip_existing is True
        assert config.include_pending is False

    def test_data_root_template(self):
        """Test data root path template."""
        config = AnalysisServiceConfig()

        assert config.data_root.format(sport="nfl") == "nfl/data/analysis"
        assert config.data_root.format(sport="nba") == "nba/data/analysis"

    def test_custom_analysis_type(self):
        """Test custom analysis type configuration."""
        config = AnalysisServiceConfig(analysis_type="analysis_ev")

        assert config.analysis_type == "analysis_ev"


class TestConfigFactories:
    """Tests for configuration factory functions."""

    def test_get_default_config(self):
        """Test default config factory."""
        config = get_default_config()

        assert isinstance(config, AnalysisServiceConfig)
        assert config.matching_config.name_similarity_threshold == 0.85
        assert config.skip_existing is True

    def test_get_strict_matching_config(self):
        """Test strict matching config factory."""
        config = get_strict_matching_config()

        assert config.matching_config.name_similarity_threshold == 0.90
        assert config.matching_config.check_all_tables is False

    def test_get_lenient_matching_config(self):
        """Test lenient matching config factory."""
        config = get_lenient_matching_config()

        assert config.matching_config.name_similarity_threshold == 0.75
        assert config.matching_config.check_all_tables is True

    def test_get_ev_analysis_config(self):
        """Test EV analysis config factory."""
        config = get_ev_analysis_config()

        assert config.analysis_type == "analysis_ev"
