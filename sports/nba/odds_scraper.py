"""NBA odds scraper for DraftKings HTML files."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from shared.utils.timezone_utils import get_eastern_now
from shared.scrapers import dk_json_parser


class NBAOddsScraper:
    """Extract betting odds from DraftKings HTML files.

    Focuses on essential betting markets:
    - Game lines (moneyline, spread, total)
    - Player props (points, rebounds, assists, 3PM)
    - Special props (double-double, triple-double)

    Excludes: quarters, halves, exotic bets.
    """

    # Market types to include (based on NBA betting)
    INCLUDED_MARKET_TYPES = {
        # Game lines
        "Moneyline",
        "Spread",
        "Total",
        # Player props
        "Points Milestones",
        "Rebounds Milestones",
        "Assists Milestones",
        "3-Pointers Made Milestones",
        "Steals Milestones",
        "Blocks Milestones",
        "Points + Rebounds Milestones",
        "Points + Assists Milestones",
        "Rebounds + Assists Milestones",
        "Points + Rebounds + Assists Milestones",
        # Special props
        "Double-Double",
        "Triple-Double",
        "First Basket",
    }

    # Market types to explicitly exclude
    EXCLUDED_MARKET_TYPES = {
        "1st Quarter Moneyline",
        "1st Quarter Spread",
        "1st Quarter Total",
        "1st Half Moneyline",
        "1st Half Spread",
        "1st Half Total",
        "DK Squares",
    }

    def extract_odds(self, html_path: str) -> dict[str, Any]:
        """Extract odds from DraftKings HTML file.

        Args:
            html_path: Path to the HTML file

        Returns:
            Dictionary with game info and odds:
            {
                "sport": "nba",
                "teams": {"away": {...}, "home": {...}},
                "game_date": str,
                "fetched_at": str,
                "source": "draftkings",
                "game_lines": {...},
                "player_props": [...]
            }

        Raises:
            FileNotFoundError: If HTML file doesn't exist
            ValueError: If data extraction fails
        """
        print(f"\nExtracting odds from {html_path}...")

        # Read HTML file
        html_path_obj = Path(html_path)
        if not html_path_obj.exists():
            raise FileNotFoundError(f"HTML file not found: {html_path}")

        html_content = html_path_obj.read_text(encoding='utf-8')

        # Extract JavaScript data
        print("  Parsing JavaScript data...")
        stadium_data = dk_json_parser.extract_stadium_data(html_content)

        # Parse the three main arrays
        events = stadium_data.get("events", [])
        markets = stadium_data.get("markets", [])
        selections = stadium_data.get("selections", [])

        if not events:
            raise ValueError("No event data found in HTML")

        event = events[0]  # Should be only one event

        print(f"  Found {len(markets)} markets, {len(selections)} selections")

        # Build the result structure
        result = {
            "sport": "nba",
            "teams": self._extract_teams(event),
            "game_date": event.get("startEventDate"),
            "fetched_at": get_eastern_now().isoformat(),
            "source": "draftkings",
            "game_lines": {},
            "player_props": []
        }

        # Filter and organize markets
        print("  Organizing markets...")
        result["game_lines"] = self._extract_game_lines(event["id"], markets, selections)
        result["player_props"] = self._extract_player_props(event["id"], markets, selections)

        print(f"\n  ✅ Extracted {len(result['game_lines'])} game lines")
        print(f"  ✅ Extracted {len(result['player_props'])} player prop markets")

        return result

    def _extract_teams(self, event: dict) -> dict[str, dict]:
        """Extract team information from event data.

        Args:
            event: Event dictionary

        Returns:
            Dictionary with away and home team info
        """
        teams = {"away": None, "home": None}

        for participant in event.get("participants", []):
            if participant.get("type") != "Team":
                continue

            team_info = {
                "name": participant.get("name"),
                "abbr": participant.get("metadata", {}).get("shortName")
            }

            venue_role = participant.get("venueRole")
            if venue_role == "Away":
                teams["away"] = team_info
            elif venue_role == "Home":
                teams["home"] = team_info

        return teams

    def _extract_game_lines(
        self,
        event_id: str,
        markets: list[dict],
        selections: list[dict]
    ) -> dict[str, Any]:
        """Extract moneyline, spread, and total game lines.

        Args:
            event_id: Event ID to filter by
            markets: All markets
            selections: All selections

        Returns:
            Dictionary with game lines
        """
        game_lines = {}

        # Find the main game line markets
        for market in markets:
            if market.get("eventId") != event_id:
                continue

            market_type = market.get("marketType", {}).get("name")

            if market_type == "Moneyline":
                game_lines["moneyline"] = dk_json_parser.parse_moneyline(market, selections)
            elif market_type == "Spread":
                game_lines["spread"] = dk_json_parser.parse_spread(market, selections)
            elif market_type == "Total":
                game_lines["total"] = dk_json_parser.parse_total(market, selections)

        return game_lines

    def _extract_player_props(
        self,
        event_id: str,
        markets: list[dict],
        selections: list[dict]
    ) -> list[dict]:
        """Extract player prop markets.

        Args:
            event_id: Event ID to filter by
            markets: All markets
            selections: All selections

        Returns:
            List of player prop dictionaries
        """
        # Group markets by player
        player_markets = {}

        for market in markets:
            if market.get("eventId") != event_id:
                continue

            market_type = market.get("marketType", {}).get("name")

            # Skip excluded markets
            if market_type in self.EXCLUDED_MARKET_TYPES:
                continue

            # Skip if not in included types (except game lines which we handled separately)
            if market_type not in self.INCLUDED_MARKET_TYPES:
                continue

            # Parse player props
            if "Milestones" in market_type or market_type in ["Double-Double", "Triple-Double", "First Basket"]:
                self._add_player_prop(market, market_type, selections, player_markets)

        # Convert to list format
        return list(player_markets.values())

    def _add_player_prop(
        self,
        market: dict,
        market_type: str,
        all_selections: list[dict],
        player_markets: dict
    ):
        """Add a player prop market to the player_markets dictionary.

        Args:
            market: Market dictionary
            market_type: Type of market
            all_selections: All selections
            player_markets: Dictionary to accumulate player props
        """
        market_id = market["id"]
        market_name = market.get("name", "")
        market_selections = [s for s in all_selections if s.get("marketId") == market_id]

        if not market_selections:
            return

        # Handle special prop types (multiple players in one market)
        if market_type in ["Double-Double", "Triple-Double", "First Basket"]:
            for selection in market_selections:
                participants = selection.get("participants", [])
                if not participants or participants[0].get("type") != "Player":
                    continue

                player_name = participants[0].get("name")
                player_id = participants[0].get("id")
                venue_role = participants[0].get("venueRole", "")

                # Determine team from venue role
                team = dk_json_parser.parse_team_from_venue_role(venue_role)

                # Create or get player entry
                key = f"{player_name}_{team}"
                if key not in player_markets:
                    player_markets[key] = {
                        "player": player_name,
                        "team": team,
                        "position": None,  # Not available in DK data
                        "props": []
                    }

                # Add prop
                odds = dk_json_parser.clean_odds(selection.get("displayOdds", {}).get("american"))
                prop_market_name = market_type.lower().replace("-", "_").replace(" ", "_")
                player_markets[key]["props"].append({
                    "market": prop_market_name,
                    "odds": odds
                })
        else:
            # Extract player name from market name
            player_info = self._extract_player_from_market_name(market_name, market_selections)
            if not player_info:
                return

            player_name = player_info["name"]
            team = player_info["team"]

            # Create or get player entry
            key = f"{player_name}_{team}"
            if key not in player_markets:
                player_markets[key] = {
                    "player": player_name,
                    "team": team,
                    "position": None,
                    "props": []
                }

            # Parse the prop based on market type
            prop = self._parse_milestone_prop(market_type, market_selections)
            if prop:
                player_markets[key]["props"].append(prop)

    def _parse_milestone_prop(self, market_type: str, selections: list[dict]) -> dict | None:
        """Parse a milestone prop (DraftKings milestone format).

        DraftKings uses milestone format (25+, 30+, etc.) instead of traditional
        Over/Under. We extract ALL milestones to provide complete odds distribution
        for EV+ analysis and better prediction accuracy.

        Args:
            market_type: Type of market
            selections: Selections for this market

        Returns:
            Prop dictionary with all milestones or None if invalid
        """
        # Map market types to prop names
        market_map = {
            "Points Milestones": "points",
            "Rebounds Milestones": "rebounds",
            "Assists Milestones": "assists",
            "3-Pointers Made Milestones": "three_pointers_made",
            "Steals Milestones": "steals",
            "Blocks Milestones": "blocks",
            "Points + Rebounds Milestones": "pts_reb",
            "Points + Assists Milestones": "pts_ast",
            "Rebounds + Assists Milestones": "reb_ast",
            "Points + Rebounds + Assists Milestones": "pts_reb_ast",
        }

        prop_name = market_map.get(market_type)
        if not prop_name:
            return None

        # Extract all milestones
        milestones = []

        for selection in selections:
            milestone_value = selection.get("milestoneValue")
            odds = dk_json_parser.clean_odds(selection.get("displayOdds", {}).get("american"))

            if milestone_value is None or odds is None:
                continue

            milestones.append({
                "line": milestone_value,
                "odds": odds
            })

        if milestones:
            # Sort by line value (ascending)
            milestones.sort(key=lambda x: x["line"])

            return {
                "market": prop_name,
                "milestones": milestones
            }

        return None

    def _extract_player_from_market_name(
        self,
        market_name: str,
        selections: list[dict]
    ) -> dict | None:
        """Extract player name and team from market name.

        Args:
            market_name: Market name (e.g., "LeBron James Points")
            selections: Selections for this market (to get team info)

        Returns:
            Dictionary with name and team, or None if not found
        """
        # Get participant info from first selection
        if not selections:
            return None

        participants = selections[0].get("participants", [])
        if not participants:
            return None

        participant = participants[0]
        if participant.get("type") != "Player":
            return None

        player_name = participant.get("name")
        venue_role = participant.get("venueRole", "")
        team = dk_json_parser.parse_team_from_venue_role(venue_role)

        return {"name": player_name, "team": team}
