"""Programmatic bet result checker - validates bets against game results without AI."""

import re
from typing import Optional
from difflib import SequenceMatcher


# Market type to (table_name, column_name) mapping
MARKET_TO_TABLE_COLUMN = {
    "passing_yards": ("passing", "pass_yds"),
    "rushing_yards": ("rushing", "rush_yds"),
    "receiving_yards": ("receiving", "rec_yds"),
    "receptions": ("receiving", "rec"),
    "passing_tds": ("passing", "pass_td"),
    "rushing_tds": ("rushing", "rush_td"),
    "receiving_tds": ("receiving", "rec_td"),
    "anytime_td": None,  # Special case - check multiple tables
}

# Market name mappings for parsing bet strings
MARKET_NAME_MAP = {
    "passing yards": "passing_yards",
    "rushing yards": "rushing_yards",
    "receiving yards": "receiving_yards",
    "receptions": "receptions",
    "passing td": "passing_tds",
    "passing tds": "passing_tds",
    "rushing td": "rushing_tds",
    "rushing tds": "rushing_tds",
    "receiving td": "receiving_tds",
    "receiving tds": "receiving_tds",
}

# Nickname mappings: full name → common nickname (and vice versa)
NICKNAME_MAP = {
    # First names
    "cameron": "cam",
    "cam": "cameron",
    "christopher": "chris",
    "chris": "christopher",
    "michael": "mike",
    "mike": "michael",
    "william": "will",
    "will": "william",
    "robert": "rob",
    "rob": "robert",
    "robert": "bobby",
    "bobby": "robert",
    "richard": "rich",
    "rich": "richard",
    "richard": "ricky",
    "ricky": "richard",
    "anthony": "tony",
    "tony": "anthony",
    "kenneth": "ken",
    "ken": "kenneth",
    "kenneth": "kenny",
    "kenny": "kenneth",
    "daniel": "dan",
    "dan": "daniel",
    "daniel": "danny",
    "danny": "daniel",
    "matthew": "matt",
    "matt": "matthew",
    "nicholas": "nick",
    "nick": "nicholas",
    "jonathan": "jon",
    "jon": "jonathan",
    "jonathan": "johnny",
    "johnny": "jonathan",
    "benjamin": "ben",
    "ben": "benjamin",
    "joseph": "joe",
    "joe": "joseph",
    "joshua": "josh",
    "josh": "joshua",
    "samuel": "sam",
    "sam": "samuel",
    "timothy": "tim",
    "tim": "timothy",
    "gregory": "greg",
    "greg": "gregory",
    "patrick": "pat",
    "pat": "patrick",
    "james": "jim",
    "jim": "james",
    "james": "jimmy",
    "jimmy": "james",
    "alexander": "alex",
    "alex": "alexander",
    "zachary": "zach",
    "zach": "zachary",
    "raymond": "ray",
    "ray": "raymond",
    "theodore": "ted",
    "ted": "theodore",
    "theodore": "teddy",
    "teddy": "theodore",
    "edward": "ed",
    "ed": "edward",
    "edward": "eddie",
    "eddie": "edward",
    "thomas": "tom",
    "tom": "thomas",
    "thomas": "tommy",
    "tommy": "thomas",
    "andrew": "andy",
    "andy": "andrew",
    "andrew": "drew",
    "drew": "andrew",
    "phillip": "phil",
    "phil": "phillip",
    "stephen": "steve",
    "steve": "stephen",
    "amon-ra": "amon",
    "amon": "amon-ra",
    "jahmyr": "jahmyr",
    "devonta": "devonta",
    "de'von": "devon",
    "devon": "de'von",
    "d'andre": "dandre",
    "dandre": "d'andre",
    "ja'marr": "jamarr",
    "jamarr": "ja'marr",
}


