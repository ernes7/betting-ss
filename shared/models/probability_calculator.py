"""Calculate true probabilities for different bet types using statistical models."""

from typing import Dict, Any, Optional
import math


class ProbabilityCalculator:
    """Statistical models for calculating true probabilities of bets."""

    # Standard deviation multipliers for different variance levels
    # NFL player stats typically have 25-35% coefficient of variation
    STD_DEV_FACTOR = 0.30  # 30% of mean as standard deviation

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

        # Adjust for opponent defense
        opponent_def_rank = stats.get("opponent_def_rank", 16)
        # Better defense (rank 1) reduces production, worse defense (rank 32) increases
        defense_multiplier = 1.0 + ((opponent_def_rank - 16) * 0.015)  # ±1.5% per rank

        # Adjust for team offensive quality
        team_offense_rank = stats.get("team_offense_rank", 16)
        # Better offense (rank 1) increases production, worse offense (rank 32) decreases
        offense_multiplier = 1.0 + ((16 - team_offense_rank) * 0.015)  # ±1.5% per rank

        # Adjust for injured receivers (WRs/TEs)
        injured_receivers = stats.get("injured_receivers", [])
        injury_penalty = len(injured_receivers) * 0.05  # -5% per injured WR/TE

        # Adjust for injured offensive linemen
        injured_ol = stats.get("injured_ol", [])
        ol_penalty = len(injured_ol) * 0.03  # -3% per injured OL

        # Adjust for opponent pressure rate (from advanced_defense)
        pressure_rate = stats.get("opponent_pressure_rate", 22.5)  # League avg ~22.5%
        # High pressure (35%+) reduces yards, low pressure (15%-) increases yards
        pressure_multiplier = 1.0 - ((pressure_rate - 22.5) * 0.01)  # ±1% per % above/below average

        # Adjust for opponent sacks (indicates pass rush effectiveness)
        sack_total = stats.get("opponent_sack_total", 0)
        # Teams with 30+ sacks are elite pass rushers, 15- sacks are poor
        sacks_per_game = sack_total / 9  # Assume 9 games played
        sack_multiplier = 1.0 - ((sacks_per_game - 3.0) * 0.02)  # ±2% per sack above/below 3/game

        # Apply all adjustments
        total_multiplier = (defense_multiplier * offense_multiplier *
                          (1 - injury_penalty) * (1 - ol_penalty) *
                          pressure_multiplier * sack_multiplier)
        adjusted_avg = player_avg * total_multiplier

        # Standard deviation (typically 25-30% of mean for passing yards)
        std_dev = adjusted_avg * ProbabilityCalculator.STD_DEV_FACTOR

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
        defense_multiplier = 1.0 + ((opponent_def_rank - 16) * 0.015)

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

        # Rushing yards have higher variance (30-35% of mean)
        std_dev = adjusted_avg * 0.32

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
        defense_multiplier = 1.0 + ((opponent_def_rank - 16) * 0.015)

        # Adjust for team offensive quality
        team_offense_rank = stats.get("team_offense_rank", 16)
        offense_multiplier = 1.0 + ((16 - team_offense_rank) * 0.015)

        # Boost for injured teammates (more targets available)
        injured_receivers = stats.get("injured_receivers", [])
        # Don't count if this player is injured
        other_injured = [wr for wr in injured_receivers if wr != player_name]
        target_boost = len(other_injured) * 0.05  # +5% per other injured WR/TE

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
                          (1 + target_boost) * game_script_multiplier)
        adjusted_avg = player_avg * total_multiplier

        # Receiving yards variance (28-33% of mean)
        std_dev = adjusted_avg * 0.30

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

        if player_avg == 0:
            return 0.0

        # Receptions are more consistent (20-25% variance)
        std_dev = player_avg * 0.22

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
