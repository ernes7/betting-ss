"""Frontend module for Streamlit dashboard."""

from frontend.config import (
    StreamlitServiceConfig,
    DisplayConfig,
    DataPathConfig,
    ThemeConfig,
    get_default_config,
    get_nfl_only_config,
    get_nba_only_config,
)
from frontend.utils import (
    DataLoader,
    format_date,
    load_all_predictions,
    load_all_analyses,
    merge_predictions_with_analyses,
    get_profit_color,
    get_win_rate_color,
    get_ev_color,
    get_roi_color,
    get_system_summary,
    detect_analysis_format,
    get_bet_results,
    calculate_combined_metrics,
)

__all__ = [
    # Config
    "StreamlitServiceConfig",
    "DisplayConfig",
    "DataPathConfig",
    "ThemeConfig",
    "get_default_config",
    "get_nfl_only_config",
    "get_nba_only_config",
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