def normalize_bet(bet: dict) -> dict:
    """Normalize AI prediction format to EV format.

    AI predictions have free-text: {"bet": "Amon-Ra St. Brown Over 70.5 Receiving Yards"}
    EV predictions have structured: {"market": "receiving_yards", "player": "...", "line": 70.5}

    This function parses the free-text bet string to extract structured fields.
    """
    # If already has market field, it's already in EV format
    if bet.get("market"):
        return bet

    # Get bet text from either 'bet' or 'description' field
    bet_text = bet.get("bet", bet.get("description", ""))
    if not bet_text:
        return bet

    normalized = bet.copy()
    normalized["description"] = bet_text

    # Strip trailing odds from bet text (e.g., "(-102)" or "(+150)")
    bet_text_clean = re.sub(r'\s*\([+-]?\d+\)\s*$', '', bet_text).strip()

    # Pattern 1: "Player Name Over/Under X.X Stat Type"
    # e.g., "Amon-Ra St. Brown Over 70.5 Receiving Yards"
    prop_pattern = r"^(.+?)\s+(Over|Under)\s+([\d.]+)\s+(Passing Yards|Rushing Yards|Receiving Yards|Receptions|Passing TDs?|Rushing TDs?|Receiving TDs?)$"
    match = re.match(prop_pattern, bet_text_clean, re.IGNORECASE)
    if match:
        normalized["player"] = match.group(1).strip()
        normalized["side"] = match.group(2).lower()
        normalized["line"] = float(match.group(3))
        stat_type = match.group(4).lower()
        normalized["market"] = MARKET_NAME_MAP.get(stat_type, stat_type.replace(" ", "_"))
        normalized["bet_type"] = "player_prop"
        return normalized

    # Pattern 2: Anytime TD - "Player Name Anytime TD" or "Player Name Anytime Touchdown"
    td_pattern = r"^(.+?)\s+Anytime\s+(?:TD|Touchdown).*$"
    match = re.match(td_pattern, bet_text_clean, re.IGNORECASE)
    if match:
        normalized["player"] = match.group(1).strip()
        normalized["market"] = "anytime_td"
        normalized["bet_type"] = "player_prop"
        normalized["line"] = 0.5
        normalized["side"] = "over"
        return normalized

    # Pattern 3: Spread - "Team +/- X.X" or "Team Name +X.X"
    # e.g., "Lions -13.5" or "DET Lions -13.5" or "Carolina Panthers +3.5"
    spread_pattern = r"^(.+?)\s+([+-]?\d+\.?\d*)$"
    match = re.match(spread_pattern, bet_text_clean, re.IGNORECASE)
    if match:
        team = match.group(1).strip()
        line = float(match.group(2))
        normalized["team"] = team
        normalized["line"] = line
        normalized["bet_type"] = "spread"
        # Assume home if we can't determine
        normalized["side"] = "home"
        return normalized

    # Pattern 4: Total - "Over/Under X.X Total Points"
    total_pattern = r"^(Over|Under)\s+([\d.]+)\s+(?:Total\s+)?Points?$"
    match = re.match(total_pattern, bet_text_clean, re.IGNORECASE)
    if match:
        normalized["side"] = match.group(1).lower()
        normalized["line"] = float(match.group(2))
        normalized["bet_type"] = "total"
        return normalized

    # Pattern 5: Game/Team Total - "Game Total Over/Under X.X Points"
    # e.g., "Game Total Under 44.5 Points" or "Bengals Team Total Over 24.5 Points"
    game_total_pattern = r"^(?:Game\s+)?(?:Total\s+)?(Over|Under)\s+([\d.]+)\s+Points?$"
    match = re.match(game_total_pattern, bet_text_clean, re.IGNORECASE)
    if match:
        normalized["side"] = match.group(1).lower()
        normalized["line"] = float(match.group(2))
        normalized["bet_type"] = "total"
        return normalized

    # Pattern 6: Team Total - "Team Name Team Total Over/Under X.X Points"
    team_total_pattern = r"^(.+?)\s+Team\s+Total\s+(Over|Under)\s+([\d.]+)\s+Points?$"
    match = re.match(team_total_pattern, bet_text_clean, re.IGNORECASE)
    if match:
        normalized["team"] = match.group(1).strip()
        normalized["side"] = match.group(2).lower()
        normalized["line"] = float(match.group(3))
        normalized["bet_type"] = "team_total"
        return normalized

    # Pattern 7: Moneyline - "Team Moneyline" or "Team ML"
    ml_pattern = r"^(.+?)\s+(?:Moneyline|ML)$"
    match = re.match(ml_pattern, bet_text_clean, re.IGNORECASE)
    if match:
        normalized["team"] = match.group(1).strip()
        normalized["bet_type"] = "moneyline"
        normalized["line"] = 0
        return normalized

    # Couldn't parse - return original
    return normalized


