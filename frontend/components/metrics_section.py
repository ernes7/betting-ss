"""Metrics section component - displays AI + EV dual system performance metrics."""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.colors import get_profit_color, get_win_rate_color
from theme import AI_GRADIENT_BG, AI_BORDER_COLOR, EV_GRADIENT_BG, EV_BORDER_COLOR

# Add project root to path for sports imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from sports.nfl.constants import FIXED_BET_AMOUNT


def _calculate_system_metrics(predictions: list[dict], system_key: str) -> dict:
    """Calculate metrics for a specific system (ai_system or ev_system).

    Args:
        predictions: List of predictions with analysis data
        system_key: 'ai_system' or 'ev_system'

    Returns:
        Dictionary with calculated metrics
    """
    preds_with_system = []
    for p in predictions:
        analysis = p.get('analysis')
        if not analysis:
            continue

        # Handle new dual-system format
        if analysis.get(system_key):
            preds_with_system.append(p)
        # Handle old single-system format (backward compatibility)
        elif system_key == 'ai_system' and 'summary' in analysis and 'ai_system' not in analysis:
            # Old format - treat entire analysis as AI system
            preds_with_system.append(p)

    if not preds_with_system:
        return {
            'total_profit': 0,
            'total_bets': 0,
            'total_bets_won': 0,
            'win_rate': 0,
            'roi': 0,
            'total_risk': 0,
            'games_analyzed': 0
        }

    total_profit = 0
    total_bets = 0
    total_bets_won = 0

    for p in preds_with_system:
        analysis = p['analysis']

        # New format - get from specific system
        if analysis.get(system_key):
            summary = analysis[system_key]['summary']
        # Old format - get from root level
        else:
            summary = analysis.get('summary', {})

        total_profit += summary.get('total_profit', 0)
        total_bets += summary.get('total_bets', 0)
        total_bets_won += summary.get('bets_won', 0)

    win_rate = (total_bets_won / total_bets * 100) if total_bets > 0 else 0
    total_risk = total_bets * FIXED_BET_AMOUNT if total_bets > 0 else 1
    roi = (total_profit / total_risk * 100) if total_risk > 0 else 0

    return {
        'total_profit': total_profit,
        'total_bets': total_bets,
        'total_bets_won': total_bets_won,
        'win_rate': win_rate,
        'roi': roi,
        'total_risk': total_risk,
        'games_analyzed': len(preds_with_system)
    }


def render_metrics(predictions: list[dict]):
    """Render dual system performance metrics in side-by-side layout.

    Args:
        predictions: List of predictions with analysis data merged
    """
    # Calculate metrics for both systems
    ai_metrics = _calculate_system_metrics(predictions, 'ai_system')
    ev_metrics = _calculate_system_metrics(predictions, 'ev_system')

    # Render dual system metrics
    st.markdown("### Dual System Performance")

    # AI System Metrics
    st.markdown(f'<div style="margin-top: 20px; padding: 15px; background: {AI_GRADIENT_BG}; border-radius: 10px; border-left: 3px solid {AI_BORDER_COLOR};">', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size: 1.1rem; font-weight: 600; color: {AI_BORDER_COLOR}; margin-bottom: 10px;">🤖 AI Predictor System</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        profit_color = get_profit_color(ai_metrics['total_profit'])
        st.markdown(f"""
            <div style='text-align: center;'>
                <div style='font-size: 0.9rem; color: rgba(255,255,255,0.8);'>Total Profit/Loss</div>
                <div style='font-size: 2rem; font-weight: 700; color: {profit_color};'>${ai_metrics['total_profit']:+.2f}</div>
                <div style='font-size: 0.75rem; color: rgba(255,255,255,0.6);'>Fixed ${FIXED_BET_AMOUNT} per bet</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.metric(
            "Total Bets",
            ai_metrics['total_bets'],
            delta=f"{ai_metrics['games_analyzed']} games"
        )

    with col3:
        win_color = get_win_rate_color(ai_metrics['win_rate'])
        st.markdown(f"""
            <div style='text-align: center;'>
                <div style='font-size: 0.9rem; color: rgba(255,255,255,0.8);'>Win Rate</div>
                <div style='font-size: 1.8rem; font-weight: 700; color: {win_color};'>{ai_metrics['win_rate']:.1f}%</div>
                <div style='font-size: 0.75rem; color: rgba(255,255,255,0.6);'>{ai_metrics['total_bets_won']}/{ai_metrics['total_bets']} bets</div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        roi_color = get_profit_color(ai_metrics['roi'])
        st.markdown(f"""
            <div style='text-align: center;'>
                <div style='font-size: 0.9rem; color: rgba(255,255,255,0.8);'>ROI</div>
                <div style='font-size: 1.8rem; font-weight: 700; color: {roi_color};'>{ai_metrics['roi']:+.1f}%</div>
                <div style='font-size: 0.75rem; color: rgba(255,255,255,0.6);'>${ai_metrics['total_profit']:+.2f} / ${ai_metrics['total_risk']:.0f}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # EV System Metrics
    st.markdown(f'<div style="margin-top: 15px; padding: 15px; background: {EV_GRADIENT_BG}; border-radius: 10px; border-left: 3px solid {EV_BORDER_COLOR};">', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size: 1.1rem; font-weight: 600; color: {EV_BORDER_COLOR}; margin-bottom: 10px;">📊 EV Calculator System</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        profit_color = get_profit_color(ev_metrics['total_profit'])
        st.markdown(f"""
            <div style='text-align: center;'>
                <div style='font-size: 0.9rem; color: rgba(255,255,255,0.8);'>Total Profit/Loss</div>
                <div style='font-size: 2rem; font-weight: 700; color: {profit_color};'>${ev_metrics['total_profit']:+.2f}</div>
                <div style='font-size: 0.75rem; color: rgba(255,255,255,0.6);'>Fixed ${FIXED_BET_AMOUNT} per bet</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.metric(
            "Total Bets",
            ev_metrics['total_bets'],
            delta=f"{ev_metrics['games_analyzed']} games"
        )

    with col3:
        win_color = get_win_rate_color(ev_metrics['win_rate'])
        st.markdown(f"""
            <div style='text-align: center;'>
                <div style='font-size: 0.9rem; color: rgba(255,255,255,0.8);'>Win Rate</div>
                <div style='font-size: 1.8rem; font-weight: 700; color: {win_color};'>{ev_metrics['win_rate']:.1f}%</div>
                <div style='font-size: 0.75rem; color: rgba(255,255,255,0.6);'>{ev_metrics['total_bets_won']}/{ev_metrics['total_bets']} bets</div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        roi_color = get_profit_color(ev_metrics['roi'])
        st.markdown(f"""
            <div style='text-align: center;'>
                <div style='font-size: 0.9rem; color: rgba(255,255,255,0.8);'>ROI</div>
                <div style='font-size: 1.8rem; font-weight: 700; color: {roi_color};'>{ev_metrics['roi']:+.1f}%</div>
                <div style='font-size: 0.75rem; color: rgba(255,255,255,0.6);'>${ev_metrics['total_profit']:+.2f} / ${ev_metrics['total_risk']:.0f}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
