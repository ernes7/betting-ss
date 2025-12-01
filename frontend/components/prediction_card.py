"""Prediction card component - clean card with profit/ROI integration."""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import format_date
from utils.colors import get_profit_color
from theme import AI_GRADIENT, EV_GRADIENT

# Add project root to path for sports imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from sports.nfl.teams import TEAMS


def _get_team_mascot(full_name: str) -> str:
    """Extract team mascot from full team name."""
    for team in TEAMS:
        if team["name"] == full_name:
            return team["mascot"]
    return full_name.split()[-1] if full_name else "Unknown"


def render_prediction_card(prediction: dict, index: int):
    """Render enhanced prediction card with profit/ROI integration.

    Args:
        prediction: Grouped prediction dictionary with ai_prediction, ev_prediction, and analysis
        index: Card index for unique key generation
    """
    # Extract data
    teams = prediction.get("teams", ["Unknown", "Unknown"])
    date = prediction.get("game_date", "Unknown")
    ai_prediction = prediction.get("ai_prediction")
    ev_prediction = prediction.get("ev_prediction")
    analysis = prediction.get("analysis")

    # Extract team mascots
    team1_mascot = _get_team_mascot(teams[0])
    team2_mascot = _get_team_mascot(teams[1])

    # Determine if we have analysis
    has_analysis = analysis and analysis.get("summary")

    # Extract analysis summary if available
    if has_analysis:
        summary = analysis.get("summary", {})
        total_profit = summary.get("total_profit", 0)
        win_rate = summary.get("win_rate", 0)
        roi = summary.get("roi_percent", 0)
        bets_won = summary.get("bets_won", 0)
        total_bets = summary.get("total_bets", 0)
        profit_color = get_profit_color(total_profit)
        card_status = "analyzed"
        final_score = analysis.get("final_score", {})
    else:
        total_profit = 0
        win_rate = 0
        roi = 0
        bets_won = 0
        total_bets = 0
        profit_color = "#86A5D9"
        card_status = "pending"
        final_score = {}

    # Build card header with profit/ROI if analyzed
    if has_analysis:
        st.markdown(f"""
        <div class="prediction-card prediction-card-{card_status}">
            <div class="card-header-enhanced">
                <div class="card-date">{format_date(date)}</div>
                <div class="card-matchup-main">{team1_mascot} vs {team2_mascot}</div>
                {f'<div class="final-score">{final_score.get("away", 0)}-{final_score.get("home", 0)}</div>' if final_score else ''}
            </div>
            <div class="profit-bar">
                <div class="profit-item">
                    <span class="profit-label">Profit</span>
                    <span class="profit-value" style="color: {profit_color};">${total_profit:+.0f}</span>
                </div>
                <div class="profit-item">
                    <span class="profit-label">ROI</span>
                    <span class="profit-value" style="color: {profit_color};">{roi:+.1f}%</span>
                </div>
                <div class="profit-item">
                    <span class="profit-label">Win Rate</span>
                    <span class="profit-value">{win_rate:.0f}% ({bets_won}/{total_bets})</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="prediction-card prediction-card-{card_status}">
            <div class="card-header-enhanced">
                <div class="card-date">{format_date(date)}</div>
                <div class="card-matchup-main">{team1_mascot} vs {team2_mascot}</div>
                <div class="pending-badge">Pending Analysis</div>
            </div>
        """, unsafe_allow_html=True)

    # Render AI section (only show if exists, old legacy predictions)
    if ai_prediction:
        _render_prediction_section("AI", ai_prediction, AI_GRADIENT, analysis)

    # Render EV section
    if ev_prediction:
        _render_prediction_section("EV", ev_prediction, EV_GRADIENT, analysis)

    # Close card
    st.markdown("</div>", unsafe_allow_html=True)


def _render_prediction_section(system_name: str, prediction_data: dict, color: str, analysis: dict = None):
    """Render a single prediction section with bet outcomes.

    Args:
        system_name: "AI" or "EV"
        prediction_data: Prediction data for this system
        color: Gradient color for badge
        analysis: Analysis data with bet results (optional)
    """
    # Check if we have predictions
    if not prediction_data or not prediction_data.get("bets"):
        st.markdown(f"""
        <div class="prediction-section">
            <div class="section-header">
                <div class="system-badge" style="background: {color};">{system_name}</div>
                <div class="section-label" style="color: rgba(255,255,255,0.4);">No predictions</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Extract bets
    bets = prediction_data.get("bets", [])

    # Get bet results from analysis if available
    bet_results = []
    if analysis and analysis.get("bet_results"):
        bet_results = analysis.get("bet_results", [])

    # Get summary stats
    summary = prediction_data.get("summary", {})
    avg_ev = summary.get("avg_ev", summary.get("top_5_avg_ev", 0))

    # Render section header
    st.markdown(f"""
    <div class="prediction-section">
        <div class="section-header">
            <div class="system-badge" style="background: {color};">{system_name}</div>
            <div class="section-stats">
                <span>{len(bets)} bets</span>
                <span>Avg EV: {avg_ev:.1f}%</span>
            </div>
        </div>
        <div class="bet-list">
    """, unsafe_allow_html=True)

    # Render each bet with outcome if available
    for i, bet in enumerate(bets):
        # Handle different field names
        description = bet.get('description', bet.get('bet', 'Unknown'))
        odds = bet.get('odds', 0)
        ev_percent = bet.get('ev_percent', bet.get('expected_value', 0))

        # Truncate long descriptions
        if len(description) > 45:
            description = description[:42] + "..."

        # Check if we have result for this bet
        bet_result = bet_results[i] if i < len(bet_results) else None

        if bet_result:
            # Analyzed bet - show outcome
            won = bet_result.get("won", False)
            profit = bet_result.get("profit", 0)
            icon = "✓" if won else "✗"
            icon_class = "bet-won-icon" if won else "bet-lost-icon"
            profit_color = get_profit_color(profit)

            st.markdown(f"""
            <div class="bet-row bet-row-analyzed">
                <span class="{icon_class}">{icon}</span>
                <div class="bet-desc">{description}</div>
                <div class="bet-outcome">
                    <span style="color: {profit_color}; font-weight: 700;">${profit:+.0f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Pending bet - show EV and odds
            odds_str = f"{odds:+d}" if odds else "N/A"

            st.markdown(f"""
            <div class="bet-row">
                <span class="bet-pending-icon">•</span>
                <div class="bet-desc">{description}</div>
                <div class="bet-stats-inline">
                    <span class="bet-odds">{odds_str}</span>
                    <span class="bet-ev">+{ev_percent:.1f}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Close bet list and section
    st.markdown("""
        </div>
    </div>
    """, unsafe_allow_html=True)
