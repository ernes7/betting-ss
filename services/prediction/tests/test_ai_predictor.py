"""Unit tests for AIPredictor."""

import pytest
from unittest.mock import MagicMock, patch

from services.prediction import AIPredictor, AIConfig


class TestAIPredictorInit:
    """Tests for AIPredictor initialization."""

    def test_init_with_defaults(self, mock_sport_config):
        """Test initialization with default configuration."""
        with patch("shared.base.predictor.Predictor"):
            predictor = AIPredictor(sport="nfl", sport_config=mock_sport_config)

        assert predictor.sport == "nfl"
        assert predictor.config is not None
        assert predictor.config.model == "claude-sonnet-4-5-20250929"

    def test_init_normalizes_sport(self, mock_sport_config):
        """Test that sport is normalized to lowercase."""
        with patch("shared.base.predictor.Predictor"):
            predictor = AIPredictor(sport="NFL", sport_config=mock_sport_config)

        assert predictor.sport == "nfl"

    def test_init_with_custom_config(self, ai_config, mock_sport_config):
        """Test initialization with custom configuration."""
        with patch("shared.base.predictor.Predictor"):
            predictor = AIPredictor(
                sport="nfl",
                sport_config=mock_sport_config,
                config=ai_config,
            )

        assert predictor.config == ai_config


class TestAIPredictorPredict:
    """Tests for AIPredictor prediction method."""

    def test_predict_success(self, ai_config, mock_sport_config, sample_odds_data):
        """Test successful AI prediction."""
        with patch("shared.base.predictor.Predictor") as MockPredictor:
            mock_instance = MagicMock()
            mock_instance.generate_predictions.return_value = {
                "success": True,
                "prediction": """## Bet 1: Test Bet
**Bet**: Test Bet
**Odds**: -110
**Implied Probability**: 52.4%
**True Probability**: 60.0%
**Expected Value**: +5.0%""",
                "cost": 0.10,
                "model": "claude-sonnet-4-5-20250929",
                "tokens": {"input": 1000, "output": 200, "total": 1200},
            }
            MockPredictor.return_value = mock_instance

            predictor = AIPredictor(
                sport="nfl",
                sport_config=mock_sport_config,
                config=ai_config,
            )

            result = predictor.predict(
                away_team="Giants",
                home_team="Cowboys",
                odds=sample_odds_data,
            )

        assert result["success"] is True
        assert len(result["bets"]) == 1
        assert result["cost"] == 0.10
        assert result["bets"][0]["expected_value"] == 5.0

    def test_predict_failure(self, ai_config, mock_sport_config, sample_odds_data):
        """Test AI prediction failure."""
        with patch("shared.base.predictor.Predictor") as MockPredictor:
            mock_instance = MagicMock()
            mock_instance.generate_predictions.return_value = {
                "success": False,
                "error": "API key not found",
                "prediction": "",
                "cost": 0.0,
                "model": "claude-sonnet-4-5-20250929",
                "tokens": {"input": 0, "output": 0, "total": 0},
            }
            MockPredictor.return_value = mock_instance

            predictor = AIPredictor(
                sport="nfl",
                sport_config=mock_sport_config,
                config=ai_config,
            )

            result = predictor.predict(
                away_team="Giants",
                home_team="Cowboys",
                odds=sample_odds_data,
            )

        assert result["success"] is False
        assert "API key not found" in result["error"]

    def test_predict_with_exception(self, ai_config, mock_sport_config, sample_odds_data):
        """Test AI prediction with exception."""
        with patch("shared.base.predictor.Predictor") as MockPredictor:
            mock_instance = MagicMock()
            mock_instance.generate_predictions.side_effect = Exception("Network error")
            MockPredictor.return_value = mock_instance

            predictor = AIPredictor(
                sport="nfl",
                sport_config=mock_sport_config,
                config=ai_config,
            )

            result = predictor.predict(
                away_team="Giants",
                home_team="Cowboys",
                odds=sample_odds_data,
            )

        assert result["success"] is False
        assert "Network error" in result["error"]


class TestAIPredictorParsing:
    """Tests for AI prediction text parsing."""

    def test_parse_prediction_text(self, ai_config, mock_sport_config):
        """Test parsing AI prediction text."""
        with patch("shared.base.predictor.Predictor"):
            predictor = AIPredictor(
                sport="nfl",
                sport_config=mock_sport_config,
                config=ai_config,
            )

        prediction_text = """
## Bet 1: Dak Prescott Over 275 Pass Yds
**Bet**: Dak Prescott Over 275 Pass Yds
**Odds**: -110
**Implied Probability**: 52.4%
**True Probability**: 60.0%
**Expected Value**: +6.5%

## Bet 2: Cowboys -3.5
**Bet**: Cowboys -3.5
**Odds**: -110
**Implied Probability**: 52.4%
**True Probability**: 58.0%
**Expected Value**: +5.2%
"""

        bets = predictor._parse_prediction_text(prediction_text)

        assert len(bets) == 2
        assert bets[0]["rank"] == 1
        assert bets[0]["bet"] == "Dak Prescott Over 275 Pass Yds"
        assert bets[0]["odds"] == -110
        assert bets[0]["expected_value"] == 6.5
        assert bets[1]["rank"] == 2
        assert bets[1]["bet"] == "Cowboys -3.5"

    def test_parse_empty_prediction(self, ai_config, mock_sport_config):
        """Test parsing empty prediction text."""
        with patch("shared.base.predictor.Predictor"):
            predictor = AIPredictor(
                sport="nfl",
                sport_config=mock_sport_config,
                config=ai_config,
            )

        bets = predictor._parse_prediction_text("")

        assert bets == []


class TestAIPredictorFormat:
    """Tests for AIPredictor formatting methods."""

    def test_format_results(self, ai_config, mock_sport_config, sample_ai_result):
        """Test formatting AI prediction results."""
        with patch("shared.base.predictor.Predictor"):
            predictor = AIPredictor(
                sport="nfl",
                sport_config=mock_sport_config,
                config=ai_config,
            )

        formatted = predictor.format_results(
            sample_ai_result,
            teams=["Giants", "Cowboys"],
            home_team="Cowboys",
            game_date="2024-11-24",
        )

        assert formatted["sport"] == "nfl"
        assert formatted["prediction_type"] == "ai_predictor"
        assert formatted["teams"] == ["Giants", "Cowboys"]
        assert formatted["home_team"] == "Cowboys"
        assert formatted["api_cost"] == 0.15
        assert "bets" in formatted
        assert "summary" in formatted

    def test_calculate_cost(self, ai_config, mock_sport_config):
        """Test API cost calculation."""
        with patch("shared.base.predictor.Predictor"):
            predictor = AIPredictor(
                sport="nfl",
                sport_config=mock_sport_config,
                config=ai_config,
            )

        # 1 million input tokens = $3, 1 million output tokens = $15
        cost = predictor.calculate_cost(1_000_000, 1_000_000)

        assert cost == 18.0  # $3 + $15

    def test_calculate_cost_small(self, ai_config, mock_sport_config):
        """Test cost calculation for small token counts."""
        with patch("shared.base.predictor.Predictor"):
            predictor = AIPredictor(
                sport="nfl",
                sport_config=mock_sport_config,
                config=ai_config,
            )

        # 5000 input, 500 output (typical prediction)
        cost = predictor.calculate_cost(5000, 500)

        expected = (5000 / 1_000_000) * 3.0 + (500 / 1_000_000) * 15.0
        assert abs(cost - expected) < 0.001
