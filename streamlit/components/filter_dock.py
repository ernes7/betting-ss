"""Filter dock component - floating top bar with filters."""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import format_date


def render_filter_dock(predictions: list[dict]) -> dict:
    """Render floating filter dock at top of page.

    Args:
        predictions: List of all predictions to extract unique dates

    Returns:
        Dictionary with selected filter values:
            - date: Selected date (or "All")
            - status: Selected status filter
    """
    # Extract unique dates for filter
    unique_dates = sorted(set([p.get("game_date", p.get("date", "")) for p in predictions]), reverse=True)

    # Create date display mapping
    date_display_map = {d: format_date(d) for d in unique_dates}
    date_options_display = ["All Dates"] + [date_display_map[d] for d in unique_dates]

    # Status options
    status_options = ["All", "Analyzed", "Pending", "Profitable", "Unprofitable"]

    # Render filter dock using columns
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

    with col1:
        st.markdown("**Date**")
        selected_date_display = st.selectbox(
            "Date",
            date_options_display,
            index=0,
            label_visibility="collapsed",
            key="filter_date"
        )

    with col2:
        st.markdown("**Status**")
        selected_status = st.selectbox(
            "Status",
            status_options,
            index=0,
            label_visibility="collapsed",
            key="filter_status"
        )

    with col3:
        st.markdown("**Count**")
        count_display = len(predictions)
        st.markdown(f"<div style='padding: 8px; text-align: center; font-size: 1.1rem; font-weight: 600;'>{count_display} games</div>", unsafe_allow_html=True)

    with col4:
        st.markdown("**Reset**")
        if st.button("Reset", use_container_width=True):
            st.rerun()

    st.divider()

    # Map date display back to actual date
    if selected_date_display == "All Dates":
        selected_date = "All"
    else:
        selected_date = next((d for d, fmt in date_display_map.items() if fmt == selected_date_display), "All")

    return {
        "date": selected_date,
        "status": selected_status
    }
