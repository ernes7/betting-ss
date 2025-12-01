"""Color utility functions for the Streamlit dashboard."""


def get_profit_color(value: float) -> str:
    """Get color for profit/loss value.

    Args:
        value: Profit/loss value (positive = profit, negative = loss)

    Returns:
        CSS color string
    """
    if value > 0:
        return "#22C55E"  # Green
    elif value < 0:
        return "#EF4444"  # Red
    else:
        return "#6B7280"  # Gray


def get_win_rate_color(win_rate: float) -> str:
    """Get color for win rate percentage.

    Args:
        win_rate: Win rate as percentage (0-100)

    Returns:
        CSS color string
    """
    if win_rate >= 55:
        return "#22C55E"  # Green - good
    elif win_rate >= 50:
        return "#EAB308"  # Yellow - breakeven
    else:
        return "#EF4444"  # Red - losing


def get_ev_color(ev: float) -> str:
    """Get color for expected value.

    Args:
        ev: Expected value percentage

    Returns:
        CSS color string
    """
    if ev >= 5:
        return "#22C55E"  # Green - strong positive EV
    elif ev >= 0:
        return "#EAB308"  # Yellow - slight positive EV
    else:
        return "#EF4444"  # Red - negative EV


def get_roi_color(roi: float) -> str:
    """Get color for ROI percentage.

    Args:
        roi: ROI as percentage

    Returns:
        CSS color string
    """
    if roi > 10:
        return "#22C55E"  # Green - strong ROI
    elif roi > 0:
        return "#84CC16"  # Light green - positive ROI
    elif roi == 0:
        return "#6B7280"  # Gray - breakeven
    else:
        return "#EF4444"  # Red - negative ROI
