"""Bayesian EV Calibrator - Learn from historical prediction errors.

This module implements a calibration system that reduces systematic overconfidence
in EV predictions by learning from historical bet results. It builds calibration
curves by EV bucket and applies market-specific adjustments.

Currently disabled in production due to over-correction (50-70% adjustment).
Needs tuning to find optimal calibration blend percentage.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict


class EVCalibrator:
    """Calibrate EV predictions based on historical performance.

    Analyzes past predictions vs actual outcomes to build calibration curves
    that adjust future probability estimates.
    """

    def __init__(self, results_dir: str):
        """Initialize calibrator with historical results.

        Args:
            results_dir: Path to analysis results directory (e.g., nfl/data/analysis)
        """
        self.results_dir = Path(results_dir)
        self.calibration_data = self._load_historical_results()
        self.calibration_curve = self._build_calibration_curve()
        self.market_adjustments = self._calculate_market_adjustments()

    def _load_historical_results(self) -> List[Dict]:
        """Load all past EV predictions and their outcomes.

        Returns:
            List of bet results with predicted EV, actual outcome, and metadata
        """
        results = []

        if not self.results_dir.exists():
            return results

        # Scan all date directories for analysis files
        for date_dir in self.results_dir.glob("*"):
            if not date_dir.is_dir():
                continue

            for game_file in date_dir.glob("*.json"):
                try:
                    with open(game_file, 'r') as f:
                        data = json.load(f)

                    # Extract EV system results if available
                    if "ev_system" in data and "bet_results" in data["ev_system"]:
                        for bet in data["ev_system"]["bet_results"]:
                            results.append({
                                "predicted_ev": bet.get("ev_percent", 0),
                                "won": bet.get("won", False),
                                "odds": bet.get("odds", 0),
                                "profit": bet.get("profit", 0),
                                "bet_type": bet.get("bet_type", "unknown"),
                                "market": bet.get("market", "unknown")
                            })
                except (json.JSONDecodeError, FileNotFoundError):
                    continue

        return results

    def _build_calibration_curve(self) -> Dict[str, Tuple[float, float]]:
        """Build calibration curve by predicted EV buckets.

        Returns:
            Dictionary mapping EV bucket to (actual_win_rate, adjustment_factor)
        """
        # Group bets by predicted EV buckets
        buckets = {
            "0-10": [],
            "10-25": [],
            "25-50": [],
            "50-75": [],
            "75+": []
        }

        for result in self.calibration_data:
            ev = result["predicted_ev"]
            won = result["won"]

            # Categorize into buckets
            if ev < 10:
                buckets["0-10"].append(won)
            elif ev < 25:
                buckets["10-25"].append(won)
            elif ev < 50:
                buckets["25-50"].append(won)
            elif ev < 75:
                buckets["50-75"].append(won)
            else:
                buckets["75+"].append(won)

        # Calculate actual win rates and adjustment factors
        calibration = {}
        bucket_midpoints = {
            "0-10": 5.0,
            "10-25": 17.5,
            "25-50": 37.5,
            "50-75": 62.5,
            "75+": 87.5
        }

        for bucket, wins in buckets.items():
            if len(wins) >= 5:  # Minimum 5 bets required for statistical reliability
                actual_win_rate = (sum(wins) / len(wins)) * 100

                # Estimate predicted win rate at bucket midpoint
                # Formula: EV = (prob × decimal_odds) - 1
                # Rearranged: prob = (EV + 1) / decimal_odds
                # Using average odds of 1.95 (approximately -105 American odds)
                predicted_prob = ((bucket_midpoints[bucket] / 100) + 1) / 1.95 * 100

                # Adjustment factor: how much to scale future predictions
                # Example: If we predicted 60% but only won 45%, factor = 0.75
                if predicted_prob > 0:
                    adjustment_factor = actual_win_rate / predicted_prob
                else:
                    adjustment_factor = 0.85  # Conservative default when no valid prediction

                calibration[bucket] = (actual_win_rate, adjustment_factor)

        return calibration

    def _calculate_market_adjustments(self) -> Dict[str, float]:
        """Calculate market-specific adjustments based on historical performance.

        Returns:
            Dictionary mapping market type to adjustment multiplier
        """
        market_performance = defaultdict(list)

        # Group results by market type
        for result in self.calibration_data:
            market = result.get("bet_type", "unknown")
            if market != "unknown":
                market_performance[market].append(result["won"])

        # Calculate win rates and adjustment factors
        adjustments = {}
        for market, wins in market_performance.items():
            if len(wins) >= 10:  # Minimum sample size
                win_rate = sum(wins) / len(wins)
                # If market wins at 35% but we expect 50%, adjust down by 0.70
                baseline = 0.50  # Expected 50% win rate at fair odds
                adjustments[market] = win_rate / baseline

        return adjustments

    def calibrate_probability(
        self,
        raw_probability: float,
        predicted_ev: float,
        bet_type: str = "unknown"
    ) -> float:
        """Apply Bayesian calibration to raw probability estimate.

        Args:
            raw_probability: Uncalibrated probability (0-100)
            predicted_ev: Predicted EV percentage
            bet_type: Type of bet for market-specific adjustment

        Returns:
            Calibrated probability (0-100)
        """
        # Determine which EV bucket this bet falls into
        if predicted_ev < 10:
            bucket = "0-10"
        elif predicted_ev < 25:
            bucket = "10-25"
        elif predicted_ev < 50:
            bucket = "25-50"
        elif predicted_ev < 75:
            bucket = "50-75"
        else:
            bucket = "75+"

        # Apply bucket-based calibration if available
        if bucket in self.calibration_curve:
            actual_rate, adjustment_factor = self.calibration_curve[bucket]

            # Weighted blend: 70% historical learning + 30% raw estimate
            # Prevents over-fitting to small samples while still learning from history
            # Example: raw=60%, adjustment=0.8 → calibrated = (0.7×60×0.8) + (0.3×60) = 51.6%
            calibrated_prob = (0.70 * raw_probability * adjustment_factor) + \
                             (0.30 * raw_probability)
        else:
            # No historical data for this bucket, apply conservative 15% haircut
            calibrated_prob = raw_probability * 0.85

        # Apply market-specific adjustment if available
        if bet_type in self.market_adjustments:
            market_adj = self.market_adjustments[bet_type]
            calibrated_prob *= market_adj

        # Bound probability between 5% and 95%
        calibrated_prob = max(5.0, min(95.0, calibrated_prob))

        return calibrated_prob

    def get_calibration_stats(self) -> Dict:
        """Get statistics about calibration data.

        Returns:
            Dictionary with calibration statistics for reporting
        """
        total_bets = len(self.calibration_data)

        if total_bets == 0:
            return {
                "total_bets": 0,
                "calibration_available": False,
                "message": "No historical data available for calibration"
            }

        overall_win_rate = sum(1 for b in self.calibration_data if b["won"]) / total_bets * 100

        # Calculate stats by bucket
        bucket_stats = {}
        for bucket, (actual_rate, adjustment) in self.calibration_curve.items():
            bucket_stats[bucket] = {
                "actual_win_rate": round(actual_rate, 2),
                "adjustment_factor": round(adjustment, 3)
            }

        return {
            "total_bets": total_bets,
            "overall_win_rate": round(overall_win_rate, 2),
            "calibration_available": True,
            "bucket_stats": bucket_stats,
            "markets_tracked": list(self.market_adjustments.keys())
        }
