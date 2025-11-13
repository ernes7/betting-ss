"""Shared DraftKings JSON parsing utilities for odds extraction.

These functions are sport-agnostic and parse the common DraftKings
window.__INITIAL_STATE__.stadiumEventData structure.
"""

import json
import re
from typing import Any


def extract_stadium_data(html_content: str) -> dict[str, Any]:
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


def parse_moneyline(market: dict, all_selections: list[dict]) -> dict:
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
        odds = clean_odds(selection.get("displayOdds", {}).get("american"))

        if venue_role == "Away":
            result["away"] = odds
        elif venue_role == "Home":
            result["home"] = odds

    return result


def parse_spread(market: dict, all_selections: list[dict]) -> dict:
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
        odds = clean_odds(selection.get("displayOdds", {}).get("american"))

        if venue_role == "Away":
            result["away"] = points
            result["away_odds"] = odds
        elif venue_role == "Home":
            result["home"] = points
            result["home_odds"] = odds

    return result


def parse_total(market: dict, all_selections: list[dict]) -> dict:
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
        odds = clean_odds(selection.get("displayOdds", {}).get("american"))

        # Set line from either over or under
        if points is not None and result["line"] is None:
            result["line"] = abs(points)

        if label == "over":
            result["over"] = odds
        elif label == "under":
            result["under"] = odds

    return result


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
