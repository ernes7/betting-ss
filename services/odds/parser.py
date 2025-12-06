"""DraftKings JSON parsing utilities for odds extraction.

This module provides sport-agnostic parsing of the DraftKings
window.__INITIAL_STATE__.stadiumEventData structure.
"""

import json
import re
from typing import Any, Optional

from shared.logging import get_logger
from shared.errors import OddsParseError


logger = get_logger("odds")


class DraftKingsParser:
    """Parser for DraftKings stadium event data.

    Extracts structured odds data from DraftKings HTML pages.
    Sport-agnostic - works for NFL, NBA, and other sports.

    Example:
        parser = DraftKingsParser()
        stadium_data = parser.extract_stadium_data(html_content)
        moneyline = parser.parse_moneyline(market, selections)
    """

    @staticmethod
    def extract_stadium_data(html_content: str) -> dict[str, Any]:
        """Extract window.__INITIAL_STATE__.stadiumEventData from HTML.

        Args:
            html_content: Raw HTML content from DraftKings page

        Returns:
            Parsed stadiumEventData dictionary

        Raises:
            OddsParseError: If JavaScript data not found or invalid
        """
        pattern = r'window\.__INITIAL_STATE__\s*=\s*({.*?});'
        match = re.search(pattern, html_content, re.DOTALL)

        if not match:
            raise OddsParseError(
                "Could not find window.__INITIAL_STATE__ in HTML",
                context={"html_length": len(html_content)}
            )

        try:
            initial_state = json.loads(match.group(1))
        except json.JSONDecodeError as e:
            raise OddsParseError(
                f"Failed to parse JavaScript JSON: {e}",
                context={"error": str(e)}
            )

        if "stadiumEventData" not in initial_state:
            raise OddsParseError(
                "stadiumEventData not found in __INITIAL_STATE__",
                context={"available_keys": list(initial_state.keys())}
            )

        return initial_state["stadiumEventData"]

    @staticmethod
    def clean_odds(odds_str: str | None) -> int | None:
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

    @staticmethod
    def parse_team_from_venue_role(venue_role: str) -> str | None:
        """Parse venue role string to team designation.

        Args:
            venue_role: e.g., "HomePlayer" or "AwayPlayer"

        Returns:
            "HOME", "AWAY", or None
        """
        if "Home" in venue_role:
            return "HOME"
        elif "Away" in venue_role:
            return "AWAY"
        return None

    def parse_moneyline(
        self,
        market: dict,
        all_selections: list[dict]
    ) -> dict[str, Optional[int]]:
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
            participants = selection.get("participants", [])
            if not participants:
                continue

            venue_role = participants[0].get("venueRole")
            odds = self.clean_odds(selection.get("displayOdds", {}).get("american"))

            if venue_role == "Away":
                result["away"] = odds
            elif venue_role == "Home":
                result["home"] = odds

        return result

    def parse_spread(
        self,
        market: dict,
        all_selections: list[dict]
    ) -> dict[str, Any]:
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
            odds = self.clean_odds(selection.get("displayOdds", {}).get("american"))

            if venue_role == "Away":
                result["away"] = points
                result["away_odds"] = odds
            elif venue_role == "Home":
                result["home"] = points
                result["home_odds"] = odds

        return result

    def parse_total(
        self,
        market: dict,
        all_selections: list[dict]
    ) -> dict[str, Any]:
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
            odds = self.clean_odds(selection.get("displayOdds", {}).get("american"))

            # Set line from either over or under
            if points is not None and result["line"] is None:
                result["line"] = abs(points)

            if label == "over":
                result["over"] = odds
            elif label == "under":
                result["under"] = odds

        return result

    def parse_milestones(
        self,
        market: dict,
        all_selections: list[dict]
    ) -> list[dict]:
        """Parse milestone market selections.

        DraftKings uses milestone format (150+, 170+, etc.) instead of
        traditional Over/Under. Extracts ALL milestones for complete
        odds distribution.

        Args:
            market: Market dictionary
            all_selections: All selections

        Returns:
            List of milestone dictionaries with line and odds
        """
        market_id = market["id"]
        market_selections = [s for s in all_selections if s.get("marketId") == market_id]

        milestones = []

        for selection in market_selections:
            milestone_value = selection.get("milestoneValue")
            odds = self.clean_odds(selection.get("displayOdds", {}).get("american"))

            if milestone_value is None or odds is None:
                continue

            milestones.append({
                "line": milestone_value,
                "odds": odds
            })

        # Sort by line value (ascending)
        milestones.sort(key=lambda x: x["line"])
        return milestones

    def extract_teams(self, event: dict) -> dict[str, Optional[dict]]:
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

            name = participant.get("name", "")
            # Try shortName (NFL), fallback to slugified name (soccer)
            abbr = participant.get("metadata", {}).get("shortName")
            if not abbr and name:
                # Create slug from name: "Bayern Munchen" -> "bayern_mun"
                abbr = name.lower().replace(" ", "_")[:10]

            team_info = {
                "name": name,
                "abbr": abbr
            }

            venue_role = participant.get("venueRole")
            if venue_role == "Away":
                teams["away"] = team_info
            elif venue_role == "Home":
                teams["home"] = team_info

        return teams

    def extract_player_info(
        self,
        selections: list[dict]
    ) -> Optional[dict]:
        """Extract player name and team from selections.

        Args:
            selections: Selections for a market

        Returns:
            Dictionary with name and team, or None if not found
        """
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
        team = self.parse_team_from_venue_role(venue_role)

        return {"name": player_name, "team": team}


# Backward compatibility - expose as functions
_parser = DraftKingsParser()

def extract_stadium_data(html_content: str) -> dict[str, Any]:
    """Extract stadium data from HTML (backward compatible)."""
    return _parser.extract_stadium_data(html_content)

def clean_odds(odds_str: str | None) -> int | None:
    """Clean odds string (backward compatible)."""
    return _parser.clean_odds(odds_str)

def parse_moneyline(market: dict, all_selections: list[dict]) -> dict:
    """Parse moneyline (backward compatible)."""
    return _parser.parse_moneyline(market, all_selections)

def parse_spread(market: dict, all_selections: list[dict]) -> dict:
    """Parse spread (backward compatible)."""
    return _parser.parse_spread(market, all_selections)

def parse_total(market: dict, all_selections: list[dict]) -> dict:
    """Parse total (backward compatible)."""
    return _parser.parse_total(market, all_selections)

def parse_team_from_venue_role(venue_role: str) -> str | None:
    """Parse team from venue role (backward compatible)."""
    return _parser.parse_team_from_venue_role(venue_role)
