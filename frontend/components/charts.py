"""Charts component - dual system profit visualizations."""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
from collections import defaultdict
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import settings


def _group_by_week_dual(predictions: list[dict]) -> tuple[dict, dict]:
    """Group predictions by week and calculate profit for both systems.

    Args:
        predictions: List of predictions with analysis

    Returns:
        Tuple of (ai_weekly_profit, ev_weekly_profit) dicts
    """
    ai_weekly_profit = defaultdict(float)
    ev_weekly_profit = defaultdict(float)

    for pred in predictions:
        analysis = pred.get('analysis')
        if not analysis:
            continue

        game_date = pred.get('date') or pred.get('game_date')
        if not game_date:
            continue

        try:
            dt = datetime.strptime(game_date, "%Y-%m-%d")
            week_num = dt.isocalendar()[1]
            week_key = f"Week {week_num}"

            # AI system profit
            if analysis.get('ai_system'):
                ai_profit = analysis['ai_system']['summary'].get('total_profit', 0)
                ai_weekly_profit[week_key] += ai_profit
            # Handle old format (backward compatibility)
            elif 'summary' in analysis and 'ai_system' not in analysis:
                ai_profit = analysis['summary'].get('total_profit', 0)
                ai_weekly_profit[week_key] += ai_profit

            # EV system profit
            if analysis.get('ev_system'):
                ev_profit = analysis['ev_system']['summary'].get('total_profit', 0)
                ev_weekly_profit[week_key] += ev_profit

        except (ValueError, KeyError):
            continue

    return dict(ai_weekly_profit), dict(ev_weekly_profit)


def _group_by_month_dual(predictions: list[dict]) -> tuple[dict, dict]:
    """Group predictions by month and calculate profit for both systems.

    Args:
        predictions: List of predictions with analysis

    Returns:
        Tuple of (ai_monthly_profit, ev_monthly_profit) dicts
    """
    ai_monthly_profit = defaultdict(float)
    ev_monthly_profit = defaultdict(float)

    for pred in predictions:
        analysis = pred.get('analysis')
        if not analysis:
            continue

        game_date = pred.get('date') or pred.get('game_date')
        if not game_date:
            continue

        try:
            dt = datetime.strptime(game_date, "%Y-%m-%d")
            month_key = dt.strftime("%b %Y")

            # AI system profit
            if analysis.get('ai_system'):
                ai_profit = analysis['ai_system']['summary'].get('total_profit', 0)
                ai_monthly_profit[month_key] += ai_profit
            # Handle old format (backward compatibility)
            elif 'summary' in analysis and 'ai_system' not in analysis:
                ai_profit = analysis['summary'].get('total_profit', 0)
                ai_monthly_profit[month_key] += ai_profit

            # EV system profit
            if analysis.get('ev_system'):
                ev_profit = analysis['ev_system']['summary'].get('total_profit', 0)
                ev_monthly_profit[month_key] += ev_profit

        except (ValueError, KeyError):
            continue

    return dict(ai_monthly_profit), dict(ev_monthly_profit)


def _group_roi_by_week_dual(predictions: list[dict]) -> tuple[dict, dict]:
    """Group predictions by week and calculate ROI for both systems.

    Args:
        predictions: List of predictions with analysis

    Returns:
        Tuple of (ai_weekly_roi, ev_weekly_roi) dicts
    """
    ai_weekly_roi = defaultdict(list)
    ev_weekly_roi = defaultdict(list)

    for pred in predictions:
        analysis = pred.get('analysis')
        if not analysis:
            continue

        game_date = pred.get('date') or pred.get('game_date')
        if not game_date:
            continue

        try:
            dt = datetime.strptime(game_date, "%Y-%m-%d")
            week_num = dt.isocalendar()[1]
            week_key = f"Week {week_num}"

            # AI system ROI
            if analysis.get('ai_system'):
                ai_roi = analysis['ai_system']['summary'].get('roi_percent', 0)
                ai_weekly_roi[week_key].append(ai_roi)
            # Handle old format (backward compatibility)
            elif 'summary' in analysis and 'ai_system' not in analysis:
                ai_roi = analysis['summary'].get('roi_percent', 0)
                ai_weekly_roi[week_key].append(ai_roi)

            # EV system ROI
            if analysis.get('ev_system'):
                ev_roi = analysis['ev_system']['summary'].get('roi_percent', 0)
                ev_weekly_roi[week_key].append(ev_roi)

        except (ValueError, KeyError):
            continue

    # Average ROI per week
    ai_avg_roi = {week: sum(rois) / len(rois) for week, rois in ai_weekly_roi.items()}
    ev_avg_roi = {week: sum(rois) / len(rois) for week, rois in ev_weekly_roi.items()}

    return ai_avg_roi, ev_avg_roi


