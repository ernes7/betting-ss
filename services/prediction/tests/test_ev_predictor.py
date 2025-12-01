"""Unit tests for EVPredictor."""

import pytest
from unittest.mock import MagicMock, patch

from services.prediction import EVPredictor, EVConfig


class TestEVPredictorInit:
    """Tests for EVPredictor initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default configuration."""
        predictor = EVPredictor(sport="nfl")

        assert predictor.sport == "nfl"
        assert predictor.config is not None
        assert predictor.config.conservative_adjustment == 0.85

    def test_init_normalizes_sport(self):
        """Test that sport is normalized to lowercase."""
        predictor = EVPredictor(sport="NFL")
        assert predictor.sport == "nfl"

    def test_init_with_custom_config(self, ev_config):
        """Test initialization with custom configuration."""
        predictor = EVPredictor(sport="nfl", config=ev_config)

        assert predictor.config == ev_config

    def test_init_with_base_dir(self):
        """Test initialization with custom base directory."""
        predictor = EVPredictor(sport="nfl", base_dir="/custom/path")

        assert predictor.base_dir == "/custom/path"


class TestEVPredictorPredict:
    """Tests for EVPredictor prediction method."""

    def test_predict_success(self, ev_config, sample_odds_data, mock_sport_config):
        """Test successful prediction."""
        predictor = EVPredictor(sport="nfl", config=ev_config)

        with patch("shared.models.ev_calculator.EVCalculator") as MockCalc:
            mock_instance = MagicMock()
            mock_instance.calculate_all_ev.return_value = [{"ev_percent": 5.0}] * 10
            mock_instance.get_top_n.return_value = [
                {"description": "Test bet", "ev_percent": 5.0}
            ]
            MockCalc.return_value = mock_instance

            result = predictor.predict(sample_odds_data, mock_sport_config)

        assert result["success"] is True
        assert result["total_analyzed"] == 10
        assert len(result["bets"]) == 1

    def test_predict_with_data_error(self, ev_config, sample_odds_data, mock_sport_config):
        """Test prediction with data validation error."""
        predictor = EVPredictor(sport="nfl", config=ev_config)

        with patch("shared.models.ev_calculator.EVCalculator") as MockCalc:
            MockCalc.side_effect = ValueError("Rankings data not available")

            result = predictor.predict(sample_odds_data, mock_sport_config)

        assert result["success"] is False
        assert "Rankings data not available" in result["error"]

    def test_predict_with_exception(self, ev_config, sample_odds_data, mock_sport_config):
        """Test prediction with unexpected exception."""
        predictor = EVPredictor(sport="nfl", config=ev_config)

        with patch("shared.models.ev_calculator.EVCalculator") as MockCalc:
            MockCalc.side_effect = Exception("Unexpected error")

            result = predictor.predict(sample_odds_data, mock_sport_config)

        assert result["success"] is False
        assert "Unexpected error" in result["error"]


class TestEVPredictorFormat:
    """Tests for EVPredictor formatting methods."""

    def test_format_results(self, ev_config, sample_ev_result):
        """Test formatting prediction results."""
        predictor = EVPredictor(sport="nfl", config=ev_config)

        formatted = predictor.format_results(
            sample_ev_result,
            teams=["Giants", "Cowboys"],
            home_team="Cowboys",
            game_date="2024-11-24",
        )

        assert formatted["sport"] == "nfl"
        assert formatted["prediction_type"] == "ev_calculator"
        assert formatted["teams"] == ["Giants", "Cowboys"]
        assert formatted["home_team"] == "Cowboys"
        assert formatted["date"] == "2024-11-24"
        assert "bets" in formatted
        assert "summary" in formatted

    def test_format_results_with_empty_bets(self, ev_config):
        """Test formatting with no bets."""
        predictor = EVPredictor(sport="nfl", config=ev_config)

        result = {"success": True, "bets": [], "total_analyzed": 45}

        formatted = predictor.format_results(
            result,
            teams=["Giants", "Cowboys"],
            home_team="Cowboys",
            game_date="2024-11-24",
        )

        assert formatted["summary"]["total_bets"] == 0
        assert formatted["summary"]["avg_ev"] == 0

    def test_format_to_markdown(self, ev_config, sample_ev_result):
        """Test formatting to markdown."""
        predictor = EVPredictor(sport="nfl", config=ev_config)

        formatted = predictor.format_results(
            sample_ev_result,
            teams=["Giants", "Cowboys"],
            home_team="Cowboys",
            game_date="2024-11-24",
        )

        markdown = predictor.format_to_markdown(formatted)

        assert "# EV Calculator Analysis" in markdown
        assert "Giants" in markdown
        assert "Cowboys" in markdown
        assert "Dak Prescott" in markdown
        assert "CeeDee Lamb" in markdown

    def test_format_to_markdown_no_bets(self, ev_config):
        """Test markdown formatting with no bets."""
        predictor = EVPredictor(sport="nfl", config=ev_config)

        formatted = {
            "teams": ["Giants", "Cowboys"],
            "home_team": "Cowboys",
            "date": "2024-11-24",
            "generated_at": "2024-11-24 12:00:00",
            "total_bets_analyzed": 45,
            "conservative_adjustment": 0.85,
            "bets": [],
        }

        markdown = predictor.format_to_markdown(formatted)

        assert "No positive EV bets found" in markdown
