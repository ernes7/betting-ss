"""Color utility functions for consistent styling across UI components."""


def get_profit_color(value: float) -> str:
    """Get color for profit/loss display.

    Args:
        value: Profit/loss value (positive or negative)

    Returns:
        Hex color code - green for profit, red for loss

    Examples:
        >>> get_profit_color(100.50)
        '#38ef7d'
        >>> get_profit_color(-50.25)
        '#f45c43'
        >>> get_profit_color(0)
        '#38ef7d'
    """
    return "#38ef7d" if value >= 0 else "#f45c43"


def get_win_rate_color(win_rate: float, threshold: float = 50.0) -> str:
    """Get color for win rate display.

    Args:
        win_rate: Win rate percentage (0-100)
        threshold: Threshold for "good" win rate (default: 50.0)

    Returns:
        Hex color code - green if above threshold, red if below

    Examples:
        >>> get_win_rate_color(55.5)
        '#38ef7d'
        >>> get_win_rate_color(45.0)
        '#f45c43'
        >>> get_win_rate_color(50.0)
        '#38ef7d'
        >>> get_win_rate_color(48.0, threshold=45.0)
        '#38ef7d'
    """
    return "#38ef7d" if win_rate >= threshold else "#f45c43"
