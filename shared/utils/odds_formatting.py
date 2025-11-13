"""Shared utilities for formatting odds and spreads for display."""


def format_odds(odds: int | None) -> str:
    """Format odds for display.

    Args:
        odds: Odds value (e.g., -110, +340)

    Returns:
        Formatted string (e.g., "-110", "+340")
    """
    if odds is None:
        return "—"

    if odds > 0:
        return f"+{odds}"
    else:
        return str(odds)


def format_spread(spread: float | None) -> str:
    """Format spread for display.

    Args:
        spread: Spread value (e.g., -7.5, +3.5)

    Returns:
        Formatted string (e.g., "-7.5", "+3.5")
    """
    if spread is None:
        return "—"

    if spread > 0:
        return f"+{spread}"
    else:
        return str(spread)