def normalize_name(name: str) -> str:
    """Normalize player name for matching.

    Removes suffixes like Jr., III, etc. and converts to lowercase.
    """
    if not name:
        return ""

    name = name.lower().strip()

    # Remove common suffixes
    suffixes = [" jr.", " jr", " iii", " ii", " iv", " sr.", " sr"]
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)]

    return name.strip()


def get_name_variants(name: str) -> list:
    """Get all variants of a name including nickname swaps.

    Args:
        name: Full name like "Cameron Ward"

    Returns:
        List of name variants: ["cameron ward", "cam ward"]
    """
    normalized = normalize_name(name)
    variants = [normalized]

    parts = normalized.split()
    if parts:
        first_name = parts[0]
        rest = " ".join(parts[1:]) if len(parts) > 1 else ""

        # Check if first name has a nickname variant
        if first_name in NICKNAME_MAP:
            nickname = NICKNAME_MAP[first_name]
            variant = f"{nickname} {rest}".strip()
            variants.append(variant)

    return variants


def name_similarity(name1: str, name2: str) -> float:
    """Calculate similarity ratio between two names.

    Tries nickname variations to improve matching.
    """
    # Get all variants for both names
    variants1 = get_name_variants(name1)
    variants2 = get_name_variants(name2)

    # Try all combinations and return the best score
    best_score = 0
    for v1 in variants1:
        for v2 in variants2:
            score = SequenceMatcher(None, v1, v2).ratio()
            if score > best_score:
                best_score = score

    return best_score


def find_player_in_table(player_name: str, table_data: list, threshold: float = 0.85) -> Optional[dict]:
    """Find a player in a table by fuzzy name matching.

    Args:
        player_name: The player name to search for
        table_data: List of row dicts from the results table
        threshold: Minimum similarity ratio for a match

    Returns:
        The matching row dict, or None if not found
    """
    if not table_data:
        return None

    normalized_target = normalize_name(player_name)
    best_match = None
    best_score = 0

    for row in table_data:
        row_player = row.get("player", "")
        if not row_player:
            continue

        score = name_similarity(player_name, row_player)
        if score > best_score and score >= threshold:
            best_score = score
            best_match = row

    return best_match


