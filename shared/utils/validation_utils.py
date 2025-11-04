"""Validation utilities for input validation.

This module provides reusable validation functions for common
input types like dates, team abbreviations, and odds formats.
"""

import re
from datetime import datetime
from typing import Tuple


def validate_date_format(date_string: str) -> Tuple[bool, str]:
    """Validate date format (YYYY-MM-DD).

    Args:
        date_string: Date string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check basic format
    parts = date_string.split("-")
    if len(parts) != 3:
        return False, "Date must be in YYYY-MM-DD format"

    # Check if all parts are digits
    if not all(p.isdigit() for p in parts):
        return False, "Date must contain only numbers"

    # Check lengths
    year, month, day = parts
    if len(year) != 4 or len(month) != 2 or len(day) != 2:
        return False, "Date must be in YYYY-MM-DD format (e.g., 2025-10-26)"

    # Try to parse as actual date
    try:
        datetime.strptime(date_string, "%Y-%m-%d")
        return True, ""
    except ValueError as e:
        return False, f"Invalid date: {str(e)}"


def validate_team_abbreviation(abbr: str, min_length: int = 2, max_length: int = 3) -> Tuple[bool, str]:
    """Validate team abbreviation format.

    Args:
        abbr: Team abbreviation to validate
        min_length: Minimum length (default: 2)
        max_length: Maximum length (default: 3)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not abbr:
        return False, "Abbreviation cannot be empty"

    if not abbr.replace("_", "").replace("-", "").isalnum():
        return False, "Abbreviation must contain only letters, numbers, underscores, or hyphens"

    if len(abbr) < min_length or len(abbr) > max_length:
        return False, f"Abbreviation must be between {min_length} and {max_length} characters"

    return True, ""


def validate_odds_format(odds_str: str) -> Tuple[bool, str]:
    """Validate American odds format (+150, -110, etc.).

    Args:
        odds_str: Odds string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Remove whitespace
    odds_str = odds_str.strip()

    # Check if it matches American odds format
    if not re.match(r'^[+-]\d+$', odds_str):
        return False, "Odds must be in American format (e.g., +150, -110)"

    # Convert to integer to verify it's a valid number
    try:
        odds_value = int(odds_str)
        # American odds should typically be at least ±100
        if abs(odds_value) < 100:
            return False, "Odds should typically be ±100 or greater"
        return True, ""
    except ValueError:
        return False, "Invalid odds value"


def validate_probability(prob: float) -> Tuple[bool, str]:
    """Validate probability value (0-100).

    Args:
        prob: Probability value to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(prob, (int, float)):
        return False, "Probability must be a number"

    if prob < 0 or prob > 100:
        return False, "Probability must be between 0 and 100"

    return True, ""


def validate_percentage(pct_str: str) -> Tuple[bool, str]:
    """Validate percentage string format (e.g., "25%", "90.5%").

    Args:
        pct_str: Percentage string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Remove whitespace and % sign
    cleaned = pct_str.strip().rstrip("%")

    try:
        value = float(cleaned)
        if value < 0 or value > 100:
            return False, "Percentage must be between 0 and 100"
        return True, ""
    except ValueError:
        return False, "Invalid percentage format (expected: 25% or 25)"


def validate_bet_amount(amount: float, min_amount: float = 0.01) -> Tuple[bool, str]:
    """Validate bet amount.

    Args:
        amount: Bet amount to validate
        min_amount: Minimum allowed amount (default: 0.01)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(amount, (int, float)):
        return False, "Bet amount must be a number"

    if amount < min_amount:
        return False, f"Bet amount must be at least ${min_amount}"

    if amount <= 0:
        return False, "Bet amount must be positive"

    return True, ""


def validate_kelly_percentage(kelly_pct: float) -> Tuple[bool, str]:
    """Validate Kelly criterion percentage.

    Args:
        kelly_pct: Kelly percentage to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(kelly_pct, (int, float)):
        return False, "Kelly percentage must be a number"

    # Kelly should typically be between 0 and 100 (representing % of bankroll)
    # But can exceed 100% in rare cases of very high EV
    if kelly_pct < 0:
        return False, "Kelly percentage cannot be negative"

    if kelly_pct > 200:
        return False, "Kelly percentage exceeds 200% - likely calculation error"

    return True, ""


def is_valid_inquirer_date(answers, current) -> bool:
    """Inquirer validator for date format.

    Args:
        answers: Previous answers (unused)
        current: Current input value

    Returns:
        True if valid, False otherwise
    """
    is_valid, _ = validate_date_format(current)
    return is_valid
