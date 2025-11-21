"""Calculate true probabilities for different bet types using statistical models."""

from typing import Dict, Any, Optional
import math
import statistics


class ProbabilityCalculator:
    """Statistical models for calculating true probabilities of bets."""

    # Base variance multipliers by stat type (replaced fixed 30%)
    BASE_VARIANCE = {
        "passing_yards": 0.28,    # QBs relatively consistent
        "rushing_yards": 0.35,    # RBs high variance
        "receiving_yards": 0.42,  # WRs highest variance
        "receptions": 0.22,       # Receptions most consistent
        "anytime_td": 0.85        # TDs extremely variable
    }

    @staticmethod
    def calculate_probability(bet: Dict[str, Any], stats: Dict[str, Any]) -> float:
        """Calculate true probability for any bet type.

        Args:
            bet: Bet dictionary from BetParser
            stats: Relevant statistics for the bet

        Returns:
            True probability as percentage (0-100)
        """
        bet_type = bet.get("bet_type")

        if bet_type == "moneyline":
            return ProbabilityCalculator.calculate_moneyline_prob(bet, stats)
        elif bet_type == "spread":
            return ProbabilityCalculator.calculate_spread_prob(bet, stats)
        elif bet_type == "total":
            return ProbabilityCalculator.calculate_total_prob(bet, stats)
        elif bet_type == "player_prop":
            return ProbabilityCalculator.calculate_player_prop_prob(bet, stats)
        else:
            return 0.0

    @staticmethod
    def calculate_moneyline_prob(bet: Dict[str, Any], stats: Dict[str, Any]) -> float:
        """Calculate win probability for moneyline bet.

        Uses point differential between teams to estimate win probability.

        Args:
            bet: Moneyline bet info
            stats: Team offensive/defensive stats

        Returns:
            Win probability (0-100)
        """
        team_stats = stats.get("team_stats", {})
        opponent_stats = stats.get("opponent_stats", {})

        # Get scoring averages
        team_ppg = float(team_stats.get("points_per_g", 20.0))
        opp_ppg = float(opponent_stats.get("points_per_g", 20.0))

        # Get defensive stats (points allowed)
        team_def_ppg = float(team_stats.get("points_allowed_per_g", 22.0))
        opp_def_ppg = float(opponent_stats.get("points_allowed_per_g", 22.0))

        # Estimated point differential
        # Team expected score = (their offense + opponent's defense allowed) / 2
        team_expected = (team_ppg + opp_def_ppg) / 2
        opp_expected = (opp_ppg + team_def_ppg) / 2

        point_diff = team_expected - opp_expected

        # Convert point differential to win probability
        # Rule of thumb: each point is worth ~3-4% win probability
        # Using logistic function for more realistic probabilities
        win_prob = 50 + (point_diff * 3.3)

        # Bound between 5% and 95%
        win_prob = max(5.0, min(95.0, win_prob))

        return win_prob

    @staticmethod
    def calculate_spread_prob(bet: Dict[str, Any], stats: Dict[str, Any]) -> float:
        """Calculate probability of covering the spread.

        Args:
            bet: Spread bet info
            stats: Team stats

        Returns:
            Cover probability (0-100)
        """
        team_stats = stats.get("team_stats", {})
        opponent_stats = stats.get("opponent_stats", {})
        spread_line = bet.get("line", 0)

        # Calculate expected point differential (same as moneyline)
        team_ppg = float(team_stats.get("points_per_g", 20.0))
        opp_ppg = float(opponent_stats.get("points_per_g", 20.0))
        team_def_ppg = float(team_stats.get("points_allowed_per_g", 22.0))
        opp_def_ppg = float(opponent_stats.get("points_allowed_per_g", 22.0))

        team_expected = (team_ppg + opp_def_ppg) / 2
        opp_expected = (opp_ppg + team_def_ppg) / 2
        expected_diff = team_expected - opp_expected

        # Adjust for spread line
        # If team is favored by -7.5 but we expect them to win by 10, good bet
        diff_from_spread = expected_diff - spread_line

        # Convert to probability (each point = ~3.3%)
        cover_prob = 50 + (diff_from_spread * 3.3)

        # Bound between 5% and 95%
        cover_prob = max(5.0, min(95.0, cover_prob))

        return cover_prob

    @staticmethod
    def calculate_total_prob(bet: Dict[str, Any], stats: Dict[str, Any]) -> float:
        """Calculate probability of over/under total points.

        Args:
            bet: Total bet info (over or under)
            stats: Both teams' offensive stats and drive efficiency

        Returns:
            Over/under probability (0-100)
        """
        team_stats = stats.get("team_stats", {})
        opponent_stats = stats.get("opponent_stats", {})
        total_line = bet.get("line", 45.0)
        side = bet.get("side", "over")

        # Expected total points (base)
        team_ppg = float(team_stats.get("points_per_g", 20.0))
        opp_ppg = float(opponent_stats.get("points_per_g", 20.0))

        expected_total = team_ppg + opp_ppg

        # Adjust for drive efficiency (from team_stats.json)
        team_drive_eff = stats.get("team_drive_eff", {})
        opp_drive_eff = stats.get("opponent_drive_eff", {})

        if team_drive_eff and opp_drive_eff:
            # Teams with high score% tend to score more points
            team_score_pct = team_drive_eff.get("score_pct", 35.0)
            opp_score_pct = opp_drive_eff.get("score_pct", 35.0)

            # Adjust expected total based on scoring efficiency
            # Teams with 45%+ score pct are elite, 25%- are poor
            team_score_mult = 1.0 + ((team_score_pct - 35.0) * 0.01)  # ±1% per % above/below avg
            opp_score_mult = 1.0 + ((opp_score_pct - 35.0) * 0.01)

            # Apply multipliers
            expected_total = (team_ppg * team_score_mult) + (opp_ppg * opp_score_mult)

        # Standard deviation (NFL game totals typically have ~10-14 point std dev)
        std_dev = 12.0

        # Calculate z-score
        z_score = (total_line - expected_total) / std_dev

        # Convert to probability using normal CDF
        if side == "over":
            prob = (1 - ProbabilityCalculator._normal_cdf(z_score)) * 100
        else:  # under
            prob = ProbabilityCalculator._normal_cdf(z_score) * 100

        # Bound between 5% and 95%
        prob = max(5.0, min(95.0, prob))

        return prob

    @staticmethod
    def calculate_player_prop_prob(bet: Dict[str, Any], stats: Dict[str, Any]) -> float:
        """Calculate probability for player prop bets.

        Args:
            bet: Player prop bet info
            stats: Player stats and context

        Returns:
            Probability (0-100)
        """
        market = bet.get("market", "")

        if market == "passing_yards":
            return ProbabilityCalculator.calculate_passing_yards_prob(bet, stats)
        elif market == "rushing_yards":
            return ProbabilityCalculator.calculate_rushing_yards_prob(bet, stats)
        elif market == "receiving_yards":
            return ProbabilityCalculator.calculate_receiving_yards_prob(bet, stats)
        elif market == "receptions":
            return ProbabilityCalculator.calculate_reception_prob(bet, stats)
        elif market == "anytime_td":
            return ProbabilityCalculator.calculate_td_prob(bet, stats)
        elif market in ["passing_tds", "pass_td"]:
            return ProbabilityCalculator.calculate_passing_td_prob(bet, stats)
        else:
            # Generic milestone calculation for other props
            return ProbabilityCalculator.calculate_generic_milestone_prob(bet, stats)

    @staticmethod
    def get_adaptive_std_dev(
        market: str,
        player_role: str,
        spread: float,
        base_avg: float
    ) -> float:
        """Calculate context-aware standard deviation.

        Args:
            market: Stat type (e.g., "passing_yards", "rushing_yards")
            player_role: Player role classification ("WR1", "RB2", etc.)
            spread: Game spread (positive = favorite)
            base_avg: Player's average for this stat

        Returns:
            Standard deviation as actual value (not multiplier)
        """
        # Get base variance multiplier for this market
        std_dev_mult = ProbabilityCalculator.BASE_VARIANCE.get(market, 0.30)

        # Adjustment 1: Player role (starters more consistent)
        if player_role in ["QB1", "RB1", "WR1", "TE1"]:
            std_dev_mult *= 0.90  # 10% less variance
        elif player_role in ["RB2", "WR2"]:
            std_dev_mult *= 1.10  # 10% more variance
        elif player_role in ["WR3", "RB3", "TE2"]:
            std_dev_mult *= 1.25  # 25% more variance (boom/bust)

        # Adjustment 2: Game spread (blowout risk increases variance)
        abs_spread = abs(spread)
        if abs_spread >= 14:
            std_dev_mult *= 1.35  # 35% more variance in expected blowouts
        elif abs_spread >= 10:
            std_dev_mult *= 1.25  # 25% more variance
        elif abs_spread >= 7:
            std_dev_mult *= 1.15  # 15% more variance
        elif abs_spread <= 3:
            std_dev_mult *= 0.95  # 5% less variance in close games

        # Bound multiplier between 0.18 and 0.50
        std_dev_mult = max(0.18, min(0.50, std_dev_mult))

        # Return actual std dev value
        return base_avg * std_dev_mult

    @staticmethod
    def _get_defense_multiplier(opponent_def_rank: int, advanced_stats: Optional[Dict] = None) -> float:
        """Get defense multiplier using continuous curve with advanced adjustments.

        Args:
            opponent_def_rank: Defense rank 1-32 (1 = best, 32 = worst)
            advanced_stats: Optional advanced defense stats (pressure, sacks, etc.)

        Returns:
            Multiplier: <1.0 for good defenses, >1.0 for poor defenses

        Formula: multiplier = 1.0 + ((rank - 16) × 0.0125)
        Examples:
            Rank 1:  0.8125 (-18.75%)
            Rank 8:  0.9000 (-10%)
            Rank 16: 1.0000 (neutral)
            Rank 24: 1.1000 (+10%)
            Rank 32: 1.2000 (+20%)
        """
        # Base multiplier: continuous curve (no tiers)
        base_mult = 1.0 + ((opponent_def_rank - 16) * 0.0125)

        # Apply advanced stat adjustments if available
        if advanced_stats:
            # Pressure rate adjustment (passing only)
            pressure_rate = advanced_stats.get("pressure_pct", 0)
            if pressure_rate:
                # Remove '%' if present and convert to float
                pressure_rate = float(str(pressure_rate).replace('%', ''))
                # Each 1% above 22.5% avg = -1.5% production
                pressure_adj = 1.0 - ((pressure_rate - 22.5) * 0.015)
                base_mult *= max(0.85, min(1.15, pressure_adj))

            # Sack rate adjustment (passing only)
            sacks = advanced_stats.get("sacks", 0)
            if sacks:
                # Estimate sacks per game (assume ~9 games)
                sacks_per_game = sacks / 9.0
                # Each sack/game above 3.0 = -2% production
                sack_adj = 1.0 - ((sacks_per_game - 3.0) * 0.02)
                base_mult *= max(0.85, min(1.15, sack_adj))

        # Bound final multiplier between 0.65 and 1.40
        return max(0.65, min(1.40, base_mult))

    @staticmethod
    def calculate_passing_yards_prob(bet: Dict[str, Any], stats: Dict[str, Any]) -> float:
        """Calculate probability of QB passing yards over/under line.

        Uses normal distribution with player's average and variance.

        Args:
            bet: Passing yards bet
            stats: QB stats and opponent defense

        Returns:
            Probability (0-100)
        """
        player_avg = stats.get("player_averages", {}).get("pass_yds_per_g", 0)
        line = bet.get("line", 250)
        side = bet.get("side", "over")

        if player_avg == 0:
            return 0.0

        # Adjust for opponent defense (with advanced stats if available)
        opponent_def_rank = stats.get("opponent_def_rank", 16)
        advanced_def_stats = {
            "pressure_pct": stats.get("opponent_pressure_rate", 22.5),
            "sacks": stats.get("opponent_sack_total", 0)
        }
        defense_multiplier = ProbabilityCalculator._get_defense_multiplier(
            opponent_def_rank,
            advanced_stats=advanced_def_stats
        )

        # Adjust for team offensive quality
        team_offense_rank = stats.get("team_offense_rank", 16)
        # Better offense (rank 1) increases production, worse offense (rank 32) decreases
        offense_multiplier = 1.0 + ((16 - team_offense_rank) * 0.015)  # ±1.5% per rank

        # Apply adjustments (pressure & sacks now handled in defense_multiplier)
        adjusted_avg = player_avg * defense_multiplier * offense_multiplier

        # Adaptive standard deviation based on context
        player_role = stats.get("player_role", "QB1")  # Assume QB1 if not specified
        spread_line = stats.get("spread_line", 0)  # Game spread (fixed: use spread_line consistently)
        std_dev = ProbabilityCalculator.get_adaptive_std_dev(
            market="passing_yards",
            player_role=player_role,
            spread=spread_line,
            base_avg=adjusted_avg
        )

        # Calculate probability using normal distribution
        over_prob = ProbabilityCalculator._calculate_over_probability(line, adjusted_avg, std_dev)

        # Return over or under probability based on bet side
        if side == "under":
            return 100.0 - over_prob
        return over_prob

    @staticmethod
    def calculate_rushing_yards_prob(bet: Dict[str, Any], stats: Dict[str, Any]) -> float:
        """Calculate probability of rushing yards over/under line."""
        player_avg = stats.get("player_averages", {}).get("rush_yds_per_g", 0)
        line = bet.get("line", 60)
        side = bet.get("side", "over")
        position = stats.get("position", "")

        if player_avg == 0:
            return 0.0

        # Adjust for opponent defense
        opponent_def_rank = stats.get("opponent_def_rank", 16)
        defense_multiplier = ProbabilityCalculator._get_defense_multiplier(opponent_def_rank)

        # Adjust for team offensive quality
        team_offense_rank = stats.get("team_offense_rank", 16)
        offense_multiplier = 1.0 + ((16 - team_offense_rank) * 0.015)

        # Game script adjustment for QB rushing
        game_script_multiplier = 1.0
        spread_line = stats.get("spread_line", 0)

        if position == "QB" and spread_line <= -7.0:
            # QB on team favored by 7+ points - they protect leads, don't scramble
            game_script_multiplier = 0.65  # 35% penalty

        adjusted_avg = player_avg * defense_multiplier * offense_multiplier * game_script_multiplier

        # Adaptive standard deviation for rushing yards
        player_role = stats.get("player_role", "RB1" if position == "RB" else "QB1")
        std_dev = ProbabilityCalculator.get_adaptive_std_dev(
            market="rushing_yards",
            player_role=player_role,
            spread=spread_line,
            base_avg=adjusted_avg
        )

        over_prob = ProbabilityCalculator._calculate_over_probability(line, adjusted_avg, std_dev)

        # Return over or under probability based on bet side
        if side == "under":
            return 100.0 - over_prob
        return over_prob

    @staticmethod
    def calculate_receiving_yards_prob(bet: Dict[str, Any], stats: Dict[str, Any]) -> float:
        """Calculate probability of receiving yards over/under line."""
        player_avg = stats.get("player_averages", {}).get("rec_yds_per_g", 0)
        player_name = bet.get("player", "")
        line = bet.get("line", 60)
        side = bet.get("side", "over")
        position = stats.get("position", "")

        if player_avg == 0:
            return 0.0

        # Adjust for opponent defense
        opponent_def_rank = stats.get("opponent_def_rank", 16)
        defense_multiplier = ProbabilityCalculator._get_defense_multiplier(opponent_def_rank)

        # Adjust for team offensive quality
        team_offense_rank = stats.get("team_offense_rank", 16)
        offense_multiplier = 1.0 + ((16 - team_offense_rank) * 0.015)

        # Game script adjustment for RB receiving
        game_script_multiplier = 1.0
        spread_line = stats.get("spread_line", 0)
        rec_per_g = stats.get("player_averages", {}).get("rec_per_g", 0)

        if position == "RB":
            if spread_line >= 7.0:
                # RB on team that's +7 or worse underdog - losing teams abandon RB checkdowns
                game_script_multiplier = 0.75  # 25% penalty
            elif spread_line <= -7.0:
                # RB on team that's -7 or better favorite - winning teams run clock, fewer passes
                game_script_multiplier = 0.85  # 15% penalty

        # Low-volume receiver penalty for big underdogs
        if rec_per_g > 0 and rec_per_g < 3.0 and spread_line >= 7.0:
            # Low-volume receiver (< 3 rec/g) on big underdog (+7 or worse)
            # Gets completely phased out in blowouts
            game_script_multiplier *= 0.80  # Additional 20% penalty

        # Apply adjustments
        total_multiplier = (defense_multiplier * offense_multiplier *
                          game_script_multiplier)
        adjusted_avg = player_avg * total_multiplier

        # Adaptive standard deviation for receiving yards
        player_role = stats.get("player_role", "WR1" if position == "WR" else ("TE1" if position == "TE" else "RB2"))
        std_dev = ProbabilityCalculator.get_adaptive_std_dev(
            market="receiving_yards",
            player_role=player_role,
            spread=spread_line,
            base_avg=adjusted_avg
        )

        over_prob = ProbabilityCalculator._calculate_over_probability(line, adjusted_avg, std_dev)

        # Return over or under probability based on bet side
        if side == "under":
            return 100.0 - over_prob
        return over_prob

    @staticmethod
    def calculate_reception_prob(bet: Dict[str, Any], stats: Dict[str, Any]) -> float:
        """Calculate probability of receptions over/under line."""
        player_avg = stats.get("player_averages", {}).get("rec_per_g", 0)
        line = bet.get("line", 5)
        side = bet.get("side", "over")
        position = stats.get("position", "")

        if player_avg == 0:
            return 0.0

        # Adaptive standard deviation for receptions
        player_role = stats.get("player_role", "WR1" if position == "WR" else ("TE1" if position == "TE" else "RB2"))
        spread_line = stats.get("spread_line", 0)
        std_dev = ProbabilityCalculator.get_adaptive_std_dev(
            market="receptions",
            player_role=player_role,
            spread=spread_line,
            base_avg=player_avg
        )

        over_prob = ProbabilityCalculator._calculate_over_probability(line, player_avg, std_dev)

        # Return over or under probability based on bet side
        if side == "under":
            return 100.0 - over_prob
        return over_prob

    @staticmethod
    def calculate_td_prob(bet: Dict[str, Any], stats: Dict[str, Any]) -> float:
        """Calculate probability of anytime touchdown.

        Uses player's TD rate and game script context.

        Args:
            bet: TD bet info
            stats: Player stats

        Returns:
            TD probability (0-100)
        """
        # Get TD rate from stats
        player_stats = stats.get("player_averages", {})
        position = stats.get("position", "")

        # Calculate TD per game rate
        if "rush_td_per_g" in player_stats and player_stats["rush_td_per_g"] > 0:
            td_per_g = player_stats["rush_td_per_g"]
        elif "rec_td_per_g" in player_stats and player_stats["rec_td_per_g"] > 0:
            td_per_g = player_stats["rec_td_per_g"]
        elif "pass_td_per_g" in player_stats and player_stats["pass_td_per_g"] > 0:
            # QBs have higher TD rates but we're betting on rushing/receiving TDs
            td_per_g = player_stats.get("rush_td_per_g", 0) + player_stats.get("rec_td_per_g", 0)
        else:
            td_per_g = 0.1  # Very low default

        # Convert to probability (Poisson approximation)
        # P(X >= 1) = 1 - P(X = 0) = 1 - e^(-lambda)
        td_prob = (1 - math.exp(-td_per_g)) * 100

        # Bound between 2% and 80%
        td_prob = max(2.0, min(80.0, td_prob))

        return td_prob

    @staticmethod
    def calculate_passing_td_prob(bet: Dict[str, Any], stats: Dict[str, Any]) -> float:
        """Calculate probability of passing TDs over/under line."""
        player_avg = stats.get("player_averages", {}).get("pass_td_per_g", 0)
        line = bet.get("line", 1.5)
        side = bet.get("side", "over")

        if player_avg == 0:
            return 0.0

        # Passing TDs follow Poisson distribution
        # P(X > line) using normal approximation for continuous line values
        std_dev = math.sqrt(player_avg)  # Poisson variance = mean

        over_prob = ProbabilityCalculator._calculate_over_probability(line, player_avg, std_dev)

        # Return over or under probability based on bet side
        if side == "under":
            return 100.0 - over_prob
        return over_prob

    @staticmethod
    def calculate_generic_milestone_prob(bet: Dict[str, Any], stats: Dict[str, Any]) -> float:
        """Generic milestone probability for unspecified markets.

        Uses conservative estimation based on implied probability.

        Args:
            bet: Bet info
            stats: Any available stats

        Returns:
            Probability (0-100)
        """
        # Use implied probability as baseline and apply conservative adjustment
        implied_prob = bet.get("implied_prob", 50.0)

        # For unknown markets, be very conservative
        # Only mark as +EV if significantly better than implied
        return implied_prob * 0.75  # 25% conservative reduction

    @staticmethod
    def _calculate_over_probability(line: float, mean: float, std_dev: float) -> float:
        """Calculate probability of going over a line using normal distribution.

        Args:
            line: The betting line
            mean: Expected average
            std_dev: Standard deviation

        Returns:
            Probability of exceeding line (0-100)
        """
        if std_dev == 0:
            return 50.0 if line == mean else (0.0 if line > mean else 100.0)

        # Calculate z-score
        z_score = (line - mean) / std_dev

        # P(X > line) = 1 - CDF(line)
        prob = (1 - ProbabilityCalculator._normal_cdf(z_score)) * 100

        # Bound between 1% and 99%
        prob = max(1.0, min(99.0, prob))

        return prob

    @staticmethod
    def _normal_cdf(x: float) -> float:
        """Cumulative distribution function for standard normal distribution.

        Uses error function approximation.

        Args:
            x: Z-score

        Returns:
            CDF value (0-1)
        """
        return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0
