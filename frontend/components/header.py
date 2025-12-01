"""Header component for Streamlit dashboard."""

import streamlit as st


def render_header():
    """Render hero header with title and subtitle."""
    st.markdown("""
        <div style='text-align: center; padding: 20px 0;'>
            <h1 style='font-size: 3rem; margin: 0;'>Sports Betting Analytics</h1>
            <p style='font-size: 1.2rem; color: rgba(255,255,255,0.8); margin-top: 10px;'>
                AI + EV Dual System Performance Tracking
            </p>
        </div>
    """, unsafe_allow_html=True)
