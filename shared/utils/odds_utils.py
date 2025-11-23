"""Utilities for filtering and manipulating odds data."""

from typing import Dict, Any, Optional, List


def filter_odds_by_range(
    odds_data: Dict[str, Any],
    min_odds: int = -200,
    max_odds: int = 150
) -> Dict[str, Any]:
    """Filter odds data to only include odds within specified range.

    Filters both game lines and player props to remove odds outside the
    acceptable range. This ensures higher probability bets for better hit rates.

    Args:
        odds_data: Full odds data dictionary from JSON file
        min_odds: Minimum American odds (e.g., -200)
        max_odds: Maximum American odds (e.g., +150)

    Returns:
        Filtered odds_data dictionary with out-of-range odds removed
    """
    if not odds_data:
        return odds_data

    # Create a copy to avoid mutating the original
    filtered_data = odds_data.copy()

    # Filter game lines
    if "game_lines" in filtered_data:
        filtered_data["game_lines"] = _filter_game_lines(
            filtered_data["game_lines"],
            min_odds,
            max_odds
        )

    # Filter player props
    if "player_props" in filtered_data:
        filtered_data["player_props"] = _filter_player_props(
            filtered_data["player_props"],
            min_odds,
            max_odds
        )

    return filtered_data


def _is_valid_odds(odds: Optional[int], min_odds: int, max_odds: int) -> bool:
    """Check if odds are within valid range.

    Args:
        odds: American odds value (can be None)
        min_odds: Minimum acceptable odds
        max_odds: Maximum acceptable odds

    Returns:
        True if odds are within range, False otherwise
    """
    if odds is None:
        return False

    try:
        odds_int = int(odds)
        return min_odds <= odds_int <= max_odds
    except (ValueError, TypeError):
        return False


def _filter_game_lines(
    game_lines: Dict[str, Any],
    min_odds: int,
    max_odds: int
) -> Dict[str, Any]:
    """Filter game lines (moneyline, spread, total) to valid odds range.

    Args:
        game_lines: Game lines dictionary
        min_odds: Minimum acceptable odds
        max_odds: Maximum acceptable odds

    Returns:
        Filtered game lines dictionary
    """
    filtered = {}

    # Filter moneyline
    if "moneyline" in game_lines:
        moneyline = game_lines["moneyline"]
        filtered_ml = {}

        if _is_valid_odds(moneyline.get("away"), min_odds, max_odds):
            filtered_ml["away"] = moneyline["away"]

        if _is_valid_odds(moneyline.get("home"), min_odds, max_odds):
            filtered_ml["home"] = moneyline["home"]

        if filtered_ml:
            filtered["moneyline"] = filtered_ml

    # Filter spread
    if "spread" in game_lines:
        spread = game_lines["spread"]
        filtered_spread = {}

        # Copy line values
        if "away" in spread:
            filtered_spread["away"] = spread["away"]
        if "home" in spread:
            filtered_spread["home"] = spread["home"]

        # Filter odds
        if _is_valid_odds(spread.get("away_odds"), min_odds, max_odds):
            filtered_spread["away_odds"] = spread["away_odds"]

        if _is_valid_odds(spread.get("home_odds"), min_odds, max_odds):
            filtered_spread["home_odds"] = spread["home_odds"]

        # Only include spread if at least one odds is valid
        if "away_odds" in filtered_spread or "home_odds" in filtered_spread:
            filtered["spread"] = filtered_spread

    # Filter total
    if "total" in game_lines:
        total = game_lines["total"]
        filtered_total = {}

        # Copy line value
        if "line" in total:
            filtered_total["line"] = total["line"]

        # Filter odds
        if _is_valid_odds(total.get("over"), min_odds, max_odds):
            filtered_total["over"] = total["over"]

        if _is_valid_odds(total.get("under"), min_odds, max_odds):
            filtered_total["under"] = total["under"]

        # Only include total if at least one odds is valid
        if "over" in filtered_total or "under" in filtered_total:
            filtered["total"] = filtered_total

    return filtered


def _filter_player_props(
    player_props: List[Dict[str, Any]],
    min_odds: int,
    max_odds: int
) -> List[Dict[str, Any]]:
    """Filter player props to only include valid odds.

    Args:
        player_props: List of player prop dictionaries
        min_odds: Minimum acceptable odds
        max_odds: Maximum acceptable odds

    Returns:
        Filtered list of player props (removes props with no valid milestones)
    """
    filtered_props = []

    for prop in player_props:
        # Copy player metadata
        filtered_prop = {
            "player": prop.get("player"),
            "team": prop.get("team"),
            "position": prop.get("position"),
            "props": []
        }

        # Filter each market's milestones
        for market_prop in prop.get("props", []):
            filtered_market = {
                "market": market_prop.get("market"),
                "milestones": []
            }

            # Filter milestones by odds
            for milestone in market_prop.get("milestones", []):
                if _is_valid_odds(milestone.get("odds"), min_odds, max_odds):
                    filtered_market["milestones"].append(milestone)

            # Only include market if it has valid milestones
            if filtered_market["milestones"]:
                filtered_prop["props"].append(filtered_market)

        # Only include player prop if they have valid markets
        if filtered_prop["props"]:
            filtered_props.append(filtered_prop)

    return filtered_props
