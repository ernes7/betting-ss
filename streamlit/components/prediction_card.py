"""Prediction card component - compact square card for grid layout."""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import format_date

# Add project root to path for nfl imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from nfl.constants import FIXED_BET_AMOUNT
from nfl.teams import TEAMS


def _get_team_mascot(full_name: str) -> str:
    """Extract team mascot from full team name.

    Args:
        full_name: Full team name (e.g., "New Orleans Saints")

    Returns:
        Team mascot (e.g., "Saints")
    """
    for team in TEAMS:
        if team["name"] == full_name:
            return team["mascot"]
    # Fallback: return last word
    return full_name.split()[-1] if full_name else "Unknown"


def render_prediction_card(prediction: dict, index: int):
    """Render compact square prediction card for grid layout.

    Args:
        prediction: Prediction dictionary with analysis data
        index: Card index for unique key generation
    """
    # Extract data
    teams = prediction.get("teams", ["Unknown", "Unknown"])
    home_team = prediction.get("home_team", "Unknown")
    date = prediction.get("date", prediction.get("game_date", "Unknown"))
    analysis = prediction.get("analysis")
    bets = prediction.get("bets", [])

    # Calculate stats
    if analysis:
        summary = analysis.get('summary', {})
        total_profit = summary.get('total_profit', 0)
        win_rate = summary.get('win_rate', 0)
        bets_won = summary.get('bets_won', 0)
        total_bets = summary.get('total_bets', 0)
        roi = summary.get('roi_percent', 0)
        profit_color = "#38ef7d" if total_profit >= 0 else "#f45c43"
        status = "analyzed"
    else:
        total_profit = 0
        win_rate = 0
        bets_won = 0
        total_bets = len(bets)
        roi = 0
        profit_color = "#86A5D9"
        status = "pending"

    # Get bet results for display
    bet_results = analysis.get('bet_results', []) if analysis else []
    bet_display_items = []

    # Show all bets (up to 5)
    for i, bet in enumerate(bets[:5]):
        bet_desc = bet.get('bet', 'Unknown')
        # Shorten bet description if too long
        if len(bet_desc) > 50:
            bet_desc = bet_desc[:47] + "..."

        if analysis and i < len(bet_results):
            result = bet_results[i]
            won = result.get('won', False)
            icon = "✓" if won else "✗"
            bet_display_items.append(f'<div class="bet-item"><span class="bet-icon {"bet-won" if won else "bet-lost"}">{icon}</span> {bet_desc}</div>')
        else:
            bet_display_items.append(f'<div class="bet-item"><span class="bet-icon bet-pending">•</span> {bet_desc}</div>')

    bets_html = "".join(bet_display_items)

    # Extract team mascots
    team1_mascot = _get_team_mascot(teams[0])
    team2_mascot = _get_team_mascot(teams[1])

    # Build card HTML
    card_html = f"""
    <div class="square-card square-card-{status}">
        <div class="card-header">
            <div class="card-date">{format_date(date)}</div>
            <div class="card-profit" style="color: {profit_color};">${total_profit:+.0f}</div>
        </div>
        <div class="card-matchup">
            <div class="matchup-text">{team1_mascot} vs {team2_mascot}</div>
        </div>
        <div class="card-stats">
            <div class="stat-item">
                <div class="stat-label">Win Rate</div>
                <div class="stat-value">{win_rate:.0f}%</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Bets</div>
                <div class="stat-value">{bets_won}/{total_bets}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">ROI</div>
                <div class="stat-value">{roi:+.0f}%</div>
            </div>
        </div>
        <div class="card-bets">
            {bets_html}
        </div>
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)
