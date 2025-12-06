"""Unit tests for StatsService."""

import pytest
from pathlib import Path

from services.stats import StatsService, StatsServiceConfig
from shared.errors import DataNotFoundError


class TestStatsServiceInit:
    """Tests for StatsService initialization."""

    def test_init_with_config(self, test_stats_config):
        """Test initialization with config."""
        service = StatsService(config=test_stats_config, sport="nfl")

        assert service.config == test_stats_config
        assert service.sport == "nfl"
        assert service.fetcher is not None

    def test_init_normalizes_sport(self, test_stats_config):
        """Test that sport is normalized to lowercase."""
        service = StatsService(config=test_stats_config, sport="NFL")
        assert service.sport == "nfl"

    def test_init_requires_config(self):
        """Test that initialization requires config parameter."""
        # StatsService now requires config - it's a sport-agnostic black box
        with pytest.raises(TypeError):
            StatsService(sport="nfl")  # Missing config


class TestStatsServiceSaveLoad:
    """Tests for save/load operations."""

    def test_save_rankings(self, stats_service, sample_rankings_data):
        """Test saving rankings as CSV files."""
        path = stats_service.save_rankings(sample_rankings_data, date="2024-12-01")

        assert path.exists()
        assert path.is_dir()
        assert path.name == "2024-12-01"
        # Check CSV file was created
        assert (path / "team_offense.csv").exists()

    def test_load_rankings(self, stats_service, sample_rankings_data):
        """Test loading rankings from CSV files."""
        # First save
        stats_service.save_rankings(sample_rankings_data, date="2024-12-01")

        # Then load
        loaded = stats_service.load_rankings("2024-12-01")

        assert "tables" in loaded
        assert "team_offense" in loaded["tables"]
        assert len(loaded["tables"]["team_offense"]) == 2

    def test_load_rankings_not_found(self, stats_service):
        """Test loading non-existent rankings raises error."""
        with pytest.raises(DataNotFoundError) as exc_info:
            stats_service.load_rankings("2099-01-01")

        assert "not found" in str(exc_info.value).lower()

    def test_load_rankings_safe(self, stats_service):
        """Test safe load returns None when not found."""
        result = stats_service.load_rankings_safe("2099-01-01")
        assert result is None

    def test_save_team_profile(self, stats_service, sample_profile_data):
        """Test saving team profile as CSV files."""
        path = stats_service.save_team_profile(
            sample_profile_data,
            team_abbr="dal",
            date="2024-12-01"
        )

        assert path.exists()
        assert path.is_dir()
        assert path.name == "dal"
        # Check CSV files were created
        assert (path / "passing.csv").exists()
        assert (path / "rushing_receiving.csv").exists()

    def test_load_team_profile(self, stats_service, sample_profile_data):
        """Test loading team profile from CSV files."""
        # First save
        stats_service.save_team_profile(
            sample_profile_data,
            team_abbr="dal",
            date="2024-12-01"
        )

        # Then load
        loaded = stats_service.load_team_profile("dal", "2024-12-01")

        assert loaded["team"] == "dal"
        assert "tables" in loaded
        assert "passing" in loaded["tables"]

    def test_load_team_profile_not_found(self, stats_service):
        """Test loading non-existent profile raises error."""
        with pytest.raises(DataNotFoundError):
            stats_service.load_team_profile("xyz", "2024-12-01")


class TestStatsServiceAvailability:
    """Tests for availability checks."""

    def test_rankings_exist(self, stats_service, sample_rankings_data):
        """Test rankings existence check."""
        assert not stats_service.rankings_exist("2024-12-01")

        stats_service.save_rankings(sample_rankings_data, date="2024-12-01")

        assert stats_service.rankings_exist("2024-12-01")

    def test_profile_exists(self, stats_service, sample_profile_data):
        """Test profile existence check."""
        assert not stats_service.profile_exists("dal", "2024-12-01")

        stats_service.save_team_profile(
            sample_profile_data,
            team_abbr="dal",
            date="2024-12-01"
        )

        assert stats_service.profile_exists("dal", "2024-12-01")

    def test_get_available_dates(self, stats_service, sample_rankings_data):
        """Test getting available dates."""
        # Initially empty
        assert stats_service.get_available_dates() == []

        # Add rankings for two dates
        stats_service.save_rankings(sample_rankings_data, date="2024-12-01")
        stats_service.save_rankings(sample_rankings_data, date="2024-12-02")

        dates = stats_service.get_available_dates()
        assert len(dates) == 2
        assert "2024-12-02" in dates  # Most recent first
        assert "2024-12-01" in dates

    def test_get_available_profiles(self, stats_service, sample_profile_data):
        """Test getting available profiles."""
        # Initially empty
        assert stats_service.get_available_profiles("2024-12-01") == []

        # Add profiles
        stats_service.save_team_profile(
            sample_profile_data,
            team_abbr="dal",
            date="2024-12-01"
        )
        stats_service.save_team_profile(
            sample_profile_data,
            team_abbr="nyg",
            date="2024-12-01"
        )

        profiles = stats_service.get_available_profiles("2024-12-01")
        assert len(profiles) == 2
        assert "dal" in profiles
        assert "nyg" in profiles


class TestStatsServiceConfig:
    """Tests for configuration."""

    def test_config_validation(self):
        """Test config validation."""
        config = StatsServiceConfig(
            rankings_url="https://example.com/rankings/",
            rankings_tables={"team_offense": "team_stats"},
        )
        # Should not raise - has required fields
        config.validate()

    def test_config_validation_fails_without_url(self):
        """Test config validation fails without rankings_url."""
        config = StatsServiceConfig(
            rankings_tables={"team_offense": "team_stats"},
        )
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "rankings_url" in str(exc_info.value)

    def test_config_validation_fails_without_tables(self):
        """Test config validation fails without rankings_tables."""
        config = StatsServiceConfig(
            rankings_url="https://example.com/rankings/",
        )
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "rankings_tables" in str(exc_info.value)
