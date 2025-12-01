"""Unit tests for AnalysisService."""

import pytest
import tempfile
import os
from unittest.mock import MagicMock, patch

from services.analysis import (
    AnalysisService,
    AnalysisServiceConfig,
    BetChecker,
    get_default_config,
)


class TestAnalysisServiceInit:
    """Tests for AnalysisService initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default configuration."""
        with patch("services.analysis.service.AnalysisRepository"):
            service = AnalysisService(sport="nfl")

        assert service.sport == "nfl"
        assert service.config is not None
        assert service.bet_checker is not None

    def test_init_normalizes_sport(self):
        """Test that sport is normalized to lowercase."""
        with patch("services.analysis.service.AnalysisRepository"):
            service = AnalysisService(sport="NFL")

        assert service.sport == "nfl"

    def test_init_with_custom_config(self, test_analysis_config):
        """Test initialization with custom configuration."""
        with patch("services.analysis.service.AnalysisRepository"):
            service = AnalysisService(
                sport="nfl",
                config=test_analysis_config,
            )

        assert service.config == test_analysis_config

    def test_init_with_injected_bet_checker(self):
        """Test initialization with injected bet checker."""
        custom_checker = BetChecker()

        with patch("services.analysis.service.AnalysisRepository"):
            service = AnalysisService(
                sport="nfl",
                bet_checker=custom_checker,
            )

        assert service.bet_checker == custom_checker

    def test_analysis_dir_property(self, test_analysis_config):
        """Test analysis directory property."""
        with patch("services.analysis.service.AnalysisRepository"):
            service = AnalysisService(
                sport="nfl",
                config=test_analysis_config,
            )

        assert "nfl" in service.analysis_dir


class TestAnalysisServiceAnalyzeGame:
    """Tests for analyze_game method."""

    def test_analyze_game_success(
        self, test_analysis_config, sample_prediction_data, sample_result_data
    ):
        """Test successful game analysis."""
        with patch("services.analysis.service.AnalysisRepository"):
            service = AnalysisService(
                sport="nfl",
                config=test_analysis_config,
            )

        result = service.analyze_game(
            game_date="2024-11-24",
            away_team="nyg",
            home_team="dal",
            prediction_data=sample_prediction_data,
            result_data=sample_result_data,
        )

        assert result["sport"] == "nfl"
        assert result["game_date"] == "2024-11-24"
        assert result["away_team"] == "nyg"
        assert result["home_team"] == "dal"
        assert "bet_results" in result
        assert "summary" in result
        assert "analyzed_at" in result

    def test_analyze_game_winning_bets(
        self, test_analysis_config, sample_prediction_data, sample_result_data
    ):
        """Test analysis with winning bets."""
        with patch("services.analysis.service.AnalysisRepository"):
            service = AnalysisService(
                sport="nfl",
                config=test_analysis_config,
            )

        result = service.analyze_game(
            game_date="2024-11-24",
            away_team="nyg",
            home_team="dal",
            prediction_data=sample_prediction_data,
            result_data=sample_result_data,
        )

        summary = result["summary"]
        assert summary["bets_won"] == 2
        assert summary["bets_lost"] == 0
        assert summary["total_profit"] > 0

    def test_analyze_game_losing_bets(
        self, test_analysis_config, sample_prediction_data, sample_result_data_losing
    ):
        """Test analysis with losing bets."""
        with patch("services.analysis.service.AnalysisRepository"):
            service = AnalysisService(
                sport="nfl",
                config=test_analysis_config,
            )

        result = service.analyze_game(
            game_date="2024-11-24",
            away_team="nyg",
            home_team="dal",
            prediction_data=sample_prediction_data,
            result_data=sample_result_data_losing,
        )

        summary = result["summary"]
        assert summary["bets_lost"] == 2
        assert summary["total_profit"] < 0

    def test_analyze_game_includes_final_score(
        self, test_analysis_config, sample_prediction_data, sample_result_data
    ):
        """Test that analysis includes final score."""
        with patch("services.analysis.service.AnalysisRepository"):
            service = AnalysisService(
                sport="nfl",
                config=test_analysis_config,
            )

        result = service.analyze_game(
            game_date="2024-11-24",
            away_team="nyg",
            home_team="dal",
            prediction_data=sample_prediction_data,
            result_data=sample_result_data,
        )

        assert "final_score" in result
        assert result["final_score"]["home"] == 27
        assert result["final_score"]["away"] == 20


class TestAnalysisServiceSaveLoad:
    """Tests for save and load methods."""

    def test_save_and_load_analysis(self, sample_analysis_result):
        """Test saving and loading analysis."""
        mock_repo = MagicMock()
        mock_repo.save_analysis.return_value = True
        mock_repo.load_analysis.return_value = sample_analysis_result

        with patch("services.analysis.service.AnalysisRepository", return_value=mock_repo):
            service = AnalysisService(sport="nfl")

        # Save
        service.save_analysis(
            sample_analysis_result,
            game_date="2024-11-24",
            away_team="nyg",
            home_team="dal",
        )

        mock_repo.save_analysis.assert_called_once()

        # Load
        loaded = service.load_analysis(
            game_date="2024-11-24",
            away_team="nyg",
            home_team="dal",
        )

        assert loaded == sample_analysis_result
        mock_repo.load_analysis.assert_called_once()

    def test_load_nonexistent_analysis(self):
        """Test loading analysis that doesn't exist."""
        mock_repo = MagicMock()
        mock_repo.load_analysis.return_value = None

        with patch("services.analysis.service.AnalysisRepository", return_value=mock_repo):
            service = AnalysisService(sport="nfl")

        result = service.load_analysis(
            game_date="2024-11-24",
            away_team="xxx",
            home_team="yyy",
        )

        assert result is None


