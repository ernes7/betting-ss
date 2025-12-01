"""Sports Betting Analytics Dashboard - Main Entry Point.

Component-based Streamlit application for EV+ singles betting analysis.
"""

import streamlit as st

# Import theme and utilities
from theme import get_custom_css
from utils import load_all_predictions, load_all_analyses, merge_predictions_with_analyses

# Import components
from components import (
    render_header,
    render_filter_dock,
    render_metrics,
    render_prediction_card,
    render_profit_charts
)


def apply_filters(predictions: list[dict], filters: dict) -> list[dict]:
    """Apply filters to predictions list.

    Args:
        predictions: List of all predictions
        filters: Dictionary with filter values (date, status)

    Returns:
        Filtered list of predictions
    """
    filtered = predictions

    # Date filter
    if filters["date"] != "All":
        filtered = [
            p for p in filtered
            if p.get("game_date", p.get("date", "")) == filters["date"]
        ]

    # Status filter
    if filters["status"] != "All":
        if filters["status"] == "Analyzed":
            filtered = [p for p in filtered if p.get('analysis')]
        elif filters["status"] == "Pending":
            filtered = [p for p in filtered if not p.get('analysis')]
        elif filters["status"] == "Profitable":
            filtered = [p for p in filtered if p.get('analysis') and p['analysis']['summary']['total_profit'] > 0]
        elif filters["status"] == "Unprofitable":
            filtered = [p for p in filtered if p.get('analysis') and p['analysis']['summary']['total_profit'] <= 0]

    return filtered


def main():
    """Main Streamlit application."""

    # Page configuration
    st.set_page_config(
        page_title="Sports Betting Analytics",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Apply custom CSS theme
    st.markdown(get_custom_css(), unsafe_allow_html=True)

    # Render header
    render_header()

    # Load data
    predictions = load_all_predictions()
    analyses = load_all_analyses()
    predictions = merge_predictions_with_analyses(predictions, analyses)

    # Sort by date (newest first)
    predictions.sort(key=lambda x: x.get("generated_at", ""), reverse=True)

    # Render filter dock and get selected filters
    filters = render_filter_dock(predictions)

    # Apply filters
    filtered_predictions = apply_filters(predictions, filters)

    # Render metrics section (uses all predictions for totals)
    render_metrics(predictions)

    # Render profit charts
    render_profit_charts(predictions)

    # Display filtered predictions count
    st.markdown(f"### {len(filtered_predictions)} Prediction{'s' if len(filtered_predictions) != 1 else ''}")

    if not filtered_predictions:
        st.info("No predictions match your filters. Try adjusting the filters above.")
    else:
        # Render predictions in grid (3 per row)
        for i in range(0, len(filtered_predictions), 3):
            cols = st.columns(3)
            for j in range(3):
                idx = i + j
                if idx < len(filtered_predictions):
                    with cols[j]:
                        render_prediction_card(filtered_predictions[idx], idx)

    # Footer
    st.divider()
    st.markdown("""
        <div style='text-align: center; color: rgba(255,255,255,0.6); font-size: 0.9rem; padding: 20px 0;'>
            Built with Claude Code | Powered by Claude Sonnet 4.5 | Component-Based Architecture
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
