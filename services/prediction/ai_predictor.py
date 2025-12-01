"""AI Predictor using Claude API for bet analysis.

Wraps the base Predictor with constructor injection for the new service architecture.
"""

import re
from typing import Any, Dict, List, Optional

from services.prediction.config import AIConfig
from shared.logging import get_logger
from shared.errors import PredictionAPIError


logger = get_logger("prediction")


class AIPredictor:
    """AI-powered predictor using Claude API.

    Uses Claude to analyze betting opportunities with:
    - Team and player statistics
    - Matchup analysis
    - EV+ calculation for positive expected value bets

    This predictor requires an Anthropic API key and incurs costs
    based on token usage.

    Attributes:
        config: AI configuration
        sport: Sport being analyzed
        predictor: Underlying Predictor instance

    Example:
        predictor = AIPredictor(sport="nfl", sport_config=config)
        results = predictor.predict(
            away_team="Giants",
            home_team="Cowboys",
            odds=odds_data,
        )
    """

    def __init__(
        self,
        sport: str,
        sport_config: Any,
        config: Optional[AIConfig] = None,
    ):
        """Initialize the AI predictor.

        Args:
            sport: Sport to analyze (nfl, nba)
            sport_config: Sport-specific configuration
            config: AI configuration (optional)
        """
        from shared.base.predictor import Predictor

        self.sport = sport.lower()
        self.config = config or AIConfig()
        self.sport_config = sport_config
        self.predictor = Predictor(sport_config, model=self.config.model)

    def predict(
        self,
        away_team: str,
        home_team: str,
        odds: Dict[str, Any],
        rankings: Optional[Dict[str, Any]] = None,
        away_profile: Optional[Dict[str, Any]] = None,
        home_profile: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate AI predictions for a game.

        Args:
            away_team: Away team name
            home_team: Home team name
            odds: Betting odds data
            rankings: Team rankings (optional, will load if not provided)
            away_profile: Away team profile (optional, will load if not provided)
            home_profile: Home team profile (optional, will load if not provided)

        Returns:
            Dictionary with prediction results:
            {
                "success": bool,
                "prediction": str,
                "bets": List[Dict],
                "cost": float,
                "model": str,
                "tokens": Dict,
                "error": str (only if success=False)
            }
        """
        logger.info(f"Running AI prediction for {away_team} @ {home_team}")

        try:
            result = self.predictor.generate_predictions(
                team_a=away_team,
                team_b=home_team,
                home_team=home_team,
                rankings=rankings,
                profile_a=away_profile,
                profile_b=home_profile,
                odds=odds,
            )

            if not result.get("success"):
                logger.error(f"AI prediction failed: {result.get('error')}")
                return {
                    "success": False,
                    "prediction": "",
                    "bets": [],
                    "cost": 0.0,
                    "model": self.config.model,
                    "tokens": {"input": 0, "output": 0, "total": 0},
                    "error": result.get("error", "Unknown error"),
                }

            # Parse prediction text into structured bets
            prediction_text = result.get("prediction", "")
            bets = self._parse_prediction_text(prediction_text)

            logger.info(
                f"AI prediction complete: {len(bets)} bets, ${result.get('cost', 0):.2f} cost"
            )

            return {
                "success": True,
                "prediction": prediction_text,
                "bets": bets,
                "cost": result.get("cost", 0.0),
                "model": result.get("model", self.config.model),
                "tokens": result.get("tokens", {"input": 0, "output": 0, "total": 0}),
            }

        except Exception as e:
            logger.error(f"AI prediction error: {e}")
            return {
                "success": False,
                "prediction": "",
                "bets": [],
                "cost": 0.0,
                "model": self.config.model,
                "tokens": {"input": 0, "output": 0, "total": 0},
                "error": str(e),
            }

    def _parse_prediction_text(self, prediction_text: str) -> List[Dict[str, Any]]:
        """Parse AI prediction text into structured bet data.

        Args:
            prediction_text: Raw prediction text from Claude

        Returns:
            List of bet dictionaries
        """
        bets = []

        # Pattern to match EV singles format
        bet_pattern = (
            r'## Bet (\d+):.+?\n'
            r'\*\*Bet\*\*: (.+?)\n'
            r'\*\*Odds\*\*: ([+-]?\d+)\n'
            r'\*\*Implied Probability\*\*: ([\d.]+)%[^\n]*\n'
            r'\*\*True Probability\*\*: ([\d.]+)%[^\n]*\n'
            r'\*\*Expected Value\*\*: \+?([\d.]+)%'
        )

        for match in re.finditer(bet_pattern, prediction_text, re.DOTALL):
            bets.append({
                "rank": int(match.group(1)),
                "bet": match.group(2).strip(),
                "odds": int(match.group(3)),
                "implied_probability": float(match.group(4)),
                "true_probability": float(match.group(5)),
                "expected_value": float(match.group(6)),
            })

        return bets

    def format_results(
        self,
        prediction: Dict[str, Any],
        teams: List[str],
        home_team: str,
        game_date: str,
    ) -> Dict[str, Any]:
        """Format AI prediction results for saving.

        Args:
            prediction: Prediction results from predict()
            teams: List of team names [away, home]
            home_team: Home team name
            game_date: Game date in YYYY-MM-DD format

        Returns:
            Formatted results dictionary
        """
        from shared.utils.timezone_utils import get_eastern_now

        bets = prediction.get("bets", [])

        # Calculate summary stats
        if bets:
            ev_values = [bet.get("expected_value", 0) for bet in bets]
            summary = {
                "total_bets": len(bets),
                "avg_ev": round(sum(ev_values) / len(ev_values), 2),
                "ev_range": [round(min(ev_values), 2), round(max(ev_values), 2)],
            }
        else:
            summary = {"total_bets": 0, "avg_ev": 0, "ev_range": [0, 0]}

        return {
            "sport": self.sport,
            "prediction_type": "ai_predictor",
            "teams": teams,
            "home_team": home_team,
            "date": game_date,
            "generated_at": get_eastern_now().strftime("%Y-%m-%d %H:%M:%S"),
            "model": prediction.get("model", self.config.model),
            "api_cost": prediction.get("cost", 0.0),
            "tokens": prediction.get("tokens", {}),
            "bets": bets,
            "summary": summary,
        }

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate API cost for token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Total cost in dollars
        """
        input_cost = (input_tokens / 1_000_000) * self.config.input_cost_per_million
        output_cost = (output_tokens / 1_000_000) * self.config.output_cost_per_million
        return input_cost + output_cost
