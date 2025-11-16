"""Main EV calculator - orchestrates bet parsing, stat aggregation, and probability calculation."""

from typing import List, Dict, Any, Optional
from shared.models.bet_parser import BetParser
from shared.models.stat_aggregator import StatAggregator
from shared.models.probability_calculator import ProbabilityCalculator
from shared.models.bet_validator import BetValidator
from nfl.teams import PFR_ABBR_TO_NAME


class EVCalculator:
    """Calculate Expected Value for all betting opportunities."""

    def __init__(
        self,
        odds_data: Dict[str, Any],
        sport_config,
        base_dir: Optional[str] = None,
        conservative_adjustment: float = 0.85
    ):
        """Initialize EV calculator.

        Args:
            odds_data: Complete odds JSON data
            sport_config: Sport-specific configuration
            base_dir: Base directory for data files
            conservative_adjustment: Probability reduction factor (0.85 = 15% reduction)
        """
        self.odds_data = odds_data
        self.sport_config = sport_config
        self.conservative_adjustment = conservative_adjustment

        # Initialize components
        self.bet_parser = BetParser()
        self.stat_aggregator = StatAggregator(sport_config, base_dir)
        self.prob_calculator = ProbabilityCalculator()

        # Extract team info using PFR abbreviations
        teams = odds_data.get("teams", {})
        away_pfr = teams.get("away", {}).get("pfr_abbr", "")
        home_pfr = teams.get("home", {}).get("pfr_abbr", "")

        # Convert PFR abbreviations to full names for profile lookup
        self.away_team = PFR_ABBR_TO_NAME.get(away_pfr, teams.get("away", {}).get("name", ""))
        self.home_team = PFR_ABBR_TO_NAME.get(home_pfr, teams.get("home", {}).get("name", ""))

        # Load team data
        self.away_profile = self.stat_aggregator.load_team_profile(self.away_team)
        self.home_profile = self.stat_aggregator.load_team_profile(self.home_team)
        self.away_rankings = self.stat_aggregator.load_team_rankings(self.away_team)
        self.home_rankings = self.stat_aggregator.load_team_rankings(self.home_team)

    def calculate_all_ev(self, min_ev_threshold: float = 0.0) -> List[Dict[str, Any]]:
        """Calculate EV for all bets in odds file.

        Args:
            min_ev_threshold: Minimum EV percentage to include (default 0.0 = all bets)

        Returns:
            List of all bets with EV calculated, filtered by threshold
        """
        # Parse all bets
        all_bets = self.bet_parser.parse_all_bets(self.odds_data)

        # Calculate EV for each bet
        bets_with_ev = []
        for bet in all_bets:
            try:
                ev_result = self._calculate_bet_ev(bet)
                if ev_result and ev_result["ev_percent"] >= min_ev_threshold:
                    bets_with_ev.append(ev_result)
            except Exception as e:
                # Skip bets that error out (missing data, etc.)
                print(f"Error calculating EV for {bet.get('description', 'unknown bet')}: {e}")
                continue

        # Sort by EV (highest first)
        bets_with_ev.sort(key=lambda x: x["ev_percent"], reverse=True)

        return bets_with_ev

    def get_top_n(self, n: int = 10, min_ev_threshold: float = 3.0, deduplicate_players: bool = True) -> List[Dict[str, Any]]:
        """Get top N bets by EV.

        Args:
            n: Number of top bets to return
            min_ev_threshold: Minimum EV percentage (default 3.0%)
            deduplicate_players: If True, show only best bet per player (default True)

        Returns:
            Top N bets ranked by EV
        """
        all_bets = self.calculate_all_ev(min_ev_threshold)

        if deduplicate_players:
            seen_players = set()
            deduped_bets = []
            for bet in all_bets:  # Already sorted by EV descending
                bet_type = bet.get("bet_type")
                if bet_type == "player_prop":
                    player = bet.get("player", "")
                    if player and player not in seen_players:
                        seen_players.add(player)
                        deduped_bets.append(bet)
                else:
                    # Always keep game-level bets (moneyline, spread, total)
                    deduped_bets.append(bet)
            return deduped_bets[:n]

        return all_bets[:n]

    def _calculate_bet_ev(self, bet: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Calculate EV for a single bet.

        Args:
            bet: Bet dictionary from BetParser

        Returns:
            Bet with EV data added, or None if calculation fails
        """
        # Get relevant stats for this bet
        stats = self._get_bet_stats(bet)

        # Validate bet before calculation
        is_valid, reason = BetValidator.is_valid_bet(bet, stats)
        if not is_valid:
            # Skip invalid bets
            return None

        # Calculate true probability
        true_prob = self.prob_calculator.calculate_probability(bet, stats)

        # Apply conservative adjustment (reduce by 10-15%)
        adjusted_prob = self.stat_aggregator.apply_conservative_adjustment(
            true_prob,
            self.conservative_adjustment
        )

        # Convert probability to decimal (0-1 range)
        prob_decimal = adjusted_prob / 100

        # Calculate EV
        decimal_odds = bet.get("decimal_odds", 1.0)
        ev_decimal = (prob_decimal * decimal_odds) - 1
        ev_percent = ev_decimal * 100

        # Build result
        result = {
            **bet,  # Include all original bet data
            "true_prob": round(true_prob, 2),
            "adjusted_prob": round(adjusted_prob, 2),
            "ev_percent": round(ev_percent, 2),
            "reasoning": self._generate_reasoning(bet, stats, true_prob, adjusted_prob)
        }

        return result

    def _get_bet_stats(self, bet: Dict[str, Any]) -> Dict[str, Any]:
        """Get relevant statistics for a bet.

        Args:
            bet: Bet dictionary

        Returns:
            Dictionary with relevant stats for probability calculation
        """
        bet_type = bet.get("bet_type")
        stats = {}

        if bet_type in ["moneyline", "spread", "total"]:
            # Game-level bets need team stats
            stats["team_stats"] = self._get_team_aggregate_stats(self.away_team, self.away_profile, self.away_rankings)
            stats["opponent_stats"] = self._get_team_aggregate_stats(self.home_team, self.home_profile, self.home_rankings)

            # Add drive efficiency for total points bets
            if bet_type == "total":
                stats["team_drive_eff"] = self.stat_aggregator.get_team_drive_efficiency(self.away_team)
                stats["opponent_drive_eff"] = self.stat_aggregator.get_team_drive_efficiency(self.home_team)

            # For specific team bet, identify which team
            # If bet is for HOME team, swap (default is away team perspective)
            if "team_abbr" in bet:
                home_abbr = self.odds_data.get("teams", {}).get("home", {}).get("abbr")
                bet_abbr = bet["team_abbr"]
                if bet_abbr == home_abbr:
                    stats["team_stats"], stats["opponent_stats"] = stats["opponent_stats"], stats["team_stats"]

        elif bet_type == "player_prop":
            # Player prop needs player stats
            player_name = bet.get("player", "")
            team_abbr = (bet.get("team") or "").upper()
            market = bet.get("market", "")

            # Determine which team the player is on
            away_abbr = self.odds_data.get("teams", {}).get("away", {}).get("abbr")
            home_abbr = self.odds_data.get("teams", {}).get("home", {}).get("abbr")

            if team_abbr == away_abbr:
                player_profile = self.away_profile
                player_team = self.away_team
                opponent_team = self.home_team
                # Get spread from away team perspective (positive = underdog, negative = favorite)
                spread_line = self.odds_data.get("game_lines", {}).get("spread", {}).get("away", 0)
            else:
                player_profile = self.home_profile
                player_team = self.home_team
                opponent_team = self.away_team
                # Get spread from home team perspective
                spread_line = self.odds_data.get("game_lines", {}).get("spread", {}).get("home", 0)

            # Load player stats
            player_stats = self.stat_aggregator.load_player_stats(player_name, player_profile)

            if player_stats:
                stats["player_averages"] = self.stat_aggregator.get_player_averages(player_stats)
                stats["position"] = player_stats.get("position", "")
                stats["player_stats"] = player_stats  # Store for validator
                stats["spread_line"] = spread_line  # Game script context

                # Get opponent defense rank for relevant market
                defense_category = self._map_market_to_defense(market)
                if defense_category:
                    stats["opponent_def_rank"] = self.stat_aggregator.get_opponent_defense_rank(
                        opponent_team,
                        {},  # Rankings loaded separately
                        defense_category
                    ) or 16  # Default to middle rank

                # Get team offensive rank for relevant market
                offense_category = self._map_market_to_offense(market)
                if offense_category:
                    stats["team_offense_rank"] = self.stat_aggregator.get_team_offense_rank(
                        player_team,
                        {},  # Rankings loaded separately
                        offense_category
                    ) or 16  # Default to middle rank

                # Add advanced defense stats for QB props (passing yards, TDs)
                if market in ["passing_yards", "passing_tds", "pass_completions", "pass_attempts"]:
                    stats["opponent_pressure_rate"] = self.stat_aggregator.get_defense_pressure_rate(opponent_team)
                    stats["opponent_sack_total"] = self.stat_aggregator.get_defense_sack_total(opponent_team)
                    stats["opponent_blitz_rate"] = self.stat_aggregator.get_defense_blitz_rate(opponent_team)

        return stats

    def _get_team_aggregate_stats(
        self,
        team_name: str,
        profile: Dict[str, Any],
        rankings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Aggregate team-level stats for game bets.

        Args:
            team_name: Team name
            profile: Team profile data
            rankings: Team rankings data

        Returns:
            Aggregated team stats
        """
        stats = {}

        # Get scoring average (offensive points per game)
        stats["points_per_g"] = self.stat_aggregator.get_team_scoring_average(team_name)

        # Get defensive points allowed per game from team_defense table
        stats["points_allowed_per_g"] = self.stat_aggregator.get_team_points_allowed_per_game(team_name)

        return stats

    def _map_market_to_defense(self, market: str) -> Optional[str]:
        """Map prop market to defensive category.

        Args:
            market: Prop market (e.g., "passing_yards", "rushing_yards")

        Returns:
            Defense category or None
        """
        market_map = {
            "passing_yards": "passing",
            "pass_completions": "passing",
            "pass_attempts": "passing",
            "passing_tds": "passing",
            "rushing_yards": "rushing",
            "rush_attempts": "rushing",
            "rushing_tds": "rushing",
            "receiving_yards": "passing",  # WR production tied to pass defense
            "receptions": "passing",
            "receiving_tds": "passing"
        }

        return market_map.get(market)

    def _map_market_to_offense(self, market: str) -> Optional[str]:
        """Map prop market to offensive category.

        Args:
            market: Prop market (e.g., "passing_yards", "rushing_yards")

        Returns:
            Offense category or None
        """
        market_map = {
            "passing_yards": "passing",
            "pass_completions": "passing",
            "pass_attempts": "passing",
            "passing_tds": "passing",
            "rushing_yards": "rushing",
            "rush_attempts": "rushing",
            "rushing_tds": "rushing",
            "receiving_yards": "passing",  # WR production tied to team passing offense
            "receptions": "passing",
            "receiving_tds": "passing"
        }

        return market_map.get(market)

    def _generate_reasoning(
        self,
        bet: Dict[str, Any],
        stats: Dict[str, Any],
        true_prob: float,
        adjusted_prob: float
    ) -> str:
        """Generate human-readable reasoning for the EV calculation.

        Args:
            bet: Bet info
            stats: Stats used in calculation
            true_prob: Calculated true probability
            adjusted_prob: Conservative adjusted probability

        Returns:
            Reasoning string
        """
        bet_type = bet.get("bet_type")
        description = bet.get("description", "")

        if bet_type == "player_prop":
            player = bet.get("player", "")
            market = bet.get("market", "")
            line = bet.get("line", 0)

            player_avg = stats.get("player_averages", {})

            # Get relevant average with correct key mapping
            if market == "passing_yards":
                avg_val = player_avg.get("pass_yds_per_g", 0)
                unit = "pass yards"
            elif market == "rushing_yards":
                avg_val = player_avg.get("rush_yds_per_g", 0)
                unit = "rush yards"
            elif market == "receiving_yards":
                avg_val = player_avg.get("rec_yds_per_g", 0)
                unit = "rec yards"
            elif "reception" in market:
                avg_val = player_avg.get("rec_per_g", 0)
                unit = "receptions"
            elif market == "anytime_td":
                # Sum all TD types
                rush_td = player_avg.get("rush_td_per_g", 0)
                rec_td = player_avg.get("rec_td_per_g", 0)
                pass_td = player_avg.get("pass_td_per_g", 0)
                avg_val = rush_td + rec_td + pass_td
                unit = "TDs"
            else:
                avg_val = 0
                unit = "units"

            # Add context info
            def_rank = stats.get("opponent_def_rank", 16)

            context = f" vs ##{def_rank} defense"

            if avg_val > 0:
                return f"{player} averages {avg_val:.1f} {unit}/game{context}. Line: {line}"
            else:
                return f"{player} has no stats in {market}"

        elif bet_type in ["moneyline", "spread", "total"]:
            team_stats = stats.get("team_stats", {})
            opp_stats = stats.get("opponent_stats", {})

            # Calculate expected scores (same logic as probability calculator)
            team_ppg = team_stats.get("points_per_g", 20.0)
            opp_ppg = opp_stats.get("points_per_g", 20.0)
            team_def_ppg = team_stats.get("points_allowed_per_g", 22.0)
            opp_def_ppg = opp_stats.get("points_allowed_per_g", 22.0)

            team_expected = (team_ppg + opp_def_ppg) / 2
            opp_expected = (opp_ppg + team_def_ppg) / 2

            return f"{description}. Expected: {team_expected:.1f} pts vs {opp_expected:.1f} pts " \
                   f"(Off: {team_ppg:.1f}/{opp_ppg:.1f}, Def: {team_def_ppg:.1f}/{opp_def_ppg:.1f} allowed). " \
                   f"True prob: {true_prob:.1f}%, Adjusted: {adjusted_prob:.1f}%"

        return f"{description}. True prob: {true_prob:.1f}%, Adjusted: {adjusted_prob:.1f}%"