def get_stat_value(row: dict, column: str) -> Optional[float]:
    """Extract a numeric stat value from a row.

    Args:
        row: The table row dict
        column: The column name to extract

    Returns:
        The numeric value, or None if not found/invalid
    """
    if not row or column not in row:
        return None

    value = row[column]
    if value is None or value == "" or value == "-":
        return None

    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def check_player_prop(bet: dict, result_data: dict) -> dict:
    """Check a player prop bet against results.

    Args:
        bet: The bet dict with market, player, line, side, odds
        result_data: The game results with tables

    Returns:
        Dict with won, actual, line, profit
    """
    market = bet.get("market")
    player = bet.get("player")
    line = bet.get("line")
    side = bet.get("side", "over").lower()
    odds = bet.get("odds", -110)
    description = bet.get("description", "")

    # Get table and column mapping
    mapping = MARKET_TO_TABLE_COLUMN.get(market)
    if mapping is None:
        # Handle anytime TD special case
        if market == "anytime_td":
            return check_anytime_td(bet, result_data)
        return {
            "bet": description,
            "won": None,
            "actual": None,
            "line": line,
            "profit": 0,
            "error": f"Unknown market type: {market}"
        }

    table_name, column_name = mapping
    tables = result_data.get("tables", {})

    # Get the table data
    table = tables.get(table_name, {})
    table_data = table.get("data", [])

    if not table_data:
        return {
            "bet": description,
            "won": None,
            "actual": None,
            "line": line,
            "profit": 0,
            "error": f"Table '{table_name}' not found or empty"
        }

    # Find the player
    player_row = find_player_in_table(player, table_data)

    if not player_row:
        # Player not found - might not have played, check other tables
        # Try searching all offensive tables
        for alt_table in ["passing", "rushing", "receiving"]:
            if alt_table != table_name:
                alt_data = tables.get(alt_table, {}).get("data", [])
                player_row = find_player_in_table(player, alt_data)
                if player_row:
                    break

    if not player_row:
        # Player not in any table = 0 stats (didn't play or didn't record any)
        # This is a valid case - compare 0 against the line
        actual = 0
        if side == "over":
            won = actual > line
        else:
            won = actual < line
        profit = calculate_profit(won, odds)
        return {
            "bet": description,
            "won": won,
            "actual": actual,
            "line": line,
            "profit": profit
        }

    # Get the actual value
    actual = get_stat_value(player_row, column_name)

    if actual is None:
        # Try to find the stat in the player row with alternate column names
        actual = 0  # Default to 0 if player found but stat missing (didn't record any)

    # Determine win/loss
    if side == "over":
        won = actual > line
    else:  # under
        won = actual < line

    # Calculate profit
    profit = calculate_profit(won, odds)

    return {
        "bet": description,
        "won": won,
        "actual": actual,
        "line": line,
        "profit": profit
    }


def check_anytime_td(bet: dict, result_data: dict) -> dict:
    """Check an anytime TD scorer bet.

    Checks if the player scored any TD (passing, rushing, or receiving).
    """
    player = bet.get("player")
    odds = bet.get("odds", -110)
    description = bet.get("description", "")

    tables = result_data.get("tables", {})
    scored_td = False

    # Check all offensive tables for TDs
    for table_name, td_column in [("passing", "pass_td"), ("rushing", "rush_td"), ("receiving", "rec_td")]:
        table_data = tables.get(table_name, {}).get("data", [])
        player_row = find_player_in_table(player, table_data)

        if player_row:
            td_count = get_stat_value(player_row, td_column)
            if td_count and td_count > 0:
                scored_td = True
                break

    profit = calculate_profit(scored_td, odds)

    return {
        "bet": description,
        "won": scored_td,
        "actual": "TD" if scored_td else "No TD",
        "line": "Anytime TD",
        "profit": profit
    }


def check_spread_bet(bet: dict, result_data: dict) -> dict:
    """Check a spread bet against final score.

    Args:
        bet: The bet dict with team, line, side (home/away), odds
        result_data: The game results with final_score and teams

    Returns:
        Dict with won, actual, line, profit
    """
    line = bet.get("line", 0)
    odds = bet.get("odds", -110)
    description = bet.get("description", "")
    bet_team = bet.get("team", "").lower()

    final_score = result_data.get("final_score", {})
    home_score = final_score.get("home", 0)
    away_score = final_score.get("away", 0)

    if home_score is None or away_score is None:
        return {
            "bet": description,
            "won": None,
            "actual": None,
            "line": line,
            "profit": 0,
            "error": "Final score not available"
        }

    # Determine if bet team is home or away from results data
    teams = result_data.get("teams", {})
    home_team = teams.get("home", "").lower()
    away_team = teams.get("away", "").lower()

    # Try to match bet team to home or away
    side = None
    if bet_team:
        # Check for partial match (e.g., "bears" in "chicago bears" or "bears")
        if bet_team in home_team or home_team in bet_team:
            side = "home"
        elif bet_team in away_team or away_team in bet_team:
            side = "away"

    # If we couldn't determine, fall back to the bet's side field
    if side is None:
        side = bet.get("side", "home").lower()

    # Calculate margin from perspective of the bet side
    if side == "home":
        margin = home_score - away_score
    else:
        margin = away_score - home_score

    # Check if spread is covered (margin > -line for favorite, margin > line for underdog)
    won = margin + line > 0

    # Handle push (exact tie with spread)
    if margin + line == 0:
        won = None  # Push
        profit = 0
    else:
        profit = calculate_profit(won, odds)

    return {
        "bet": description,
        "won": won,
        "actual": f"{margin:+.1f} margin",
        "line": line,
        "profit": profit
    }


