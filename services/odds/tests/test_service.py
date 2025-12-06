"""Unit tests for OddsService."""

import json
import pytest
from pathlib import Path

from services.odds import OddsService, OddsServiceConfig
from shared.errors import DataNotFoundError


class TestOddsServiceInit:
    """Tests for OddsService initialization."""

    def test_init_with_config(self, test_odds_config):
        """Test initialization with config."""
        service = OddsService(sport="nfl", config=test_odds_config)

        assert service.sport == "nfl"
        assert service.config == test_odds_config
        assert service.scraper is not None

    def test_init_requires_config(self):
        """Test that initialization requires config parameter."""
        # OddsService now requires config - it's a sport-agnostic black box
        with pytest.raises(TypeError):
            OddsService(sport="nfl")  # Missing config

    def test_init_normalizes_sport(self, test_odds_config):
        """Test that sport name is normalized to lowercase."""
        service = OddsService(sport="NFL", config=test_odds_config)
        assert service.sport == "nfl"

        service = OddsService(sport="Nfl", config=test_odds_config)
        assert service.sport == "nfl"


class TestOddsServiceSave:
    """Tests for OddsService.save_odds()."""

    def test_save_odds_basic(self, odds_service, sample_odds_data):
        """Test basic save functionality - creates directory with CSV files."""
        game_dir = odds_service.save_odds(sample_odds_data)

        assert game_dir.exists()
        assert game_dir.is_dir()
        assert game_dir.name == "dal_nyg"
        assert "2024-12-01" in str(game_dir)

        # Verify CSV files were created
        assert (game_dir / "game_lines.csv").exists()
        assert (game_dir / "player_props.csv").exists()

    def test_save_odds_creates_directory(self, odds_service, sample_odds_data):
        """Test that save creates necessary directories."""
        game_dir = odds_service.save_odds(sample_odds_data)

        assert game_dir.parent.exists()
        assert game_dir.parent.name == "2024-12-01"

    def test_save_odds_with_explicit_params(self, odds_service, sample_odds_data):
        """Test save with explicit game_date and team params."""
        game_dir = odds_service.save_odds(
            sample_odds_data,
            game_date="2024-12-15",
            home_team="phi",
            away_team="was"
        )

        assert game_dir.is_dir()
        assert game_dir.name == "phi_was"
        assert "2024-12-15" in str(game_dir)

    def test_save_odds_overwrites_existing(self, odds_service, sample_odds_data):
        """Test that saving overwrites existing CSV files."""
        import pandas as pd

        # Save first time
        game_dir = odds_service.save_odds(sample_odds_data)
        original_df = pd.read_csv(game_dir / "game_lines.csv")
        original_ml = original_df.iloc[0]["ml_home"]

        # Modify and save again
        sample_odds_data["game_lines"]["moneyline"]["home"] = -200
        game_dir2 = odds_service.save_odds(sample_odds_data)

        assert game_dir == game_dir2
        new_df = pd.read_csv(game_dir / "game_lines.csv")
        new_ml = new_df.iloc[0]["ml_home"]
        assert original_ml != new_ml
        assert new_ml == -200


class TestOddsServiceLoad:
    """Tests for OddsService.load_odds()."""

    def test_load_odds_success(self, odds_service, sample_odds_data):
        """Test loading existing odds."""
        # First save
        odds_service.save_odds(sample_odds_data)

        # Then load
        loaded = odds_service.load_odds("2024-12-01", "dal", "nyg")

        assert loaded["sport"] == "nfl"
        assert loaded["teams"]["home"]["abbr"] == "DAL"

    def test_load_odds_not_found(self, odds_service):
        """Test loading non-existent odds raises error."""
        with pytest.raises(DataNotFoundError) as exc_info:
            odds_service.load_odds("2024-12-01", "dal", "nyg")

        assert "dal" in str(exc_info.value).lower()
        assert "nyg" in str(exc_info.value).lower()

    def test_load_odds_case_insensitive(self, odds_service, sample_odds_data):
        """Test that team abbreviations are case-insensitive."""
        odds_service.save_odds(sample_odds_data)

        # Load with uppercase
        loaded = odds_service.load_odds("2024-12-01", "DAL", "NYG")
        assert loaded is not None

    def test_load_odds_safe_returns_none(self, odds_service):
        """Test load_odds_safe returns None for missing file."""
        result = odds_service.load_odds_safe("2024-12-01", "dal", "nyg")
        assert result is None

    def test_load_odds_safe_returns_data(self, odds_service, sample_odds_data):
        """Test load_odds_safe returns data when file exists."""
        odds_service.save_odds(sample_odds_data)

        result = odds_service.load_odds_safe("2024-12-01", "dal", "nyg")
        assert result is not None
        assert result["sport"] == "nfl"


