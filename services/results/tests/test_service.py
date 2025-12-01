"""Unit tests for ResultsService."""

import pytest
import tempfile
import os
import json
from unittest.mock import MagicMock, patch

from services.results import ResultsService, ResultsServiceConfig, get_default_config
from shared.errors import ResultsFetchError


class TestResultsServiceInit:
    """Tests for ResultsService initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default configuration."""
        service = ResultsService(sport="nfl")

        assert service.sport == "nfl"
        assert service.config is not None
        assert service.fetcher is not None
        assert service.error_handler is not None

    def test_init_normalizes_sport(self):
        """Test that sport is normalized to lowercase."""
        service = ResultsService(sport="NFL")
        assert service.sport == "nfl"

    def test_init_with_custom_config(self, test_results_config):
        """Test initialization with custom configuration."""
        service = ResultsService(sport="nfl", config=test_results_config)

        assert service.config == test_results_config

    def test_results_dir_property(self, test_results_config):
        """Test that results_dir property is formatted correctly."""
        service = ResultsService(sport="nfl", config=test_results_config)

        assert "nfl" in service.results_dir


class TestResultsServiceBuildUrl:
    """Tests for URL building."""

    def test_build_url_nfl(self):
        """Test building NFL boxscore URL."""
        service = ResultsService(sport="nfl")

        url = service._build_url(date="20241124", home_abbr="DAL", game_id=None)

        assert "pro-football-reference.com" in url
        assert "20241124" in url
        assert "dal" in url

    def test_build_url_nfl_missing_params(self):
        """Test building NFL URL with missing params raises error."""
        service = ResultsService(sport="nfl")

        with pytest.raises(ResultsFetchError) as exc_info:
            service._build_url(date="20241124", home_abbr=None, game_id=None)

        assert "requires date and home_abbr" in str(exc_info.value)

    def test_build_url_nba(self):
        """Test building NBA boxscore URL."""
        service = ResultsService(sport="nba")

        url = service._build_url(date=None, home_abbr=None, game_id="202411240DAL")

        assert "basketball-reference.com" in url
        assert "202411240DAL" in url

    def test_build_url_nba_missing_params(self):
        """Test building NBA URL with missing params raises error."""
        service = ResultsService(sport="nba")

        with pytest.raises(ResultsFetchError) as exc_info:
            service._build_url(date=None, home_abbr=None, game_id=None)

        assert "requires game_id" in str(exc_info.value)


class TestResultsServiceSaveLoad:
    """Tests for saving and loading results."""

    def test_save_and_load_result(self, sample_result_data):
        """Test saving and loading a result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ResultsServiceConfig(data_root=tmpdir)
            service = ResultsService(sport="nfl", config=config)

            game_key = "2024-11-24_nyg_dal"

            # Save
            filepath = service.save_result(sample_result_data, game_key)

            assert os.path.exists(filepath)
            assert filepath.endswith(".json")

            # Load
            loaded = service.load_result(game_key)

            assert loaded is not None
            assert loaded["winner"] == sample_result_data["winner"]
            assert loaded["final_score"] == sample_result_data["final_score"]

    def test_load_nonexistent_result(self):
        """Test loading a result that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ResultsServiceConfig(data_root=tmpdir)
            service = ResultsService(sport="nfl", config=config)

            result = service.load_result("2024-11-24_xxx_yyy")

            assert result is None

    def test_list_results_empty(self):
        """Test listing results for a date with no results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ResultsServiceConfig(data_root=tmpdir)
            service = ResultsService(sport="nfl", config=config)

            results = service.list_results("2024-11-24")

            assert results == []

    def test_list_results_multiple(self, sample_result_data):
        """Test listing multiple results for a date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ResultsServiceConfig(data_root=tmpdir)
            service = ResultsService(sport="nfl", config=config)

            # Save multiple results
            service.save_result(sample_result_data, "2024-11-24_nyg_dal")
            service.save_result(sample_result_data, "2024-11-24_phi_was")

            results = service.list_results("2024-11-24")

            assert len(results) == 2
            assert "2024-11-24_nyg_dal" in results
            assert "2024-11-24_phi_was" in results


