"""Prediction service for generating betting predictions.

Main entry point for the PREDICTION service. Coordinates EV and AI predictors
to generate betting recommendations.
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.prediction.config import (
    PredictionServiceConfig,
    get_default_config,
)
from services.prediction.ev_predictor import EVPredictor
from services.prediction.ai_predictor import AIPredictor
from shared.logging import get_logger
from shared.errors import ErrorHandler, create_error_handler, PredictionError
from shared.utils.csv_storage import save_csv, load_csv, ensure_directory


logger = get_logger("prediction")


class PredictionService:
    """Service for generating betting predictions.

    Orchestrates the prediction workflow:
    1. Load odds data for games
    2. Run EV Calculator (statistical analysis)
    3. Optionally run AI Predictor (Claude API)
    4. Compare and save results

    Attributes:
        sport: Sport being processed (nfl, nba)
        sport_config: Sport-specific configuration
        config: Prediction service configuration
        ev_predictor: EV Calculator predictor
        ai_predictor: AI predictor (optional)
        error_handler: Error handler for the service

    Example:
        service = PredictionService(sport="nfl", sport_config=nfl_config)
        result = service.predict_game(
            game_date="2024-11-24",
            away_team="Giants",
            home_team="Cowboys",
            odds=odds_data,
        )
    """

    def __init__(
        self,
        sport: str,
        sport_config: Any,
        config: Optional[PredictionServiceConfig] = None,
        ev_predictor: Optional[EVPredictor] = None,
        ai_predictor: Optional[AIPredictor] = None,
        error_handler: Optional[ErrorHandler] = None,
        base_dir: Optional[str] = None,
    ):
        """Initialize the prediction service.

        Args:
            sport: Sport to process (nfl, nba)
            sport_config: Sport-specific configuration
            config: Prediction service configuration
            ev_predictor: EV predictor instance (optional)
            ai_predictor: AI predictor instance (optional)
            error_handler: Error handler (optional)
            base_dir: Base directory for data files
        """
        self.sport = sport.lower()
        self.sport_config = sport_config
        self.config = config or get_default_config()
        self.base_dir = base_dir or os.getcwd()

        # Initialize predictors
        self.ev_predictor = ev_predictor or EVPredictor(
            sport=self.sport,
            config=self.config.ev_config,
            base_dir=self.base_dir,
        )

        # Only create AI predictor if dual predictions enabled
        if self.config.use_dual_predictions:
            self.ai_predictor = ai_predictor or AIPredictor(
                sport=self.sport,
                sport_config=sport_config,
                config=self.config.ai_config,
            )
        else:
            self.ai_predictor = None

        self.error_handler = error_handler or create_error_handler("prediction")

        # Use sport config's predictions_dir if available, otherwise use default
        if hasattr(sport_config, 'predictions_dir') and sport_config.predictions_dir:
            self._predictions_dir = Path(sport_config.predictions_dir)
        else:
            self._predictions_dir = Path(self.config.data_root.format(sport=self.sport))

    @property
    def predictions_dir(self) -> Path:
        """Get the predictions data directory path."""
        return self._predictions_dir

    def predict_game(
        self,
        game_date: str,
        away_team: str,
        home_team: str,
        odds: Dict[str, Any],
        rankings: Optional[Dict[str, Any]] = None,
        away_profile: Optional[Dict[str, Any]] = None,
        home_profile: Optional[Dict[str, Any]] = None,
        run_ev: bool = True,
        run_ai: bool = True,
        odds_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate predictions for a single game.

        Args:
            game_date: Game date in YYYY-MM-DD format
            away_team: Away team name
            home_team: Home team name
            odds: Betting odds data
            rankings: Team rankings (optional)
            away_profile: Away team profile (optional)
            home_profile: Home team profile (optional)
            run_ev: Whether to run EV prediction
            run_ai: Whether to run AI prediction
            odds_dir: Path to odds directory (optional, constructed if not provided)

        Returns:
            Dictionary with prediction results:
            {
                "success": bool,
                "ev_result": Dict (if run_ev),
                "ai_result": Dict (if run_ai),
                "comparison": Dict (if both run),
                "total_cost": float,
                "error": str (only if success=False)
            }
        """
        logger.info(f"Predicting game: {away_team} @ {home_team} on {game_date}")

        result = {
            "success": True,
            "game_date": game_date,
            "away_team": away_team,
            "home_team": home_team,
            "ev_result": None,
            "ai_result": None,
            "comparison": None,
            "total_cost": 0.0,
        }

        # Filter odds if configured
        if self.config.odds_filter:
            odds = self._filter_odds(odds)

        # Run EV prediction
        if run_ev:
            try:
                ev_start = time.time()
                ev_prediction = self.ev_predictor.predict(
                    odds_data=odds,
                    sport_config=self.sport_config,
                )
                ev_time = time.time() - ev_start

                if ev_prediction.get("success"):
                    result["ev_result"] = self.ev_predictor.format_results(
                        ev_prediction,
                        teams=[away_team, home_team],
                        home_team=home_team,
                        game_date=game_date,
                    )
                    result["ev_result"]["processing_time"] = ev_time
                    logger.info(f"EV prediction complete ({ev_time:.1f}s)")
                else:
                    logger.warning(f"EV prediction failed: {ev_prediction.get('error')}")
                    result["ev_result"] = {"error": ev_prediction.get("error")}

            except Exception as e:
                logger.error(f"EV prediction error: {e}")
                result["ev_result"] = {"error": str(e)}

        # Run AI prediction
        if run_ai and self.ai_predictor:
            try:
                ai_start = time.time()

                # Use provided odds_dir or construct from team names (fallback)
                if odds_dir is None:
                    game_folder = f"{home_team}_{away_team}".lower().replace(" ", "_").replace(".", "")[:20]
                    if self.sport == "bundesliga":
                        odds_dir = f"sports/futbol/bundesliga/data/odds/{game_date}/{game_folder}"
                    else:
                        odds_dir = f"sports/{self.sport}/data/odds/{game_date}/{game_folder}"

                ai_prediction = self.ai_predictor.predict(
                    away_team=away_team,
                    home_team=home_team,
                    odds=odds,
                    rankings=rankings,
                    away_profile=away_profile,
                    home_profile=home_profile,
                    game_date=game_date,
                    odds_dir=odds_dir,
                )
                ai_time = time.time() - ai_start

                if ai_prediction.get("success"):
                    result["ai_result"] = self.ai_predictor.format_results(
                        ai_prediction,
                        teams=[away_team, home_team],
                        home_team=home_team,
                        game_date=game_date,
                    )
                    result["ai_result"]["processing_time"] = ai_time
                    result["total_cost"] = ai_prediction.get("cost", 0.0)
                    logger.info(
                        f"AI prediction complete ({ai_time:.1f}s, ${result['total_cost']:.2f})"
                    )
                else:
                    logger.warning(f"AI prediction failed: {ai_prediction.get('error')}")
                    result["ai_result"] = {"error": ai_prediction.get("error")}

            except Exception as e:
                logger.error(f"AI prediction error: {e}")
                result["ai_result"] = {"error": str(e)}

        # Generate comparison if both predictions succeeded
        if result["ev_result"] and result["ai_result"]:
            if "error" not in result["ev_result"] and "error" not in result["ai_result"]:
                result["comparison"] = self._compare_predictions(
                    result["ev_result"],
                    result["ai_result"],
                )

        return result

    def predict_games_batch(
        self,
        game_date: str,
        games: List[Dict[str, Any]],
        odds_loader: Any = None,
    ) -> Dict[str, Any]:
        """Generate predictions for multiple games.

        Args:
            game_date: Game date in YYYY-MM-DD format
            games: List of game info dicts with team names
            odds_loader: Function to load odds for a game

        Returns:
            Summary dictionary with batch results
        """
        logger.info(f"Batch prediction for {len(games)} games on {game_date}")

        summary = {
            "success": True,
            "games_processed": 0,
            "games_skipped": 0,
            "games_failed": 0,
            "total_cost": 0.0,
            "results": [],
            "errors": [],
        }

        for game in games:
            away_team = game.get("away_team") or game.get("away_name")
            home_team = game.get("home_team") or game.get("home_name")

            if not away_team or not home_team:
                summary["errors"].append({
                    "game": str(game),
                    "error": "Missing team names",
                })
                summary["games_failed"] += 1
                continue

            try:
                # Load odds if loader provided
                odds = None
                if odds_loader:
                    odds = odds_loader(game_date, game)

                if not odds:
                    logger.warning(f"No odds for {away_team} @ {home_team}")
                    summary["games_skipped"] += 1
                    continue

                # Run prediction
                result = self.predict_game(
                    game_date=game_date,
                    away_team=away_team,
                    home_team=home_team,
                    odds=odds,
                )

                if result.get("success"):
                    summary["games_processed"] += 1
                    summary["total_cost"] += result.get("total_cost", 0.0)
                    summary["results"].append({
                        "game": f"{away_team} @ {home_team}",
                        "ev_bets": len(result.get("ev_result", {}).get("bets", [])),
                        "ai_bets": len(result.get("ai_result", {}).get("bets", [])),
                        "cost": result.get("total_cost", 0.0),
                    })
                else:
                    summary["games_failed"] += 1
                    summary["errors"].append({
                        "game": f"{away_team} @ {home_team}",
                        "error": result.get("error", "Unknown error"),
                    })

                # Rate limiting between AI predictions
                if self.ai_predictor and self.config.ai_config.rate_limit_seconds > 0:
                    time.sleep(self.config.ai_config.rate_limit_seconds)

            except Exception as e:
                logger.error(f"Failed to predict {away_team} @ {home_team}: {e}")
                summary["games_failed"] += 1
                summary["errors"].append({
                    "game": f"{away_team} @ {home_team}",
                    "error": str(e),
                })

        logger.info(
            f"Batch complete: {summary['games_processed']} processed, "
            f"{summary['games_skipped']} skipped, {summary['games_failed']} failed, "
            f"${summary['total_cost']:.2f} total cost"
        )

        return summary

    def save_prediction(
        self,
        prediction: Dict[str, Any],
        game_key: str,
        game_date: str,
        prediction_type: str = "dual",
    ) -> Path:
        """Save prediction to JSON file.

        Args:
            prediction: Prediction data
            game_key: Unique game identifier (fallback for filename)
            game_date: Game date in YYYY-MM-DD format
            prediction_type: Type suffix (ev, ai, dual)

        Returns:
            Path to saved file
        """
        # Get team names from matchup if available, otherwise use game_key
        matchup = prediction.get("matchup", "")
        if matchup and " @ " in matchup:
            # "1. FC Heidenheim @ SC Freiburg" -> "1_FC_Heidenheim_vs_SC_Freiburg"
            away, home = matchup.split(" @ ")
            filename = f"{away}_vs_{home}".replace(" ", "_").replace(".", "")
        else:
            # Fallback to game_key
            filename = game_key

        # Create game directory: predictions/{date}/
        game_dir = self._predictions_dir / game_date
        ensure_directory(game_dir)

        # Save prediction as JSON
        filepath = game_dir / f"{filename}.json"
        with open(filepath, "w") as f:
            json.dump(prediction, f, indent=2)

        logger.info(f"Saved prediction to {filepath}")
        return filepath

    def load_prediction(
        self,
        game_key: str,
        game_date: Optional[str] = None,
        prediction_type: str = "dual",
    ) -> Optional[Dict[str, Any]]:
        """Load a saved prediction.

        Args:
            game_key: Unique game identifier
            game_date: Game date (optional, extracted from game_key if not provided)
            prediction_type: Type suffix to load

        Returns:
            Prediction data or None if not found
        """
        if game_date is None:
            game_date = game_key.split("_")[0]

        parts = game_key.split("_")
        if len(parts) >= 3:
            teams = "_".join(parts[1:])
        else:
            teams = game_key

        filepath = self._predictions_dir / game_date / teams / f"prediction_{prediction_type}.csv"

        return load_csv(filepath, as_dict=True)

    def _filter_odds(self, odds: Dict[str, Any]) -> Dict[str, Any]:
        """Filter odds based on configuration.

        Args:
            odds: Original odds data

        Returns:
            Filtered odds data
        """
        from shared.utils.odds_utils import filter_odds_by_range

        return filter_odds_by_range(
            odds,
            min_odds=self.config.odds_filter.min_odds,
            max_odds=self.config.odds_filter.max_odds,
        )

    def _compare_predictions(
        self,
        ev_result: Dict[str, Any],
        ai_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compare EV and AI predictions.

        Args:
            ev_result: EV prediction results
            ai_result: AI prediction results

        Returns:
            Comparison dictionary
        """
        ev_bets = {b.get("description", ""): b for b in ev_result.get("bets", [])}
        ai_bets = {b.get("bet", ""): b for b in ai_result.get("bets", [])}

        # Find overlapping bets (simplified comparison)
        ev_descriptions = set(ev_bets.keys())
        ai_descriptions = set(ai_bets.keys())

        # Count agreements (bets that appear in both)
        agreements = 0
        for ev_desc in ev_descriptions:
            for ai_desc in ai_descriptions:
                if self._bets_match(ev_desc, ai_desc):
                    agreements += 1
                    break

        total_unique = len(ev_descriptions | ai_descriptions)
        agreement_rate = agreements / max(total_unique, 1)

        return {
            "ev_bet_count": len(ev_bets),
            "ai_bet_count": len(ai_bets),
            "agreements": agreements,
            "agreement_rate": agreement_rate,
            "ev_only_bets": len(ev_descriptions) - agreements,
            "ai_only_bets": len(ai_descriptions) - agreements,
        }

    def _bets_match(self, ev_desc: str, ai_desc: str) -> bool:
        """Check if two bet descriptions match.

        Args:
            ev_desc: EV bet description
            ai_desc: AI bet description

        Returns:
            True if bets match
        """
        # Normalize descriptions for comparison
        ev_normalized = ev_desc.lower().replace("over", "").replace("under", "").strip()
        ai_normalized = ai_desc.lower().replace("over", "").replace("under", "").strip()

        # Check for player name and line overlap
        return ev_normalized in ai_normalized or ai_normalized in ev_normalized