class TestOddsServiceQuery:
    """Tests for OddsService query methods."""

    def test_odds_exist_true(self, odds_service, sample_odds_data):
        """Test odds_exist returns True when file exists."""
        odds_service.save_odds(sample_odds_data)

        assert odds_service.odds_exist("2024-12-01", "dal", "nyg") is True

    def test_odds_exist_false(self, odds_service):
        """Test odds_exist returns False when file doesn't exist."""
        assert odds_service.odds_exist("2024-12-01", "dal", "nyg") is False

    def test_get_available_dates_empty(self, odds_service):
        """Test get_available_dates with no data."""
        dates = odds_service.get_available_dates()
        assert dates == []

    def test_get_available_dates_with_data(self, odds_service, sample_odds_data):
        """Test get_available_dates with saved data."""
        # Save odds for multiple dates
        odds_service.save_odds(sample_odds_data, game_date="2024-12-01")

        sample_odds_data["game_date"] = "2024-12-08T18:00:00Z"
        odds_service.save_odds(sample_odds_data, game_date="2024-12-08")

        dates = odds_service.get_available_dates()

        assert len(dates) == 2
        assert "2024-12-08" in dates
        assert "2024-12-01" in dates
        # Most recent first
        assert dates[0] == "2024-12-08"

    def test_get_odds_files_for_date(self, odds_service, sample_odds_data):
        """Test getting odds files for a specific date."""
        odds_service.save_odds(sample_odds_data)

        files = odds_service.get_odds_files_for_date("2024-12-01")

        assert len(files) == 1
        game_dir, display_name = files[0]
        assert game_dir.name == "dal_nyg"
        assert game_dir.is_dir()
        assert display_name == "DAL vs NYG"

    def test_get_odds_files_for_date_empty(self, odds_service):
        """Test getting odds files for date with no data."""
        files = odds_service.get_odds_files_for_date("2024-12-01")
        assert files == []

    def test_get_all_odds_for_date(self, odds_service, sample_odds_data):
        """Test getting all odds for a date."""
        # Save multiple games
        odds_service.save_odds(sample_odds_data)

        sample_odds_data["teams"]["home"]["abbr"] = "PHI"
        sample_odds_data["teams"]["away"]["abbr"] = "WAS"
        odds_service.save_odds(sample_odds_data, home_team="phi", away_team="was")

        all_odds = odds_service.get_all_odds_for_date("2024-12-01")

        assert len(all_odds) == 2


class TestOddsServiceExtract:
    """Tests for OddsService extraction methods."""

    def test_get_game_lines(self, odds_service, sample_odds_data):
        """Test extracting game lines from odds data."""
        game_lines = odds_service.get_game_lines(sample_odds_data)

        assert game_lines is not None
        assert "moneyline" in game_lines
        assert game_lines["moneyline"]["home"] == -150

    def test_get_player_props(self, odds_service, sample_odds_data):
        """Test extracting player props from odds data."""
        player_props = odds_service.get_player_props(sample_odds_data)

        assert player_props is not None
        assert len(player_props) == 1
        assert player_props[0]["player"] == "Dak Prescott"

    def test_to_model(self, odds_service, sample_odds_data):
        """Test converting to Odds model."""
        odds_model = odds_service.to_model(sample_odds_data)

        assert odds_model.sport == "nfl"
        assert odds_model.home_team == "Dallas Cowboys"


class TestOddsServiceFromData:
    """Tests for OddsService.fetch_from_data()."""

    def test_fetch_from_data(self, odds_service, sample_stadium_data):
        """Test fetching odds from stadium data."""
        odds = odds_service.fetch_from_data(sample_stadium_data)

        assert odds["sport"] == "nfl"
        assert odds["teams"]["home"]["name"] == "Dallas Cowboys"
        assert "game_lines" in odds
        assert "player_props" in odds

    def test_fetch_from_data_extracts_game_lines(self, odds_service, sample_stadium_data):
        """Test that game lines are extracted correctly."""
        odds = odds_service.fetch_from_data(sample_stadium_data)

        game_lines = odds["game_lines"]
        assert game_lines["moneyline"]["home"] == -150
        assert game_lines["moneyline"]["away"] == 130
        assert game_lines["spread"]["home"] == -3.5
        assert game_lines["total"]["line"] == 47.5

    def test_fetch_from_data_extracts_player_props(self, odds_service, sample_stadium_data):
        """Test that player props are extracted correctly."""
        odds = odds_service.fetch_from_data(sample_stadium_data)

        player_props = odds["player_props"]
        assert len(player_props) > 0

        # Find Dak Prescott
        dak_props = next((p for p in player_props if p["player"] == "Dak Prescott"), None)
        assert dak_props is not None
        assert len(dak_props["props"]) > 0


class TestOddsServiceSchedule:
    """Tests for OddsService schedule methods."""

    def test_save_schedule(self, odds_service, sample_schedule_data):
        """Test saving schedule to CSV."""
        schedule_path = odds_service.save_schedule(sample_schedule_data)

        assert schedule_path.exists()
        assert schedule_path.name == "schedule.csv"

    def test_save_schedule_custom_filename(self, odds_service, sample_schedule_data):
        """Test saving schedule with custom filename."""
        schedule_path = odds_service.save_schedule(sample_schedule_data, filename="upcoming.csv")

        assert schedule_path.exists()
        assert schedule_path.name == "upcoming.csv"

    def test_load_schedule(self, odds_service, sample_schedule_data):
        """Test loading schedule from CSV."""
        # First save
        odds_service.save_schedule(sample_schedule_data)

        # Then load
        loaded = odds_service.load_schedule()

        assert len(loaded) == 3
        assert loaded[0]["event_id"] == "28937481"
        assert loaded[0]["matchup"] == "NYG @ DAL"

    def test_load_schedule_not_found(self, odds_service):
        """Test loading non-existent schedule raises error."""
        with pytest.raises(DataNotFoundError) as exc_info:
            odds_service.load_schedule()

        assert "Schedule not found" in str(exc_info.value)

    def test_save_and_load_schedule_roundtrip(self, odds_service, sample_schedule_data):
        """Test that save/load preserves data."""
        # Save
        odds_service.save_schedule(sample_schedule_data)

        # Load
        loaded = odds_service.load_schedule()

        # Verify all records
        assert len(loaded) == len(sample_schedule_data)
        for original, loaded_item in zip(sample_schedule_data, loaded):
            assert loaded_item["event_id"] == original["event_id"]
            assert loaded_item["matchup"] == original["matchup"]
            assert loaded_item["start_date"] == original["start_date"]
