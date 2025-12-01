"""Bet checker component for the Analysis service.

Wraps the shared bet_result_checker functionality with constructor injection
for configuration management.
"""

from typing import Any, Dict, List, Optional

from services.analysis.config import MatchingConfig, ProfitConfig
from shared.utils.bet_result_checker import (
    normalize_bet,
    check_player_prop,
    check_spread_bet,
    check_total_bet,
    check_anytime_td,
    check_bets,
    calculate_profit,
    find_player_in_table,
    name_similarity,
    normalize_name,
    get_name_variants,
)


class BetChecker:
    """Component for checking bet results against game outcomes.

    This class wraps the shared bet_result_checker functionality and provides
    a configurable interface for validating predictions.

    Attributes:
        matching_config: Configuration for player name matching
        profit_config: Configuration for profit calculations
    """

    def __init__(
        self,
        matching_config: Optional[MatchingConfig] = None,
        profit_config: Optional[ProfitConfig] = None,
    ):
        """Initialize BetChecker with configuration.

        Args:
            matching_config: Player name matching configuration
            profit_config: Profit calculation configuration
        """
        self.matching_config = matching_config or MatchingConfig()
        self.profit_config = profit_config or ProfitConfig()

    def check_all_bets(
        self,
        prediction_data: Dict[str, Any],
        result_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Check all bets in a prediction against game results.

        Args:
            prediction_data: The prediction JSON with bets array
            result_data: The game results JSON with tables and final_score

        Returns:
            Analysis dict with bet_results and summary
        """
        # Use the shared check_bets function
        result = check_bets(prediction_data, result_data)

        # Recalculate summary with our configured stake
        bet_results = result.get("bet_results", [])
        self._recalculate_summary(result, bet_results)

        return result

    def check_single_bet(
        self,
        bet: Dict[str, Any],
        result_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Check a single bet against game results.

        Args:
            bet: The bet dict with market, player, line, side, odds
            result_data: The game results with tables and final_score

        Returns:
            Dict with won, actual, line, profit
        """
        # Normalize the bet format first
        normalized_bet = normalize_bet(bet)

        bet_type = normalized_bet.get("bet_type", "player_prop")

        if bet_type == "player_prop":
            return check_player_prop(normalized_bet, result_data)
        elif bet_type == "spread":
            return check_spread_bet(normalized_bet, result_data)
        elif bet_type == "total":
            return check_total_bet(normalized_bet, result_data)
        elif bet_type == "team_total":
            return check_total_bet(normalized_bet, result_data)
        elif bet_type == "moneyline":
            bet_copy = normalized_bet.copy()
            bet_copy["line"] = 0
            return check_spread_bet(bet_copy, result_data)
        else:
            return {
                "bet": normalized_bet.get("description", "Unknown bet"),
                "won": None,
                "actual": None,
                "line": normalized_bet.get("line"),
                "profit": 0,
                "error": f"Unknown bet type: {bet_type}"
            }

    def normalize_bet(self, bet: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a bet from AI format to EV format.

        AI predictions have free-text: {"bet": "Player Over 70.5 Receiving Yards"}
        EV predictions have structured: {"market": "receiving_yards", "player": "..."}

        Args:
            bet: The bet dict to normalize

        Returns:
            Normalized bet dict with structured fields
        """
        return normalize_bet(bet)

    def find_player(
        self,
        player_name: str,
        table_data: List[Dict[str, Any]],
        threshold: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """Find a player in a table by fuzzy name matching.

        Args:
            player_name: The player name to search for
            table_data: List of row dicts from the results table
            threshold: Optional custom threshold (uses config default if not provided)

        Returns:
            The matching row dict, or None if not found
        """
        actual_threshold = threshold or self.matching_config.name_similarity_threshold
        return find_player_in_table(player_name, table_data, actual_threshold)

    def calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity ratio between two names.

        Tries nickname variations to improve matching.

        Args:
            name1: First player name
            name2: Second player name

        Returns:
            Similarity ratio between 0.0 and 1.0
        """
        return name_similarity(name1, name2)

    def calculate_profit(
        self,
        won: bool,
        odds: int,
        stake: Optional[float] = None,
    ) -> float:
        """Calculate profit/loss based on American odds.

        Args:
            won: Whether the bet won
            odds: American odds (e.g., -110, +150)
            stake: Bet amount (uses config default if not provided)

        Returns:
            Profit/loss amount (positive for win, negative for loss)
        """
        actual_stake = stake if stake is not None else self.profit_config.default_stake
        return calculate_profit(won, odds, actual_stake)

    def _recalculate_summary(
        self,
        result: Dict[str, Any],
        bet_results: List[Dict[str, Any]],
    ) -> None:
        """Recalculate summary statistics with configured stake.

        Args:
            result: The result dict to update
            bet_results: List of bet results
        """
        total_bets = len(bet_results)
        bets_won = sum(1 for r in bet_results if r.get("won") is True)
        bets_lost = sum(1 for r in bet_results if r.get("won") is False)

        # Recalculate profit with configured stake
        total_profit = sum(r.get("profit", 0) for r in bet_results)
        total_staked = total_bets * self.profit_config.default_stake

        win_rate = (bets_won / total_bets * 100) if total_bets > 0 else 0
        roi = (total_profit / total_staked * 100) if total_staked > 0 else 0

        result["summary"] = {
            "total_bets": total_bets,
            "bets_won": bets_won,
            "bets_lost": bets_lost,
            "win_rate": round(win_rate, 1),
            "total_profit": round(total_profit, 2),
            "total_staked": total_staked,
            "roi_percent": round(roi, 1),
        }

    def format_results_markdown(self, analysis_result: Dict[str, Any]) -> str:
        """Format analysis results as markdown.

        Args:
            analysis_result: The analysis result from check_all_bets

        Returns:
            Markdown-formatted string
        """
        summary = analysis_result.get("summary", {})
        bet_results = analysis_result.get("bet_results", [])

        lines = [
            "# Bet Analysis Results",
            "",
            "## Summary",
            "",
            f"- **Total Bets**: {summary.get('total_bets', 0)}",
            f"- **Won**: {summary.get('bets_won', 0)}",
            f"- **Lost**: {summary.get('bets_lost', 0)}",
            f"- **Win Rate**: {summary.get('win_rate', 0)}%",
            f"- **Total Profit**: ${summary.get('total_profit', 0):.2f}",
            f"- **Total Staked**: ${summary.get('total_staked', 0):.2f}",
            f"- **ROI**: {summary.get('roi_percent', 0)}%",
            "",
            "## Bet Details",
            "",
        ]

        for i, bet in enumerate(bet_results, 1):
            won = bet.get("won")
            status = "✅ WON" if won is True else "❌ LOST" if won is False else "⏸️ PUSH"
            profit = bet.get("profit", 0)
            profit_str = f"+${profit:.2f}" if profit > 0 else f"-${abs(profit):.2f}" if profit < 0 else "$0.00"

            lines.append(f"### Bet {i}: {bet.get('bet', 'Unknown')}")
            lines.append(f"- **Status**: {status}")
            lines.append(f"- **Line**: {bet.get('line', 'N/A')}")
            lines.append(f"- **Actual**: {bet.get('actual', 'N/A')}")
            lines.append(f"- **Profit**: {profit_str}")
            if bet.get("error"):
                lines.append(f"- **Error**: {bet['error']}")
            lines.append("")

        return "\n".join(lines)
