"""NFL odds scraper for DraftKings HTML files."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from shared.utils.timezone_utils import get_eastern_now


class NFLOddsScraper:
    """Extract betting odds from DraftKings HTML files.

    Focuses on essential betting markets:
    - Game lines (moneyline, spread, total)
    - Player props (passing, rushing, receiving)
    - Touchdown scorers

    Excludes: quarters, halves, 1st drive props, exotic bets.
    """

    # Market types to include (based on prompt analysis)
    INCLUDED_MARKET_TYPES = {
        # Game lines
        "Moneyline",
        "Spread",
        "Total",
        # Player props
        "Passing Yards Milestones",
        "Passing Touchdowns Milestones",
        "Pass Completions Milestones",
        "Pass Attempts Milestones",
        "Rushing Yards Milestones",
        "Rushing Attempts Milestones",
        "Receiving Yards Milestones",
        "Receptions Milestones",
        "Rushing + Receiving Yards Milestones",
        # TD scorers
        "Anytime Touchdown Scorer",
        # Defensive props
        "Sacks Milestones",
        "Tackles + Assists Milestones",
        "Interceptions Milestones",
    }

    # Market types to explicitly exclude
    EXCLUDED_MARKET_TYPES = {
        "1st Quarter Moneyline",
        "1st Quarter Spread",
        "1st Quarter Total",
        "1st Half Moneyline",
        "1st Half Spread",
        "1st Half Total",
        "1st Drive Result",
        "DK Squares",
    }

    def extract_odds(self, html_path: str) -> dict[str, Any]:
        """Extract odds from DraftKings HTML file.

        Args:
            html_path: Path to the HTML file

        Returns:
            Dictionary with game info and odds:
            {
                "sport": "nfl",
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
        stadium_data = self._extract_stadium_data(html_content)

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
            "sport": "nfl",
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

    def _extract_stadium_data(self, html_content: str) -> dict[str, Any]:
        """Extract window.__INITIAL_STATE__.stadiumEventData from HTML.

        Args:
            html_content: Raw HTML content

        Returns:
            Parsed stadiumEventData dictionary

        Raises:
            ValueError: If JavaScript data not found or invalid
        """
        # Find the JavaScript object
        pattern = r'window\.__INITIAL_STATE__\s*=\s*({.*?});'
        match = re.search(pattern, html_content, re.DOTALL)

        if not match:
            raise ValueError("Could not find window.__INITIAL_STATE__ in HTML")

        try:
            initial_state = json.loads(match.group(1))
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JavaScript JSON: {e}")

        if "stadiumEventData" not in initial_state:
            raise ValueError("stadiumEventData not found in __INITIAL_STATE__")

        return initial_state["stadiumEventData"]

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
                game_lines["moneyline"] = self._parse_moneyline(market, selections)
            elif market_type == "Spread":
                game_lines["spread"] = self._parse_spread(market, selections)
            elif market_type == "Total":
                game_lines["total"] = self._parse_total(market, selections)

        return game_lines

    def _parse_moneyline(self, market: dict, all_selections: list[dict]) -> dict:
        """Parse moneyline market into simple away/home format.

        Args:
            market: Market dictionary
            all_selections: All selections

        Returns:
            Dictionary with away and home odds
        """
        market_id = market["id"]
        market_selections = [s for s in all_selections if s.get("marketId") == market_id]

        result = {"away": None, "home": None}

        for selection in market_selections:
            # Get participant info to determine if away or home
            participants = selection.get("participants", [])
            if not participants:
                continue

            venue_role = participants[0].get("venueRole")
            odds = self._clean_odds(selection.get("displayOdds", {}).get("american"))

            if venue_role == "Away":
                result["away"] = odds
            elif venue_role == "Home":
                result["home"] = odds

        return result

    def _parse_spread(self, market: dict, all_selections: list[dict]) -> dict:
        """Parse spread market.

        Args:
            market: Market dictionary
            all_selections: All selections

        Returns:
            Dictionary with away/home spread and odds
        """
        market_id = market["id"]
        market_selections = [s for s in all_selections if s.get("marketId") == market_id]

        result = {
            "away": None,
            "away_odds": None,
            "home": None,
            "home_odds": None
        }

        for selection in market_selections:
            participants = selection.get("participants", [])
            if not participants:
                continue

            venue_role = participants[0].get("venueRole")
            points = selection.get("points")
            odds = self._clean_odds(selection.get("displayOdds", {}).get("american"))

            if venue_role == "Away":
                result["away"] = points
                result["away_odds"] = odds
            elif venue_role == "Home":
                result["home"] = points
                result["home_odds"] = odds

        return result

    def _parse_total(self, market: dict, all_selections: list[dict]) -> dict:
        """Parse total (over/under) market.

        Args:
            market: Market dictionary
            all_selections: All selections

        Returns:
            Dictionary with line, over odds, under odds
        """
        market_id = market["id"]
        market_selections = [s for s in all_selections if s.get("marketId") == market_id]

        result = {"line": None, "over": None, "under": None}

        for selection in market_selections:
            label = selection.get("label", "").lower()
            points = selection.get("points")
            odds = self._clean_odds(selection.get("displayOdds", {}).get("american"))

            # Set line from either over or under
            if points is not None and result["line"] is None:
                result["line"] = abs(points)

            if label == "over":
                result["over"] = odds
            elif label == "under":
                result["under"] = odds

        return result

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
            if "Milestones" in market_type or "Touchdown Scorer" in market_type:
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

        # Handle Anytime TD differently (multiple players in one market)
        if market_type == "Anytime Touchdown Scorer":
            for selection in market_selections:
                participants = selection.get("participants", [])
                if not participants or participants[0].get("type") != "Player":
                    continue

                player_name = participants[0].get("name")
                player_id = participants[0].get("id")
                venue_role = participants[0].get("venueRole", "")

                # Determine team from venue role
                team = self._parse_team_from_venue_role(venue_role)

                # Create or get player entry
                key = f"{player_name}_{team}"
                if key not in player_markets:
                    player_markets[key] = {
                        "player": player_name,
                        "team": team,
                        "position": None,  # Not available in DK data
                        "props": []
                    }

                # Add TD prop
                odds = self._clean_odds(selection.get("displayOdds", {}).get("american"))
                player_markets[key]["props"].append({
                    "market": "anytime_td",
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

        DraftKings uses milestone format (150+, 170+, etc.) instead of traditional
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
            "Passing Yards Milestones": "passing_yards",
            "Passing Touchdowns Milestones": "passing_tds",
            "Pass Completions Milestones": "pass_completions",
            "Pass Attempts Milestones": "pass_attempts",
            "Rushing Yards Milestones": "rushing_yards",
            "Rushing Attempts Milestones": "rush_attempts",
            "Receiving Yards Milestones": "receiving_yards",
            "Receptions Milestones": "receptions",
            "Rushing and Receiving Yards Milestones": "rush_rec_yards",  # Note: "and" not "+"
            "Sacks Milestones": "sacks",
            "Tackles + Assists Milestones": "tackles_assists",
            "Interceptions Milestones": "interceptions",
        }

        prop_name = market_map.get(market_type)
        if not prop_name:
            return None

        # Extract all milestones
        milestones = []

        for selection in selections:
            milestone_value = selection.get("milestoneValue")
            odds = self._clean_odds(selection.get("displayOdds", {}).get("american"))

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
            market_name: Market name (e.g., "Lamar Jackson Passing Yards")
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
        team = self._parse_team_from_venue_role(venue_role)

        return {"name": player_name, "team": team}

    def _parse_team_from_venue_role(self, venue_role: str) -> str | None:
        """Extract team abbr from venue role.

        Args:
            venue_role: e.g., "HomePlayer" or "AwayPlayer"

        Returns:
            Team abbreviation or None
        """
        # venue_role will be like "HomePlayer" or "AwayPlayer"
        # We'll need to map this back to the actual team
        # For now, just return the role and we'll fix it in post-processing
        if "Home" in venue_role:
            return "HOME"
        elif "Away" in venue_role:
            return "AWAY"
        return None

    def _clean_odds(self, odds_str: str | None) -> int | None:
        """Clean odds string to integer.

        DraftKings uses Unicode minus sign (\\u2212) instead of ASCII hyphen.

        Args:
            odds_str: Odds string (e.g., "−110", "+340")

        Returns:
            Integer odds or None if invalid
        """
        if not odds_str:
            return None

        # Replace Unicode minus with ASCII minus
        odds_str = odds_str.replace('\u2212', '-')

        try:
            return int(odds_str)
        except (ValueError, TypeError):
            return None
