"""Parse all betting opportunities from odds JSON files."""

from typing import List, Dict, Any, Optional


class BetParser:
    """Extracts and structures all bets from odds data."""

    @staticmethod
    def parse_all_bets(odds_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse all bets from odds file (game lines + player props).

        Args:
            odds_data: Complete odds JSON data

        Returns:
            List of all bets with standardized structure
        """
        all_bets = []

        # Parse game lines (moneyline, spread, total)
        all_bets.extend(BetParser.parse_game_lines(odds_data))

        # Parse all player props
        all_bets.extend(BetParser.parse_player_props(odds_data))

        return all_bets

    @staticmethod
    def parse_game_lines(odds_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse game lines (moneyline, spread, totals).

        Returns:
            List of game line bets (typically 6 bets: 2 moneylines, 2 spreads, 2 totals)
        """
        bets = []
        game_lines = odds_data.get("game_lines", {})
        teams = odds_data.get("teams", {})

        away_team = teams.get("away", {}).get("name", "Away")
        home_team = teams.get("home", {}).get("name", "Home")
        away_abbr = teams.get("away", {}).get("abbr", "AWAY")
        home_abbr = teams.get("home", {}).get("abbr", "HOME")

        # Moneyline
        if "moneyline" in game_lines:
            ml = game_lines["moneyline"]
            if "away" in ml and BetParser.is_valid_odds_range(ml["away"]):
                bets.append({
                    "bet_type": "moneyline",
                    "team": away_team,
                    "team_abbr": away_abbr,
                    "side": "away",
                    "description": f"{away_team} Moneyline",
                    "odds": ml["away"],
                    "decimal_odds": BetParser.american_to_decimal(ml["away"]),
                    "implied_prob": BetParser.calculate_implied_probability(ml["away"])
                })
            if "home" in ml and BetParser.is_valid_odds_range(ml["home"]):
                bets.append({
                    "bet_type": "moneyline",
                    "team": home_team,
                    "team_abbr": home_abbr,
                    "side": "home",
                    "description": f"{home_team} Moneyline",
                    "odds": ml["home"],
                    "decimal_odds": BetParser.american_to_decimal(ml["home"]),
                    "implied_prob": BetParser.calculate_implied_probability(ml["home"])
                })

        # Spread
        if "spread" in game_lines:
            spread = game_lines["spread"]
            if "away" in spread and "away_odds" in spread and BetParser.is_valid_odds_range(spread["away_odds"]):
                bets.append({
                    "bet_type": "spread",
                    "team": away_team,
                    "team_abbr": away_abbr,
                    "side": "away",
                    "line": spread["away"],
                    "description": f"{away_team} {spread['away']:+.1f}",
                    "odds": spread["away_odds"],
                    "decimal_odds": BetParser.american_to_decimal(spread["away_odds"]),
                    "implied_prob": BetParser.calculate_implied_probability(spread["away_odds"])
                })
            if "home" in spread and "home_odds" in spread and BetParser.is_valid_odds_range(spread["home_odds"]):
                bets.append({
                    "bet_type": "spread",
                    "team": home_team,
                    "team_abbr": home_abbr,
                    "side": "home",
                    "line": spread["home"],
                    "description": f"{home_team} {spread['home']:+.1f}",
                    "odds": spread["home_odds"],
                    "decimal_odds": BetParser.american_to_decimal(spread["home_odds"]),
                    "implied_prob": BetParser.calculate_implied_probability(spread["home_odds"])
                })

        # Totals
        if "total" in game_lines:
            total = game_lines["total"]
            if "line" in total and "over" in total and BetParser.is_valid_odds_range(total["over"]):
                bets.append({
                    "bet_type": "total",
                    "side": "over",
                    "line": total["line"],
                    "description": f"Over {total['line']} Total Points",
                    "odds": total["over"],
                    "decimal_odds": BetParser.american_to_decimal(total["over"]),
                    "implied_prob": BetParser.calculate_implied_probability(total["over"])
                })
            if "line" in total and "under" in total and BetParser.is_valid_odds_range(total["under"]):
                bets.append({
                    "bet_type": "total",
                    "side": "under",
                    "line": total["line"],
                    "description": f"Under {total['line']} Total Points",
                    "odds": total["under"],
                    "decimal_odds": BetParser.american_to_decimal(total["under"]),
                    "implied_prob": BetParser.calculate_implied_probability(total["under"])
                })

        return bets

    @staticmethod
    def parse_player_props(odds_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse all player prop bets.

        Returns:
            List of all player prop bets (500-1000 bets per game)
        """
        bets = []
        player_props = odds_data.get("player_props", [])

        for player_data in player_props:
            player = player_data.get("player", "Unknown Player")
            team = player_data.get("team", "").upper()
            position = player_data.get("position")

            props = player_data.get("props", [])
            for prop in props:
                market = prop.get("market", "")

                # Handle milestone-based markets (yards, receptions, etc.)
                if "milestones" in prop:
                    milestones = prop.get("milestones", [])
                    for milestone in milestones:
                        line = milestone.get("line")
                        odds = milestone.get("odds")

                        if line is not None and odds is not None and BetParser.is_valid_odds_range(odds):
                            bets.append({
                                "bet_type": "player_prop",
                                "market": market,
                                "player": player,
                                "team": team,
                                "position": position,
                                "line": line,
                                "side": "over",
                                "description": f"{player} Over {line} {market.replace('_', ' ').title()}",
                                "odds": odds,
                                "decimal_odds": BetParser.american_to_decimal(odds),
                                "implied_prob": BetParser.calculate_implied_probability(odds)
                            })

                # Handle single-odds markets (anytime_td, etc.)
                elif "odds" in prop:
                    odds = prop.get("odds")
                    if odds is not None and BetParser.is_valid_odds_range(odds):
                        bets.append({
                            "bet_type": "player_prop",
                            "market": market,
                            "player": player,
                            "team": team,
                            "position": position,
                            "description": f"{player} {market.replace('_', ' ').title()}",
                            "odds": odds,
                            "decimal_odds": BetParser.american_to_decimal(odds),
                            "implied_prob": BetParser.calculate_implied_probability(odds)
                        })

        return bets

    @staticmethod
    def is_valid_odds_range(odds: int, min_odds: int = -150, max_odds: int = 400) -> bool:
        """Check if odds are within acceptable range.

        Args:
            odds: American odds (e.g., +150, -110)
            min_odds: Minimum acceptable odds (default -150)
            max_odds: Maximum acceptable odds (default +400)

        Returns:
            True if odds are in range, False otherwise
        """
        return min_odds <= odds <= max_odds

    @staticmethod
    def american_to_decimal(odds: int) -> float:
        """Convert American odds to decimal odds.

        Args:
            odds: American odds (e.g., +150, -110)

        Returns:
            Decimal odds (e.g., 2.50, 1.91)
        """
        if odds > 0:
            return (odds / 100) + 1
        else:
            return (100 / abs(odds)) + 1

    @staticmethod
    def calculate_implied_probability(odds: int) -> float:
        """Calculate implied probability from American odds.

        Args:
            odds: American odds (e.g., +150, -110)

        Returns:
            Implied probability as percentage (e.g., 40.0, 52.4)
        """
        if odds > 0:
            return (100 / (odds + 100)) * 100
        else:
            return (abs(odds) / (abs(odds) + 100)) * 100

    @staticmethod
    def filter_bets_by_type(bets: List[Dict[str, Any]], bet_type: str) -> List[Dict[str, Any]]:
        """Filter bets by type.

        Args:
            bets: List of all bets
            bet_type: Type to filter (e.g., "player_prop", "moneyline", "spread")

        Returns:
            Filtered list of bets
        """
        return [bet for bet in bets if bet.get("bet_type") == bet_type]

    @staticmethod
    def filter_bets_by_market(bets: List[Dict[str, Any]], market: str) -> List[Dict[str, Any]]:
        """Filter player props by market.

        Args:
            bets: List of all bets
            market: Market to filter (e.g., "receiving_yards", "passing_yards")

        Returns:
            Filtered list of bets
        """
        return [bet for bet in bets if bet.get("market") == market]
