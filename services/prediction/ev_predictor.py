"""EV (Expected Value) Predictor for statistical bet analysis.

Wraps the EVCalculator with constructor injection for the new service architecture.
"""

from typing import Any, Dict, List, Optional

from services.prediction.config import EVConfig, PredictionServiceConfig, get_default_config
from shared.logging import get_logger
from shared.errors import PredictionDataError


logger = get_logger("prediction")


class EVPredictor:
    """Statistical EV predictor using probability calculations.

    Calculates Expected Value for betting opportunities using:
    - Team and player statistics
    - Probability models
    - Conservative adjustments

    This predictor is free to use (no API calls) and provides
    fast statistical analysis of betting opportunities.

    Attributes:
        config: EV configuration
        sport: Sport being analyzed

    Example:
        predictor = EVPredictor(sport="nfl")
        results = predictor.predict(odds_data, sport_config)
    """

    def __init__(
        self,
        sport: str,
        config: Optional[EVConfig] = None,
        base_dir: Optional[str] = None,
    ):
        """Initialize the EV predictor.

        Args:
            sport: Sport to analyze (nfl, nba)
            config: EV configuration (optional)
            base_dir: Base directory for data files
        """
        self.sport = sport.lower()
        self.config = config or EVConfig()
        self.base_dir = base_dir

    def predict(
        self,
        odds_data: Dict[str, Any],
        sport_config: Any,
    ) -> Dict[str, Any]:
        """Generate EV predictions for a game.

        Args:
            odds_data: Complete odds JSON data
            sport_config: Sport-specific configuration

        Returns:
            Dictionary with prediction results:
            {
                "success": bool,
                "bets": List[Dict],
                "total_analyzed": int,
                "top_bets": int,
                "config": Dict,
                "error": str (only if success=False)
            }

        Raises:
            PredictionDataError: If required data is missing
        """
        from shared.models.ev_calculator import EVCalculator

        logger.info(f"Running EV prediction for {self.sport}")

        try:
            # Initialize EV Calculator
            calculator = EVCalculator(
                odds_data=odds_data,
                sport_config=sport_config,
                base_dir=self.base_dir,
                conservative_adjustment=self.config.conservative_adjustment,
            )

            # Calculate all EVs (for total count)
            all_bets = calculator.calculate_all_ev(min_ev_threshold=0.0)
            total_analyzed = len(all_bets)

            # Get top N bets
            top_bets = calculator.get_top_n(
                n=self.config.top_n_bets,
                min_ev_threshold=self.config.min_ev_threshold,
                deduplicate_players=self.config.deduplicate_players,
                max_receivers_per_team=self.config.max_receivers_per_team,
            )

            logger.info(
                f"EV prediction complete: {len(top_bets)} top bets from {total_analyzed} analyzed"
            )

            return {
                "success": True,
                "bets": top_bets,
                "total_analyzed": total_analyzed,
                "top_bets": len(top_bets),
                "config": {
                    "conservative_adjustment": self.config.conservative_adjustment,
                    "min_ev_threshold": self.config.min_ev_threshold,
                    "deduplicate_players": self.config.deduplicate_players,
                },
            }

        except ValueError as e:
            # Data validation errors (e.g., missing rankings)
            logger.error(f"EV prediction data error: {e}")
            return {
                "success": False,
                "bets": [],
                "total_analyzed": 0,
                "top_bets": 0,
                "error": str(e),
            }

        except Exception as e:
            logger.error(f"EV prediction failed: {e}")
            return {
                "success": False,
                "bets": [],
                "total_analyzed": 0,
                "top_bets": 0,
                "error": str(e),
            }

    def format_results(
        self,
        prediction: Dict[str, Any],
        teams: List[str],
        home_team: str,
        game_date: str,
    ) -> Dict[str, Any]:
        """Format EV prediction results for saving.

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
            ev_values = [bet.get("ev_percent", 0) for bet in bets]
            summary = {
                "total_bets": len(bets),
                "avg_ev": round(sum(ev_values) / len(ev_values), 2),
                "ev_range": [round(min(ev_values), 2), round(max(ev_values), 2)],
            }
        else:
            summary = {"total_bets": 0, "avg_ev": 0, "ev_range": [0, 0]}

        return {
            "sport": self.sport,
            "prediction_type": "ev_calculator",
            "teams": teams,
            "home_team": home_team,
            "date": game_date,
            "generated_at": get_eastern_now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_bets_analyzed": prediction.get("total_analyzed", 0),
            "conservative_adjustment": self.config.conservative_adjustment,
            "bets": bets,
            "summary": summary,
        }

    def format_to_markdown(self, formatted_results: Dict[str, Any]) -> str:
        """Format results as markdown.

        Args:
            formatted_results: Formatted results from format_results()

        Returns:
            Markdown string
        """
        lines = []

        teams = formatted_results.get("teams", ["Away", "Home"])
        home_team = formatted_results.get("home_team", teams[1])
        away_team = teams[0] if teams[0] != home_team else teams[1]

        lines.append(f"# EV Calculator Analysis: {away_team} @ {home_team}")
        lines.append(f"**Date:** {formatted_results.get('date', 'Unknown')}")
        lines.append(f"**Generated:** {formatted_results.get('generated_at', 'Unknown')}")
        lines.append(f"**Total Bets Analyzed:** {formatted_results.get('total_bets_analyzed', 0)}")
        lines.append(f"**Conservative Adjustment:** {formatted_results.get('conservative_adjustment', 0.85):.0%}")
        lines.append("")

        bets = formatted_results.get("bets", [])
        if not bets:
            lines.append("No positive EV bets found.")
            return "\n".join(lines)

        lines.append(f"## Top {len(bets)} EV+ Bets")
        lines.append("")

        for i, bet in enumerate(bets, 1):
            lines.append(f"### Bet {i}: {bet.get('description', 'Unknown')}")
            lines.append(f"**Odds:** {bet.get('odds', 'N/A')}")
            lines.append(f"**Implied Probability:** {bet.get('implied_prob', 0):.1f}%")
            lines.append(f"**True Probability:** {bet.get('true_prob', 0):.1f}%")
            lines.append(f"**Adjusted Probability:** {bet.get('adjusted_prob', 0):.1f}%")
            lines.append(f"**Expected Value:** +{bet.get('ev_percent', 0):.2f}%")

            reasoning = bet.get("reasoning", "")
            if reasoning:
                lines.append(f"**Reasoning:** {reasoning}")

            lines.append("")

        return "\n".join(lines)