class TestAnalysisServiceBatch:
    """Tests for batch analysis."""

    def test_analyze_games_batch_success(
        self, test_analysis_config, sample_prediction_data, sample_result_data
    ):
        """Test batch analysis with multiple games."""
        mock_repo = MagicMock()
        mock_repo.save_analysis.return_value = True
        mock_repo.analysis_exists.return_value = False

        with patch("services.analysis.service.AnalysisRepository", return_value=mock_repo):
            service = AnalysisService(
                sport="nfl",
                config=test_analysis_config,
            )

        games = [
            {"away_team": "nyg", "home_team": "dal"},
            {"away_team": "phi", "home_team": "was"},
        ]

        def mock_pred_loader(date, game):
            return sample_prediction_data

        def mock_result_loader(date, game):
            return sample_result_data

        summary = service.analyze_games_batch(
            game_date="2024-11-24",
            games=games,
            prediction_loader=mock_pred_loader,
            result_loader=mock_result_loader,
        )

        assert summary["success"] is True
        assert summary["games_analyzed"] == 2
        assert summary["games_skipped"] == 0

    def test_analyze_games_batch_missing_predictions(self, test_analysis_config, sample_result_data):
        """Test batch analysis with missing predictions."""
        mock_repo = MagicMock()
        mock_repo.analysis_exists.return_value = False

        with patch("services.analysis.service.AnalysisRepository", return_value=mock_repo):
            service = AnalysisService(
                sport="nfl",
                config=test_analysis_config,
            )

        games = [
            {"away_team": "nyg", "home_team": "dal"},
        ]

        def mock_pred_loader(date, game):
            return None  # No prediction

        def mock_result_loader(date, game):
            return sample_result_data

        summary = service.analyze_games_batch(
            game_date="2024-11-24",
            games=games,
            prediction_loader=mock_pred_loader,
            result_loader=mock_result_loader,
        )

        assert summary["games_skipped"] == 1
        assert summary["games_analyzed"] == 0

    def test_analyze_games_batch_missing_results(
        self, test_analysis_config, sample_prediction_data
    ):
        """Test batch analysis with missing results."""
        mock_repo = MagicMock()
        mock_repo.analysis_exists.return_value = False

        with patch("services.analysis.service.AnalysisRepository", return_value=mock_repo):
            service = AnalysisService(
                sport="nfl",
                config=test_analysis_config,
            )

        games = [
            {"away_team": "nyg", "home_team": "dal"},
        ]

        def mock_pred_loader(date, game):
            return sample_prediction_data

        def mock_result_loader(date, game):
            return None  # No results

        summary = service.analyze_games_batch(
            game_date="2024-11-24",
            games=games,
            prediction_loader=mock_pred_loader,
            result_loader=mock_result_loader,
        )

        assert summary["games_skipped"] == 1
        assert summary["games_analyzed"] == 0


class TestAnalysisServiceAggregation:
    """Tests for statistics aggregation."""

    def test_get_aggregate_stats(self, sample_analysis_result):
        """Test aggregate statistics calculation."""
        with patch("services.analysis.service.AnalysisRepository"):
            service = AnalysisService(sport="nfl")

        analyses = [sample_analysis_result, sample_analysis_result]

        stats = service.get_aggregate_stats(analyses)

        assert stats["total_games"] == 2
        assert stats["total_bets"] == 4
        assert stats["bets_won"] == 4
        assert stats["bets_lost"] == 0
        assert stats["win_rate"] == 100.0
        assert stats["total_profit"] > 0

    def test_get_aggregate_stats_empty(self):
        """Test aggregate statistics with no analyses."""
        with patch("services.analysis.service.AnalysisRepository"):
            service = AnalysisService(sport="nfl")

        stats = service.get_aggregate_stats([])

        assert stats["total_games"] == 0
        assert stats["total_bets"] == 0
        assert stats["win_rate"] == 0


class TestAnalysisServiceFormatting:
    """Tests for markdown formatting."""

    def test_format_analysis_markdown(
        self, test_analysis_config, sample_prediction_data, sample_result_data
    ):
        """Test formatting single analysis as markdown."""
        with patch("services.analysis.service.AnalysisRepository"):
            service = AnalysisService(
                sport="nfl",
                config=test_analysis_config,
            )

        result = service.analyze_game(
            game_date="2024-11-24",
            away_team="nyg",
            home_team="dal",
            prediction_data=sample_prediction_data,
            result_data=sample_result_data,
        )

        markdown = service.format_analysis_markdown(result)

        assert "# Bet Analysis Results" in markdown
        assert "Summary" in markdown
        assert "Bet Details" in markdown

    def test_format_batch_summary_markdown(
        self, test_analysis_config, sample_prediction_data, sample_result_data
    ):
        """Test formatting batch summary as markdown."""
        mock_repo = MagicMock()
        mock_repo.save_analysis.return_value = True
        mock_repo.analysis_exists.return_value = False

        with patch("services.analysis.service.AnalysisRepository", return_value=mock_repo):
            service = AnalysisService(
                sport="nfl",
                config=test_analysis_config,
            )

        games = [{"away_team": "nyg", "home_team": "dal"}]

        def mock_pred_loader(date, game):
            return sample_prediction_data

        def mock_result_loader(date, game):
            return sample_result_data

        batch_result = service.analyze_games_batch(
            game_date="2024-11-24",
            games=games,
            prediction_loader=mock_pred_loader,
            result_loader=mock_result_loader,
        )

        markdown = service.format_batch_summary_markdown(batch_result)

        assert "# Analysis Summary" in markdown
        assert "2024-11-24" in markdown
        assert "Games Analyzed" in markdown
        assert "Aggregate Results" in markdown
