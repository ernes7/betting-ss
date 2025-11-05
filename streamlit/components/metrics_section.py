"""Metrics section component - displays EV+ performance metrics."""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path for nfl imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from nfl.constants import FIXED_BET_AMOUNT


def render_metrics(predictions: list[dict]):
    """Render EV+ Singles performance metrics in 4-column layout.

    Args:
        predictions: List of predictions with analysis data merged
    """
    # Calculate EV+ metrics (P/L stats from Claude AI analysis)
    preds_with_analysis = [p for p in predictions if p.get('analysis')]
    total_profit = sum([p['analysis']['summary']['total_profit'] for p in preds_with_analysis]) if preds_with_analysis else 0
    total_bets = sum([p['analysis']['summary']['total_bets'] for p in preds_with_analysis]) if preds_with_analysis else 0
    total_bets_won = sum([p['analysis']['summary']['bets_won'] for p in preds_with_analysis]) if preds_with_analysis else 0
    win_rate = (total_bets_won / total_bets * 100) if total_bets > 0 else 0

    # Calculate ROI
    total_risk = total_bets * FIXED_BET_AMOUNT if total_bets > 0 else 1
    roi = (total_profit / total_risk * 100) if total_risk > 0 else 0

    # Render metrics
    st.markdown("### EV+ Singles Performance")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        profit_color = "#38ef7d" if total_profit >= 0 else "#f45c43"
        st.markdown(f"""
            <div style='text-align: center;'>
                <div style='font-size: 0.9rem; color: rgba(255,255,255,0.8);'>Total Profit/Loss</div>
                <div style='font-size: 2.5rem; font-weight: 700; color: {profit_color};'>${total_profit:+.2f}</div>
                <div style='font-size: 0.8rem; color: rgba(255,255,255,0.6);'>Fixed ${FIXED_BET_AMOUNT} per bet</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.metric(
            "Total Bets",
            total_bets,
            delta=f"{len(preds_with_analysis)} games analyzed"
        )

    with col3:
        win_color = "#38ef7d" if win_rate >= 50 else "#f45c43"
        st.markdown(f"""
            <div style='text-align: center;'>
                <div style='font-size: 0.9rem; color: rgba(255,255,255,0.8);'>Win Rate</div>
                <div style='font-size: 2rem; font-weight: 700; color: {win_color};'>{win_rate:.1f}%</div>
                <div style='font-size: 0.8rem; color: rgba(255,255,255,0.6);'>{total_bets_won}/{total_bets} bets</div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        roi_color = "#38ef7d" if roi >= 0 else "#f45c43"
        st.markdown(f"""
            <div style='text-align: center;'>
                <div style='font-size: 0.9rem; color: rgba(255,255,255,0.8);'>ROI</div>
                <div style='font-size: 2rem; font-weight: 700; color: {roi_color};'>{roi:+.1f}%</div>
                <div style='font-size: 0.8rem; color: rgba(255,255,255,0.6);'>${total_profit:+.2f} / ${total_risk:.0f}</div>
            </div>
        """, unsafe_allow_html=True)

    st.divider()