class TestResultsServiceFetch:
    """Tests for fetching results."""

    def test_fetch_game_result_with_url(self, sample_result_data):
        """Test fetching game result with direct URL."""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_boxscore.return_value = sample_result_data

        service = ResultsService(sport="nfl", fetcher=mock_fetcher)

        result = service.fetch_game_result(
            boxscore_url="https://example.com/boxscore"
        )

        assert result == sample_result_data
        mock_fetcher.fetch_boxscore.assert_called_once()

    def test_fetch_game_result_builds_url(self, sample_result_data):
        """Test fetching game result builds URL from params."""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_boxscore.return_value = sample_result_data

        service = ResultsService(sport="nfl", fetcher=mock_fetcher)

        result = service.fetch_game_result(date="20241124", home_abbr="dal")

        assert result == sample_result_data
        call_args = mock_fetcher.fetch_boxscore.call_args[0][0]
        assert "20241124" in call_args
        assert "dal" in call_args


class TestResultsServiceFetchForDate:
    """Tests for fetching results for a date."""

    def test_fetch_results_for_date_success(self, sample_result_data):
        """Test fetching results for multiple games."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ResultsServiceConfig(data_root=tmpdir)
            mock_fetcher = MagicMock()
            mock_fetcher.fetch_boxscore.return_value = sample_result_data

            service = ResultsService(
                sport="nfl",
                config=config,
                fetcher=mock_fetcher,
            )

            games = [
                {"home_abbr": "dal", "away_abbr": "nyg"},
                {"home_abbr": "phi", "away_abbr": "was"},
            ]

            summary = service.fetch_results_for_date("2024-11-24", games)

            assert summary["fetched_count"] == 2
            assert summary["failed_count"] == 0
            assert len(summary["results"]) == 2

    def test_fetch_results_for_date_skips_existing(self, sample_result_data):
        """Test that existing results are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ResultsServiceConfig(data_root=tmpdir)
            mock_fetcher = MagicMock()
            mock_fetcher.fetch_boxscore.return_value = sample_result_data

            service = ResultsService(
                sport="nfl",
                config=config,
                fetcher=mock_fetcher,
            )

            # Pre-save one result
            service.save_result(sample_result_data, "2024-11-24_nyg_dal")

            games = [
                {"home_abbr": "dal", "away_abbr": "nyg"},  # Already exists
                {"home_abbr": "phi", "away_abbr": "was"},  # New
            ]

            summary = service.fetch_results_for_date("2024-11-24", games)

            assert summary["fetched_count"] == 1
            assert summary["skipped_count"] == 1

    def test_fetch_results_for_date_handles_errors(self):
        """Test that errors are captured but don't stop processing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ResultsServiceConfig(data_root=tmpdir)
            mock_fetcher = MagicMock()
            mock_fetcher.fetch_boxscore.side_effect = Exception("Network error")

            service = ResultsService(
                sport="nfl",
                config=config,
                fetcher=mock_fetcher,
            )

            games = [
                {"home_abbr": "dal", "away_abbr": "nyg"},
                {"home_abbr": "phi", "away_abbr": "was"},
            ]

            summary = service.fetch_results_for_date("2024-11-24", games)

            assert summary["fetched_count"] == 0
            assert summary["failed_count"] == 2
            assert len(summary["errors"]) == 2


class TestResultsServiceNBA:
    """Tests for NBA-specific service functionality."""

    def test_nba_service_init(self):
        """Test NBA service initialization."""
        service = ResultsService(sport="nba")

        assert service.sport == "nba"
        assert "line_score" in service.config.result_tables

    def test_nba_fetch_results_for_date(self, sample_result_data):
        """Test fetching NBA results uses game_id."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ResultsServiceConfig(
                data_root=tmpdir,
                result_tables={"line_score": "line_score"},
            )
            mock_fetcher = MagicMock()
            mock_fetcher.fetch_boxscore.return_value = sample_result_data

            service = ResultsService(
                sport="nba",
                config=config,
                fetcher=mock_fetcher,
            )

            games = [
                {"game_id": "202411240DAL"},
            ]

            summary = service.fetch_results_for_date("2024-11-24", games)

            assert summary["fetched_count"] == 1
            call_args = mock_fetcher.fetch_boxscore.call_args[0][0]
            assert "202411240DAL" in call_args