def render_profit_charts(predictions: list[dict]):
    """Render dual-system comparison charts.

    Args:
        predictions: List of all predictions with analysis
    """
    st.markdown("### Performance Charts - System Comparison")

    # Filter only analyzed predictions
    analyzed = [p for p in predictions if p.get('analysis')]

    if not analyzed:
        st.info("No analyzed predictions yet. Charts will appear once results are fetched.")
        return

    # Create three columns for charts
    col1, col2, col3 = st.columns(3)

    # Weekly profit comparison (AI vs EV)
    with col1:
        ai_weekly, ev_weekly = _group_by_week_dual(analyzed)

        if ai_weekly or ev_weekly:
            # Get all unique weeks
            all_weeks = sorted(set(list(ai_weekly.keys()) + list(ev_weekly.keys())),
                             key=lambda x: int(x.split()[1]))

            ai_profits = [ai_weekly.get(w, 0) for w in all_weeks]
            ev_profits = [ev_weekly.get(w, 0) for w in all_weeks]

            fig_week = go.Figure()

            # AI system line
            if ai_weekly:
                fig_week.add_trace(go.Scatter(
                    x=all_weeks,
                    y=ai_profits,
                    mode='lines+markers',
                    name='AI System',
                    line=dict(color='#667eea', width=3, shape='spline'),
                    marker=dict(size=8, line=dict(color='white', width=2)),
                    hovertemplate='<b>AI - %{x}</b><br>Profit: $%{y:+.2f}<extra></extra>'
                ))

            # EV system line
            if ev_weekly:
                fig_week.add_trace(go.Scatter(
                    x=all_weeks,
                    y=ev_profits,
                    mode='lines+markers',
                    name='EV System',
                    line=dict(color='#f093fb', width=3, shape='spline'),
                    marker=dict(size=8, line=dict(color='white', width=2)),
                    hovertemplate='<b>EV - %{x}</b><br>Profit: $%{y:+.2f}<extra></extra>'
                ))

            fig_week.update_layout(
                title="Weekly Profit Comparison",
                xaxis=dict(gridcolor='rgba(255,255,255,0.05)', color='white', showline=False),
                yaxis=dict(
                    title="Profit ($)",
                    gridcolor='rgba(255,255,255,0.05)',
                    color='white',
                    zeroline=True,
                    zerolinecolor='rgba(255,255,255,0.2)',
                    zerolinewidth=1
                ),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inconsolata', color='white', size=10),
                height=280,
                margin=dict(l=40, r=10, t=40, b=30),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    bgcolor='rgba(0,0,0,0)',
                    font=dict(size=9)
                )
            )

            st.plotly_chart(fig_week, use_container_width=True)

    # Monthly profit comparison
    with col2:
        ai_monthly, ev_monthly = _group_by_month_dual(analyzed)

        if ai_monthly or ev_monthly:
            all_months = sorted(set(list(ai_monthly.keys()) + list(ev_monthly.keys())),
                              key=lambda x: datetime.strptime(x, "%b %Y"))

            ai_profits = [ai_monthly.get(m, 0) for m in all_months]
            ev_profits = [ev_monthly.get(m, 0) for m in all_months]

            fig_month = go.Figure()

            # AI system line
            if ai_monthly:
                fig_month.add_trace(go.Scatter(
                    x=all_months,
                    y=ai_profits,
                    mode='lines+markers',
                    name='AI System',
                    line=dict(color='#667eea', width=3, shape='spline'),
                    marker=dict(size=8, line=dict(color='white', width=2)),
                    hovertemplate='<b>AI - %{x}</b><br>Profit: $%{y:+.2f}<extra></extra>'
                ))

            # EV system line
            if ev_monthly:
                fig_month.add_trace(go.Scatter(
                    x=all_months,
                    y=ev_profits,
                    mode='lines+markers',
                    name='EV System',
                    line=dict(color='#f093fb', width=3, shape='spline'),
                    marker=dict(size=8, line=dict(color='white', width=2)),
                    hovertemplate='<b>EV - %{x}</b><br>Profit: $%{y:+.2f}<extra></extra>'
                ))

            fig_month.update_layout(
                title="Monthly Profit Comparison",
                xaxis=dict(gridcolor='rgba(255,255,255,0.05)', color='white', showline=False),
                yaxis=dict(
                    title="Profit ($)",
                    gridcolor='rgba(255,255,255,0.05)',
                    color='white',
                    zeroline=True,
                    zerolinecolor='rgba(255,255,255,0.2)',
                    zerolinewidth=1
                ),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inconsolata', color='white', size=10),
                height=280,
                margin=dict(l=40, r=10, t=40, b=30),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    bgcolor='rgba(0,0,0,0)',
                    font=dict(size=9)
                )
            )

            st.plotly_chart(fig_month, use_container_width=True)

    # ROI comparison
    with col3:
        ai_roi, ev_roi = _group_roi_by_week_dual(analyzed)

        if ai_roi or ev_roi:
            all_weeks = sorted(set(list(ai_roi.keys()) + list(ev_roi.keys())),
                             key=lambda x: int(x.split()[1]))

            ai_roi_values = [ai_roi.get(w, 0) for w in all_weeks]
            ev_roi_values = [ev_roi.get(w, 0) for w in all_weeks]

            fig_roi = go.Figure()

            # AI system line
            if ai_roi:
                fig_roi.add_trace(go.Scatter(
                    x=all_weeks,
                    y=ai_roi_values,
                    mode='lines+markers',
                    name='AI System',
                    line=dict(color='#667eea', width=3, shape='spline'),
                    marker=dict(size=8, line=dict(color='white', width=2)),
                    hovertemplate='<b>AI - %{x}</b><br>ROI: %{y:+.1f}%<extra></extra>'
                ))

            # EV system line
            if ev_roi:
                fig_roi.add_trace(go.Scatter(
                    x=all_weeks,
                    y=ev_roi_values,
                    mode='lines+markers',
                    name='EV System',
                    line=dict(color='#f093fb', width=3, shape='spline'),
                    marker=dict(size=8, line=dict(color='white', width=2)),
                    hovertemplate='<b>EV - %{x}</b><br>ROI: %{y:+.1f}%<extra></extra>'
                ))

            fig_roi.update_layout(
                title="Weekly ROI Comparison",
                xaxis=dict(gridcolor='rgba(255,255,255,0.05)', color='white', showline=False),
                yaxis=dict(
                    title="ROI (%)",
                    gridcolor='rgba(255,255,255,0.05)',
                    color='white',
                    zeroline=True,
                    zerolinecolor='rgba(255,255,255,0.2)',
                    zerolinewidth=1
                ),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inconsolata', color='white', size=10),
                height=280,
                margin=dict(l=40, r=10, t=40, b=30),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    bgcolor='rgba(0,0,0,0)',
                    font=dict(size=9)
                )
            )

            st.plotly_chart(fig_roi, use_container_width=True)

    st.divider()
