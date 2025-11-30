"""Validation rules for betting opportunities."""

from typing import Dict, Any, Tuple


class BetValidator:
    """Validates bets before EV calculation."""

    @staticmethod
    def is_valid_bet(bet: Dict[str, Any], stats: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if bet is valid for EV calculation.

        Args:
            bet: Bet dictionary
            stats: Stats dictionary for this bet

        Returns:
            (is_valid, reason) tuple
        """
        bet_type = bet.get("bet_type")

        if bet_type == "player_prop":
            return BetValidator.is_valid_player_bet(bet, stats)
        elif bet_type in ["moneyline", "spread", "total"]:
            return BetValidator.is_valid_game_bet(bet, stats)
        else:
            return True, "Valid"

    @staticmethod
    def is_valid_player_bet(bet: Dict[str, Any], stats: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate player prop bet.

        Args:
            bet: Player prop bet
            stats: Player stats

        Returns:
            (is_valid, reason) tuple
        """
        player_name = bet.get("player", "Unknown")
        market = bet.get("market", "")

        # Check if player stats exist
        player_averages = stats.get("player_averages")
        if not player_averages:
            return False, f"Player {player_name} not found in team profile"

        # Check injury status
        injury_status = stats.get("injury_status", "healthy")
        if injury_status in ["out", "injured_reserve"]:
            return False, f"{player_name} is {injury_status}"

        # Check minimum games played (allow 0+ games)
        player_stats = stats.get("player_stats", {}).get("stats", {})
        games = BetValidator._safe_int(player_stats.get("games", 0))

        # Relaxed requirement: allow players with any game time (including 0)
        if games < 0:
            return False, f"{player_name} has invalid games played data"

        # Check has relevant stat for market
        if not BetValidator._has_market_stat(market, player_averages):
            return False, f"{player_name} has no production in {market}"

        return True, "Valid"

    @staticmethod
    def is_valid_game_bet(bet: Dict[str, Any], stats: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate game-level bet (moneyline, spread, total).

        Args:
            bet: Game bet
            stats: Team stats

        Returns:
            (is_valid, reason) tuple
        """
        # Game bets are always valid if we have team stats
        team_stats = stats.get("team_stats", {})
        opp_stats = stats.get("opponent_stats", {})

        # Check if stats dicts exist and are not None
        if not team_stats or not opp_stats:
            return False, "Team stats are None or empty"

        # Validate required fields exist (not just that dicts exist)
        required_keys = ["points_per_g", "points_allowed_per_g"]
        for key in required_keys:
            if team_stats.get(key) is None:
                return False, f"Missing {key} in team stats"
            if opp_stats.get(key) is None:
                return False, f"Missing {key} in opponent stats"

        return True, "Valid"

    @staticmethod
    def _has_market_stat(market: str, player_averages: Dict[str, float]) -> bool:
        """Check if player has relevant stat for market.

        Args:
            market: Bet market (e.g., "passing_yards", "receptions")
            player_averages: Player averages dict

        Returns:
            True if player has production in this market
        """
        # Map markets to average fields
        market_map = {
            "passing_yards": "pass_yds_per_g",
            "passing_tds": "pass_td_per_g",
            "pass_completions": "pass_cmp_per_g",
            "pass_attempts": "pass_att_per_g",
            "rushing_yards": "rush_yds_per_g",
            "rushing_tds": "rush_td_per_g",
            "rush_attempts": "rush_att_per_g",
            "receiving_yards": "rec_yds_per_g",
            "receiving_tds": "rec_td_per_g",
            "receptions": "rec_per_g",
            "anytime_td": "rush_receive_td",  # Special case
        }

        # Get required field
        required_field = market_map.get(market)
        if not required_field:
            # Unknown market, allow it
            return True

        # Check if player has this stat and meaningful production
        avg_value = player_averages.get(required_field, 0)

        # For anytime_td, check if player has receiving/rushing usage (not TD history)
        # Players with 0 TDs but high usage (3+ rec/game or 30+ rush yds/game) can still score
        if market == "anytime_td":
            rec_pg = player_averages.get("rec_per_g", 0)
            rush_ypg = player_averages.get("rush_yds_per_g", 0)
            # Allow if player has meaningful offensive touches
            return rec_pg >= 3.0 or rush_ypg >= 30.0

        # Relax from > 0 to >= 0.1 to allow minimal but real production
        return avg_value >= 0.1

    @staticmethod
    def _safe_int(value: Any) -> int:
        """Safely convert value to int.

        Args:
            value: Value to convert

        Returns:
            Integer or 0
        """
        if value is None or value == "":
            return 0

        try:
            return int(value)
        except (ValueError, TypeError):
            return 0
