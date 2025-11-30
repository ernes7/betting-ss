"""Aggregate statistics utility for calculating hit rates across all analyzed games."""

from typing import Dict, List, Optional
from shared.repositories import AnalysisRepository


class AggregateStats:
    """Aggregate statistics across all analyzed games.

    Calculates overall hit rate, ROI, and performance metrics
    for both AI and EV prediction systems without any AI calls.
    """

    def __init__(self, sport_code: str):
        """Initialize aggregate stats utility.

        Args:
            sport_code: Sport identifier (e.g., 'nfl')
        """
        self.sport_code = sport_code
        self.analysis_repo = AnalysisRepository(sport_code)

    def calculate_aggregate(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Dict:
        """Calculate aggregate stats across all games.

        Args:
            date_from: Optional start date filter (YYYY-MM-DD)
            date_to: Optional end date filter (YYYY-MM-DD)

        Returns:
            Dictionary with aggregate statistics for both systems
        """
        # Initialize accumulators
        ai_totals = self._init_system_totals()
        ev_totals = self._init_system_totals()
        bet_type_stats = {}
        games_analyzed = 0
        games_ai_won = 0
        games_ev_won = 0
        games_tied = 0

        # Get all analysis dates
        all_dates = self.analysis_repo.get_all_analysis_dates()

        # Filter by date range if specified
        if date_from or date_to:
            all_dates = self._filter_dates(all_dates, date_from, date_to)

        # Process each date
        for game_date in all_dates:
            analyses = self.analysis_repo.list_analyses_for_date(game_date)

            for analysis in analyses:
                games_analyzed += 1

                # Process AI system
                if "ai_system" in analysis:
                    self._accumulate_system_stats(
                        ai_totals,
                        analysis["ai_system"],
                        bet_type_stats,
                        "ai"
                    )

                # Process EV system
                if "ev_system" in analysis:
                    self._accumulate_system_stats(
                        ev_totals,
                        analysis["ev_system"],
                        bet_type_stats,
                        "ev"
                    )

                # Track which system won this game
                comparison = analysis.get("comparison", {})
                better = comparison.get("better_system")
                if better == "ai":
                    games_ai_won += 1
                elif better == "ev":
                    games_ev_won += 1
                else:
                    games_tied += 1

        # Calculate final metrics
        ai_stats = self._calculate_final_stats(ai_totals)
        ev_stats = self._calculate_final_stats(ev_totals)

        # Calculate bet type breakdown
        bet_type_breakdown = self._calculate_bet_type_breakdown(bet_type_stats)

        return {
            "games_analyzed": games_analyzed,
            "ai_system": ai_stats,
            "ev_system": ev_stats,
            "by_bet_type": bet_type_breakdown,
            "comparison": {
                "games_ai_won": games_ai_won,
                "games_ev_won": games_ev_won,
                "games_tied": games_tied,
                "better_system": "ai" if ai_stats["roi_percent"] > ev_stats["roi_percent"] else "ev",
                "roi_advantage": abs(ai_stats["roi_percent"] - ev_stats["roi_percent"])
            }
        }

    def _init_system_totals(self) -> Dict:
        """Initialize totals accumulator for a system."""
        return {
            "total_bets": 0,
            "bets_won": 0,
            "bets_lost": 0,
            "total_profit": 0.0,
            "total_staked": 0.0,
            "predicted_ev_sum": 0.0,
            "predicted_ev_count": 0
        }

    def _accumulate_system_stats(
        self,
        totals: Dict,
        system_data: Dict,
        bet_type_stats: Dict,
        system_name: str
    ):
        """Accumulate stats from a single game's system data.

        Args:
            totals: Running totals to update
            system_data: The ai_system or ev_system dict from analysis
            bet_type_stats: Bet type breakdown to update
            system_name: 'ai' or 'ev'
        """
        summary = system_data.get("summary", {})

        totals["total_bets"] += summary.get("total_bets", 0)
        totals["bets_won"] += summary.get("bets_won", 0)
        totals["bets_lost"] += summary.get("bets_lost", 0)
        totals["total_profit"] += summary.get("total_profit", 0.0)
        totals["total_staked"] += summary.get("total_staked", 0.0)

        # Track predicted EV for calibration analysis
        avg_ev = summary.get("avg_predicted_ev", 0)
        if avg_ev:
            totals["predicted_ev_sum"] += avg_ev
            totals["predicted_ev_count"] += 1

        # Process individual bet results for bet type breakdown
        bet_results = system_data.get("bet_results", [])
        for bet in bet_results:
            bet_type = bet.get("bet_type", "unknown")
            if bet_type not in bet_type_stats:
                bet_type_stats[bet_type] = {
                    "ai_wins": 0, "ai_total": 0, "ai_profit": 0.0,
                    "ev_wins": 0, "ev_total": 0, "ev_profit": 0.0
                }

            stats = bet_type_stats[bet_type]
            stats[f"{system_name}_total"] += 1
            stats[f"{system_name}_profit"] += bet.get("profit", 0.0)
            if bet.get("won") is True:
                stats[f"{system_name}_wins"] += 1

    def _calculate_final_stats(self, totals: Dict) -> Dict:
        """Calculate final stats from accumulated totals.

        Args:
            totals: Accumulated totals

        Returns:
            Final statistics dictionary
        """
        total_bets = totals["total_bets"]
        bets_won = totals["bets_won"]
        bets_lost = totals["bets_lost"]
        total_profit = totals["total_profit"]
        total_staked = totals["total_staked"]

        hit_rate = (bets_won / total_bets * 100) if total_bets > 0 else 0
        roi_percent = (total_profit / total_staked * 100) if total_staked > 0 else 0
        avg_predicted_ev = (
            totals["predicted_ev_sum"] / totals["predicted_ev_count"]
            if totals["predicted_ev_count"] > 0 else 0
        )

        return {
            "total_bets": total_bets,
            "bets_won": bets_won,
            "bets_lost": bets_lost,
            "hit_rate": round(hit_rate, 1),
            "total_profit": round(total_profit, 2),
            "total_staked": round(total_staked, 2),
            "roi_percent": round(roi_percent, 1),
            "avg_predicted_ev": round(avg_predicted_ev, 1)
        }

    def _calculate_bet_type_breakdown(self, bet_type_stats: Dict) -> Dict:
        """Calculate hit rate breakdown by bet type.

        Args:
            bet_type_stats: Raw bet type statistics

        Returns:
            Formatted bet type breakdown
        """
        breakdown = {}
        for bet_type, stats in bet_type_stats.items():
            ai_total = stats["ai_total"]
            ev_total = stats["ev_total"]
            ai_hit_rate = (stats["ai_wins"] / ai_total * 100) if ai_total > 0 else 0
            ev_hit_rate = (stats["ev_wins"] / ev_total * 100) if ev_total > 0 else 0

            breakdown[bet_type] = {
                "ai_wins": stats["ai_wins"],
                "ai_total": ai_total,
                "ai_hit_rate": round(ai_hit_rate, 1),
                "ai_profit": round(stats["ai_profit"], 2),
                "ev_wins": stats["ev_wins"],
                "ev_total": ev_total,
                "ev_hit_rate": round(ev_hit_rate, 1),
                "ev_profit": round(stats["ev_profit"], 2)
            }

        return breakdown

    def _filter_dates(
        self,
        dates: List[str],
        date_from: Optional[str],
        date_to: Optional[str]
    ) -> List[str]:
        """Filter dates by range.

        Args:
            dates: List of date strings (YYYY-MM-DD)
            date_from: Start date (inclusive)
            date_to: End date (inclusive)

        Returns:
            Filtered list of dates
        """
        filtered = []
        for date in dates:
            if date_from and date < date_from:
                continue
            if date_to and date > date_to:
                continue
            filtered.append(date)
        return filtered
