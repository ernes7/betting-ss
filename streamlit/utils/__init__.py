"""Streamlit utility modules for UI components."""

# Color utilities
from .colors import get_profit_color, get_win_rate_color

# Analysis helpers
from .analysis_helpers import get_system_summary, detect_analysis_format

# Data loading utilities (from old utils.py)
from .data_loading import (
    format_date,
    load_all_predictions,
    load_all_analyses,
    merge_predictions_with_analyses
)

__all__ = [
    # Color utilities
    'get_profit_color',
    'get_win_rate_color',
    # Analysis helpers
    'get_system_summary',
    'detect_analysis_format',
    # Data loading
    'format_date',
    'load_all_predictions',
    'load_all_analyses',
    'merge_predictions_with_analyses',
]
