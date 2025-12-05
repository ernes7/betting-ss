"""Unit tests for StatsService."""

import pytest
from pathlib import Path

from services.stats import StatsService, StatsServiceConfig, get_default_config
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

    def test_init_with_default_config(self):
        """Test initialization with default config."""
        service = StatsService(sport="nfl")

        assert service.sport == "nfl"
        assert service.config is not None
        assert "team_offense" in service.config.rankings_tables


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

    def test_default_nfl_config(self):
        """Test default NFL configuration."""
        config = get_default_config("nfl")

        assert "team_offense" in config.rankings_tables
        assert "team_defense" in config.defensive_tables
        assert "passing" in config.profile_tables

    def test_default_unknown_sport(self):
        """Test default config for unknown sport."""
        config = get_default_config("unknown")

        assert config.rankings_tables == {}
        assert config.defensive_tables == {}
