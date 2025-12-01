"""Streamlit dashboard utility modules."""

from .data_loader import (
    DataLoader,
    format_date,
    load_all_predictions,
    load_all_analyses,
    merge_predictions_with_analyses,
)
from .colors import get_profit_color, get_win_rate_color, get_ev_color, get_roi_color
from .analysis_helpers import (
    get_system_summary,
    detect_analysis_format,
    get_bet_results,
    calculate_combined_metrics,
)

__all__ = [
    # Data loader
    "DataLoader",
    "format_date",
    "load_all_predictions",
    "load_all_analyses",
    "merge_predictions_with_analyses",
    # Colors
    "get_profit_color",
    "get_win_rate_color",
    "get_ev_color",
    "get_roi_color",
    # Analysis helpers
    "get_system_summary",
    "detect_analysis_format",
    "get_bet_results",
    "calculate_combined_metrics",
]
