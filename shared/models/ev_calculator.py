"""Main EV calculator - orchestrates bet parsing, stat aggregation, and probability calculation."""

from typing import List, Dict, Any, Optional
from pathlib import Path
from shared.models.bet_parser import BetParser
from shared.models.stat_aggregator import StatAggregator
from shared.models.probability_calculator import ProbabilityCalculator
from shared.models.bet_validator import BetValidator
from shared.utils.player_filter import PlayerFilter
from shared.utils.player_game_log import PlayerGameLog
from nfl.teams import PFR_ABBR_TO_NAME

# Minimum games required for recent form calculation
MIN_GAMES_REQUIRED = 3


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

        self.calibrator = None

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

        # Initialize player filter (filters to top players by position)
        # Pass stat_aggregator for name normalization (handles nicknames, suffixes, etc.)
        self.player_filter = PlayerFilter(self.home_profile, self.away_profile, self.stat_aggregator)

        # Initialize player game log utility for recent form (last 5 games)
        self.player_game_log = PlayerGameLog(sport_config.sport_name, base_dir)

        # Validate that data loaded successfully
        if not self.away_profile or not self.home_profile:
            print(f"⚠️  Warning: Profiles missing for {self.away_team} or {self.home_team}")
            print(f"    Away profile loaded: {bool(self.away_profile)}")
            print(f"    Home profile loaded: {bool(self.home_profile)}")

        # Check if stat aggregator has rankings data (test with scoring average)
        test_stat_away = self.stat_aggregator.get_team_scoring_average(self.away_team)
        test_stat_home = self.stat_aggregator.get_team_scoring_average(self.home_team)
        if test_stat_away == 20.0 and test_stat_home == 20.0:
            # Both teams using default value - rankings likely not loaded
            print(f"⚠️  Warning: Both teams using default stats (20.0 PPG)")
            print(f"    This suggests rankings may not be loaded properly")
            print(f"    Check that rankings directory exists and has data")

            # Fail fast with clear error instead of silently continuing with bad data
            raise ValueError(
                f"Rankings data not available for {self.away_team} and {self.home_team}. "
                f"Please ensure rankings have been scraped."
            )

    def calculate_all_ev(self, min_ev_threshold: float = 0.0) -> List[Dict[str, Any]]:
        """Calculate EV for all bets in odds file.

        Args:
            min_ev_threshold: Minimum EV percentage to include (default 0.0 = all bets)

        Returns:
            List of all bets with EV calculated, filtered by threshold
        """
        # Parse all bets
        all_bets = self.bet_parser.parse_all_bets(self.odds_data)
        print(f"[DEBUG] Parsed {len(all_bets)} bets from odds")

        # Filter player props to only include top players by position
        filtered_bets = []
        for bet in all_bets:
            bet_type = bet.get("bet_type")

            # Always include game-level bets (moneyline, spread, total)
            if bet_type in ["moneyline", "spread", "total"]:
                filtered_bets.append(bet)

            # Filter player props to only top performers
            elif bet_type == "player_prop":
                player = bet.get("player", "")
                team = bet.get("team", "")
                if self.player_filter.is_player_eligible(player, team):
                    filtered_bets.append(bet)

        print(f"[DEBUG] Filtered to {len(filtered_bets)} bets (removed {len(all_bets) - len(filtered_bets)} bets from bench/backup players)")
        all_bets = filtered_bets

        # Calculate EV for each bet
        bets_with_ev = []
        for bet in all_bets:
            try:
                ev_result = self._calculate_bet_ev(bet)
                if ev_result and ev_result["ev_percent"] >= min_ev_threshold:
                    bets_with_ev.append(ev_result)
            except Exception as e:
                # Skip bets that error out (missing data, etc.)
                bet_desc = bet.get('description', 'unknown bet')
                bet_type = bet.get('bet_type', 'unknown')
                player = bet.get('player', 'N/A')

                print(f"❌ Error calculating EV for {bet_desc}")
                print(f"    Type: {bet_type}, Player: {player}")
                print(f"    Error: {e}")

                # Only show full stack trace in debug mode (set DEBUG=1 env var)
                import os
                if os.getenv('DEBUG'):
                    import traceback
                    traceback.print_exc()
                continue

        print(f"[DEBUG] {len(bets_with_ev)} bets passed validation and met EV threshold")

        # Sort by EV (highest first)
        bets_with_ev.sort(key=lambda x: x["ev_percent"], reverse=True)

        return bets_with_ev

    def get_top_n(self, n: int = 10, min_ev_threshold: float = 0.0, deduplicate_players: bool = True, max_receivers_per_team: int = 1) -> List[Dict[str, Any]]:
        """Get top N bets by EV.

        Args:
            n: Number of top bets to return
            min_ev_threshold: Minimum EV percentage (default 0.0% - any positive EV)
            deduplicate_players: If True, show only best bet per player (default True)
            max_receivers_per_team: Maximum receivers (WR/TE) per team to avoid correlation (default 1)

        Returns:
            Top N bets ranked by EV
        """
        all_bets = self.calculate_all_ev(min_ev_threshold)

        if deduplicate_players:
            seen_players = set()
            team_receiver_count = {}  # Track receiver count per team
            deduped_bets = []

            for bet in all_bets:  # Already sorted by EV descending
                bet_type = bet.get("bet_type")
                if bet_type == "player_prop":
                    player = bet.get("player", "")
                    team = bet.get("team", "")
                    position = bet.get("position", "")
                    market = bet.get("market", "")

                    # Check if this is a receiver (WR/TE or receiving market)
                    is_receiver = (
                        position in ["WR", "TE"] or
                        market in ["receiving_yards", "receptions"]
                    )

                    # Skip if player already seen
                    if player and player in seen_players:
                        continue

                    # Skip if this is a receiver and team already has max receivers
                    if is_receiver and team:
                        team_receivers = team_receiver_count.get(team, 0)
                        if team_receivers >= max_receivers_per_team:
                            continue

                    # Add the bet
                    if player:
                        seen_players.add(player)
                    if is_receiver and team:
                        team_receiver_count[team] = team_receiver_count.get(team, 0) + 1
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
            # Log validation failure for debugging
            bet_desc = bet.get("description", "unknown bet")
            print(f"⚠️  Validation failed: {reason} ({bet_desc})")
            return None

        # Calculate true probability
        true_prob = self.prob_calculator.calculate_probability(bet, stats)

        # Calculate preliminary EV for calibration
        decimal_odds = bet.get("decimal_odds", 1.0)
        preliminary_ev = ((true_prob / 100) * decimal_odds - 1) * 100

        # Apply Bayesian calibration if available
        if self.calibrator:
            bet_type = bet.get("bet_type", "unknown")
            calibrated_prob = self.calibrator.calibrate_probability(
                raw_probability=true_prob,
                predicted_ev=preliminary_ev,
                bet_type=bet_type
            )
        else:
            calibrated_prob = true_prob

        # Apply conservative adjustment (reduce by 10-15%)
        adjusted_prob = self.stat_aggregator.apply_conservative_adjustment(
            calibrated_prob,
            self.conservative_adjustment
        )

        # Convert probability to decimal (0-1 range)
        prob_decimal = adjusted_prob / 100

        # Calculate final EV (decimal_odds already retrieved above)
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
            team_side = (bet.get("team") or "").upper()
            market = bet.get("market", "")

            # Determine which team the player is on
            # Get BOTH abbr (e.g., "HOU") AND pfr_abbr (e.g., "htx") for each team
            away_teams = self.odds_data.get("teams", {}).get("away", {})
            home_teams = self.odds_data.get("teams", {}).get("home", {})

            away_abbr = (away_teams.get("abbr") or "").upper()
            away_pfr_abbr = (away_teams.get("pfr_abbr") or "").upper()
            home_abbr = (home_teams.get("abbr") or "").upper()
            home_pfr_abbr = (home_teams.get("pfr_abbr") or "").upper()

            # Handle "AWAY"/"HOME" strings, abbr field (e.g., "HOU"), AND pfr_abbr field (e.g., "HTX")
            if team_side == "AWAY" or team_side == away_abbr or team_side == away_pfr_abbr:
                player_profile = self.away_profile
                player_team = self.away_team
                opponent_team = self.home_team
                # Get spread from away team perspective (positive = underdog, negative = favorite)
                spread_line = self.odds_data.get("game_lines", {}).get("spread", {}).get("away", 0)
            elif team_side == "HOME" or team_side == home_abbr or team_side == home_pfr_abbr:
                player_profile = self.home_profile
                player_team = self.home_team
                opponent_team = self.away_team
                # Get spread from home team perspective
                spread_line = self.odds_data.get("game_lines", {}).get("spread", {}).get("home", 0)
            else:
                # Unknown team - log warning and skip
                print(f"⚠️  Unknown team '{team_side}' for {player_name} (expected AWAY/HOME, {away_abbr}/{home_abbr}, or {away_pfr_abbr}/{home_pfr_abbr})")
                return stats

            # Load player stats from season profile (needed for position, validation)
            player_stats = self.stat_aggregator.load_player_stats(player_name, player_profile)

            if player_stats:
                # Get team abbreviation for game log lookup
                if team_side == "AWAY" or team_side == away_abbr or team_side == away_pfr_abbr:
                    player_team_abbr = away_abbr  # Use DraftKings abbr (e.g., "DET")
                else:
                    player_team_abbr = home_abbr

                # Try to get recent game stats (last 5 games) from boxscore data
                recent_games = self.player_game_log.get_player_recent_games(
                    player_name,
                    player_team_abbr,
                    num_games=5
                )

                if len(recent_games) >= MIN_GAMES_REQUIRED:
                    # Use ONLY recent form (last 5 games) for player props
                    stats["player_averages"] = self.player_game_log.calculate_recent_averages(recent_games)
                    stats["recent_games_count"] = len(recent_games)
                    stats["using_recent_form"] = True
                else:
                    # Insufficient sample size - skip this bet
                    print(f"⚠️  Skipping {player_name}: only {len(recent_games)} games found (need {MIN_GAMES_REQUIRED}+)")
                    return stats  # Return without player_averages to trigger validation failure

                stats["position"] = player_stats.get("position", "")
                stats["player_stats"] = player_stats  # Store for validator
                stats["spread_line"] = spread_line  # Game script context

                # Infer player role for adaptive variance calculation
                stats["player_role"] = self._infer_player_role(
                    stats["position"],
                    stats["player_averages"],
                    player_profile
                )

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

    def _infer_player_role(
        self,
        position: str,
        player_averages: Dict[str, Any],
        player_profile: Dict[str, Any]
    ) -> str:
        """Infer player role (WR1, RB2, etc.) based on usage stats.

        Args:
            position: Player position (QB, RB, WR, TE)
            player_averages: Player's season averages
            player_profile: Team profile for comparison

        Returns:
            Player role string (e.g., "QB1", "WR1", "RB2", "TE1")
        """
        # QBs are typically QB1 (starter)
        if position == "QB":
            return "QB1"

        # TEs - check if they're the primary receiving option
        if position == "TE":
            rec_per_g = player_averages.get("rec_per_g", 0)
            return "TE1" if rec_per_g >= 3.0 else "TE2"

        # RBs - infer role based on rush attempts
        if position == "RB":
            rush_att_per_g = player_averages.get("rush_att_per_g", 0)
            if rush_att_per_g >= 12.0:
                return "RB1"  # Bell cow / primary back
            elif rush_att_per_g >= 6.0:
                return "RB2"  # Timeshare / change of pace
            else:
                return "RB3"  # Situational / backup

        # WRs - infer role based on targets/receptions
        if position == "WR":
            rec_per_g = player_averages.get("rec_per_g", 0)
            targets_per_g = player_averages.get("targets_per_g", 0) if "targets_per_g" in player_averages else rec_per_g * 1.5

            if targets_per_g >= 7.0 or rec_per_g >= 5.0:
                return "WR1"  # Primary receiver
            elif targets_per_g >= 4.5 or rec_per_g >= 3.0:
                return "WR2"  # Secondary receiver
            else:
                return "WR3"  # Depth receiver / situational

        # Default fallback
        return f"{position}1"

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
            recent_games = stats.get("recent_games_count", 0)

            context = f" vs #{def_rank} defense"
            form_info = f" (last {recent_games} games)" if recent_games > 0 else " (season avg)"

            if avg_val > 0:
                return f"{player} averages {avg_val:.1f} {unit}/game{form_info}{context}. Line: {line}"
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
