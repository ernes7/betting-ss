"""Unit tests for PredictionService."""

import pytest
import tempfile
import os
import json
from unittest.mock import MagicMock, patch

from services.prediction import (
    PredictionService,
    PredictionServiceConfig,
    EVPredictor,
    AIPredictor,
    get_default_config,
    get_ev_only_config,
)


class TestPredictionServiceInit:
    """Tests for PredictionService initialization."""

    def test_init_with_defaults(self, mock_sport_config):
        """Test initialization with default configuration."""
        with patch("services.prediction.service.EVPredictor"), \
             patch("services.prediction.service.AIPredictor"):
            service = PredictionService(
                sport="nfl",
                sport_config=mock_sport_config,
            )

        assert service.sport == "nfl"
        assert service.config is not None
        assert service.ev_predictor is not None

    def test_init_normalizes_sport(self, mock_sport_config):
        """Test that sport is normalized to lowercase."""
        with patch("services.prediction.service.EVPredictor"), \
             patch("services.prediction.service.AIPredictor"):
            service = PredictionService(
                sport="NFL",
                sport_config=mock_sport_config,
            )

        assert service.sport == "nfl"

    def test_init_with_ev_only_config(self, mock_sport_config):
        """Test initialization with EV-only configuration."""
        config = get_ev_only_config()

        with patch("services.prediction.service.EVPredictor"):
            service = PredictionService(
                sport="nfl",
                sport_config=mock_sport_config,
                config=config,
            )

        assert service.config.use_dual_predictions is False
        assert service.ai_predictor is None

    def test_predictions_dir_property(self, mock_sport_config, test_prediction_config):
        """Test predictions directory property."""
        with patch("services.prediction.service.EVPredictor"), \
             patch("services.prediction.service.AIPredictor"):
            service = PredictionService(
                sport="nfl",
                sport_config=mock_sport_config,
                config=test_prediction_config,
            )

        assert "nfl" in str(service.predictions_dir)


class TestPredictionServicePredictGame:
    """Tests for predict_game method."""

    def test_predict_game_ev_only(
        self, mock_sport_config, sample_odds_data, sample_ev_result
    ):
        """Test predicting game with EV only."""
        mock_ev = MagicMock()
        mock_ev.predict.return_value = sample_ev_result
        mock_ev.format_results.return_value = {
            "sport": "nfl",
            "bets": sample_ev_result["bets"],
        }

        config = get_ev_only_config()

        with patch("services.prediction.service.EVPredictor", return_value=mock_ev):
            service = PredictionService(
                sport="nfl",
                sport_config=mock_sport_config,
                config=config,
            )

        result = service.predict_game(
            game_date="2024-11-24",
            away_team="Giants",
            home_team="Cowboys",
            odds=sample_odds_data,
            run_ai=False,
        )

        assert result["success"] is True
        assert result["ev_result"] is not None
        assert result["ai_result"] is None

    def test_predict_game_dual(
        self,
        mock_sport_config,
        test_prediction_config,
        sample_odds_data,
        sample_ev_result,
        sample_ai_result,
    ):
        """Test predicting game with both EV and AI."""
        mock_ev = MagicMock()
        mock_ev.predict.return_value = sample_ev_result
        mock_ev.format_results.return_value = {
            "sport": "nfl",
            "bets": sample_ev_result["bets"],
        }

        mock_ai = MagicMock()
        mock_ai.predict.return_value = sample_ai_result
        mock_ai.format_results.return_value = {
            "sport": "nfl",
            "bets": sample_ai_result["bets"],
        }

        with patch("services.prediction.service.EVPredictor", return_value=mock_ev), \
             patch("services.prediction.service.AIPredictor", return_value=mock_ai):
            service = PredictionService(
                sport="nfl",
                sport_config=mock_sport_config,
                config=test_prediction_config,
            )

        result = service.predict_game(
            game_date="2024-11-24",
            away_team="Giants",
            home_team="Cowboys",
            odds=sample_odds_data,
        )

        assert result["success"] is True
        assert result["ev_result"] is not None
        assert result["ai_result"] is not None
        assert result["comparison"] is not None

    def test_predict_game_ev_failure(self, mock_sport_config, sample_odds_data):
        """Test handling EV prediction failure."""
        mock_ev = MagicMock()
        mock_ev.predict.return_value = {
            "success": False,
            "error": "Rankings not found",
            "bets": [],
        }

        config = get_ev_only_config()

        with patch("services.prediction.service.EVPredictor", return_value=mock_ev):
            service = PredictionService(
                sport="nfl",
                sport_config=mock_sport_config,
                config=config,
            )

        result = service.predict_game(
            game_date="2024-11-24",
            away_team="Giants",
            home_team="Cowboys",
            odds=sample_odds_data,
            run_ai=False,
        )

        assert result["ev_result"] is not None
        assert "error" in result["ev_result"]