def check_total_bet(bet: dict, result_data: dict) -> dict:
    """Check a total (over/under) bet against final score.

    Args:
        bet: The bet dict with line, side (over/under), odds
        result_data: The game results with final_score

    Returns:
        Dict with won, actual, line, profit
    """
    line = bet.get("line", 0)
    side = bet.get("side", "over").lower()
    odds = bet.get("odds", -110)
    description = bet.get("description", "")

    final_score = result_data.get("final_score", {})
    home_score = final_score.get("home", 0)
    away_score = final_score.get("away", 0)

    if home_score is None or away_score is None:
        return {
            "bet": description,
            "won": None,
            "actual": None,
            "line": line,
            "profit": 0,
            "error": "Final score not available"
        }

    total = home_score + away_score

    if side == "over":
        won = total > line
    else:
        won = total < line

    # Handle push
    if total == line:
        won = None
        profit = 0
    else:
        profit = calculate_profit(won, odds)

    return {
        "bet": description,
        "won": won,
        "actual": total,
        "line": line,
        "profit": profit
    }


def calculate_profit(won: bool, odds: int, stake: float = 100) -> float:
    """Calculate profit/loss based on American odds.

    Args:
        won: Whether the bet won
        odds: American odds (e.g., -110, +150)
        stake: Bet amount (default $100)

    Returns:
        Profit/loss amount (positive for win, negative for loss)
    """
    if won is None:
        return 0  # Push

    if not won:
        return -stake

    # Calculate winnings for American odds
    if odds > 0:
        return stake * (odds / 100)
    else:
        return stake * (100 / abs(odds))


def check_bets(prediction_data: dict, result_data: dict) -> dict:
    """Check all bets in a prediction against game results.

    Args:
        prediction_data: The prediction JSON with bets array
        result_data: The game results JSON with tables and final_score

    Returns:
        Analysis dict with bet_results and summary
    """
    bets = prediction_data.get("bets", [])
    bet_results = []

    for bet in bets:
        # Normalize AI format to EV format (parses free-text bet strings)
        bet = normalize_bet(bet)

        bet_type = bet.get("bet_type", "player_prop")

        if bet_type == "player_prop":
            result = check_player_prop(bet, result_data)
        elif bet_type == "spread":
            result = check_spread_bet(bet, result_data)
        elif bet_type == "total":
            result = check_total_bet(bet, result_data)
        elif bet_type == "team_total":
            # Team total - check team's score vs line
            # For now, treat as regular total (sum of both teams)
            # since we don't have per-team score mapping yet
            result = check_total_bet(bet, result_data)
        elif bet_type == "moneyline":
            # Moneyline is just spread with 0 line
            bet_copy = bet.copy()
            bet_copy["line"] = 0
            result = check_spread_bet(bet_copy, result_data)
        else:
            result = {
                "bet": bet.get("description", "Unknown bet"),
                "won": None,
                "actual": None,
                "line": bet.get("line"),
                "profit": 0,
                "error": f"Unknown bet type: {bet_type}"
            }

        bet_results.append(result)

    # Calculate summary
    total_bets = len(bet_results)
    bets_won = sum(1 for r in bet_results if r.get("won") is True)
    bets_lost = sum(1 for r in bet_results if r.get("won") is False)
    total_profit = sum(r.get("profit", 0) for r in bet_results)
    total_staked = total_bets * 100  # Assuming $100 per bet

    win_rate = (bets_won / total_bets * 100) if total_bets > 0 else 0
    roi = (total_profit / total_staked * 100) if total_staked > 0 else 0

    return {
        "bet_results": bet_results,
        "summary": {
            "total_bets": total_bets,
            "bets_won": bets_won,
            "bets_lost": bets_lost,
            "win_rate": round(win_rate, 1),
            "total_profit": round(total_profit, 2),
            "total_staked": total_staked,
            "roi_percent": round(roi, 1)
        }
    }