class TestPredictionServiceSaveLoad:
    """Tests for save and load methods."""

    def test_save_and_load_prediction(self, mock_sport_config, sample_ev_result):
        """Test saving and loading a prediction."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = PredictionServiceConfig(data_root=tmpdir)

            with patch("services.prediction.service.EVPredictor"), \
                 patch("services.prediction.service.AIPredictor"):
                service = PredictionService(
                    sport="nfl",
                    sport_config=mock_sport_config,
                    config=config,
                )

            prediction = {"sport": "nfl", "bets": sample_ev_result["bets"]}
            game_key = "2024-11-24_nyg_dal"

            # Save
            filepath = service.save_prediction(
                prediction, game_key, "2024-11-24", "ev"
            )

            assert os.path.exists(filepath)

            # Load
            loaded = service.load_prediction(game_key, "2024-11-24", "ev")

            assert loaded is not None
            assert loaded["sport"] == "nfl"

    def test_load_nonexistent_prediction(self, mock_sport_config):
        """Test loading a prediction that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = PredictionServiceConfig(data_root=tmpdir)

            with patch("services.prediction.service.EVPredictor"), \
                 patch("services.prediction.service.AIPredictor"):
                service = PredictionService(
                    sport="nfl",
                    sport_config=mock_sport_config,
                    config=config,
                )

            result = service.load_prediction("2024-11-24_xxx_yyy", "2024-11-24", "ev")

            assert result is None


class TestPredictionServiceComparison:
    """Tests for prediction comparison."""

    def test_compare_predictions(self, mock_sport_config, test_prediction_config):
        """Test comparing EV and AI predictions."""
        with patch("services.prediction.service.EVPredictor"), \
             patch("services.prediction.service.AIPredictor"):
            service = PredictionService(
                sport="nfl",
                sport_config=mock_sport_config,
                config=test_prediction_config,
            )

        ev_result = {
            "bets": [
                {"description": "Dak Prescott Over 275 Pass Yds"},
                {"description": "Cowboys -3.5"},
            ]
        }

        ai_result = {
            "bets": [
                {"bet": "Dak Prescott Over 275 Pass Yds"},
                {"bet": "Giants +3.5"},
            ]
        }

        comparison = service._compare_predictions(ev_result, ai_result)

        assert comparison["ev_bet_count"] == 2
        assert comparison["ai_bet_count"] == 2
        assert "agreement_rate" in comparison

    def test_bets_match(self, mock_sport_config, test_prediction_config):
        """Test bet matching logic."""
        with patch("services.prediction.service.EVPredictor"), \
             patch("services.prediction.service.AIPredictor"):
            service = PredictionService(
                sport="nfl",
                sport_config=mock_sport_config,
                config=test_prediction_config,
            )

        # Same player, same market
        assert service._bets_match(
            "Dak Prescott Over 275 Pass Yds",
            "Dak Prescott Over 275 Pass Yds"
        ) is True

        # Different bets
        assert service._bets_match(
            "Cowboys -3.5",
            "Giants +3.5"
        ) is False


class TestPredictionServiceBatch:
    """Tests for batch prediction."""

    def test_predict_games_batch_success(
        self,
        mock_sport_config,
        test_prediction_config,
        sample_odds_data,
        sample_ev_result,
    ):
        """Test batch prediction with multiple games."""
        mock_ev = MagicMock()
        mock_ev.predict.return_value = sample_ev_result
        mock_ev.format_results.return_value = {
            "sport": "nfl",
            "bets": sample_ev_result["bets"],
        }

        # Use EV-only config to avoid AI mocking complexity
        config = get_ev_only_config()

        with patch("services.prediction.service.EVPredictor", return_value=mock_ev):
            service = PredictionService(
                sport="nfl",
                sport_config=mock_sport_config,
                config=config,
            )

        games = [
            {"away_team": "Giants", "home_team": "Cowboys"},
            {"away_team": "Eagles", "home_team": "Commanders"},
        ]

        def mock_odds_loader(date, game):
            return sample_odds_data

        summary = service.predict_games_batch(
            game_date="2024-11-24",
            games=games,
            odds_loader=mock_odds_loader,
        )

        assert summary["success"] is True
        assert summary["games_processed"] == 2

    def test_predict_games_batch_missing_odds(self, mock_sport_config):
        """Test batch prediction when odds are missing."""
        config = get_ev_only_config()

        with patch("services.prediction.service.EVPredictor"):
            service = PredictionService(
                sport="nfl",
                sport_config=mock_sport_config,
                config=config,
            )

        games = [
            {"away_team": "Giants", "home_team": "Cowboys"},
        ]

        def mock_odds_loader(date, game):
            return None  # No odds available

        summary = service.predict_games_batch(
            game_date="2024-11-24",
            games=games,
            odds_loader=mock_odds_loader,
        )

        assert summary["games_skipped"] == 1
        assert summary["games_processed"] == 0
