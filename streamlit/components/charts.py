"""Charts component - profit visualizations by week and month."""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
from collections import defaultdict
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from nfl.constants import FIXED_BET_AMOUNT


def _group_by_week(predictions: list[dict]) -> dict:
    """Group predictions by week and calculate profit.

    Args:
        predictions: List of predictions with analysis

    Returns:
        Dict mapping week string to profit amount
    """
    weekly_profit = defaultdict(float)

    for pred in predictions:
        analysis = pred.get('analysis')
        if not analysis:
            continue

        game_date = pred.get('date') or pred.get('game_date')
        if not game_date:
            continue

        try:
            dt = datetime.strptime(game_date, "%Y-%m-%d")
            # Get week number
            week_num = dt.isocalendar()[1]
            week_key = f"Week {week_num}"

            profit = analysis['summary'].get('total_profit', 0)
            weekly_profit[week_key] += profit
        except (ValueError, KeyError):
            continue

    return dict(weekly_profit)


def _group_by_month(predictions: list[dict]) -> dict:
    """Group predictions by month and calculate profit.

    Args:
        predictions: List of predictions with analysis

    Returns:
        Dict mapping month string to profit amount
    """
    monthly_profit = defaultdict(float)

    for pred in predictions:
        analysis = pred.get('analysis')
        if not analysis:
            continue

        game_date = pred.get('date') or pred.get('game_date')
        if not game_date:
            continue

        try:
            dt = datetime.strptime(game_date, "%Y-%m-%d")
            month_key = dt.strftime("%b %Y")  # e.g., "Nov 2025"

            profit = analysis['summary'].get('total_profit', 0)
            monthly_profit[month_key] += profit
        except (ValueError, KeyError):
            continue

    return dict(monthly_profit)


def _group_roi_by_week(predictions: list[dict]) -> dict:
    """Group predictions by week and calculate ROI.

    Args:
        predictions: List of predictions with analysis

    Returns:
        Dict mapping week string to ROI percentage
    """
    weekly_roi = defaultdict(list)

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

            roi = analysis['summary'].get('roi_percent', 0)
            weekly_roi[week_key].append(roi)
        except (ValueError, KeyError):
            continue

    # Average ROI per week
    return {week: sum(rois) / len(rois) for week, rois in weekly_roi.items()}


def render_profit_charts(predictions: list[dict]):
    """Render profit and ROI line charts.

    Args:
        predictions: List of all predictions with analysis
    """
    st.markdown("### Performance Charts")

    # Filter only analyzed predictions
    analyzed = [p for p in predictions if p.get('analysis')]

    if not analyzed:
        st.info("No analyzed predictions yet. Charts will appear once results are fetched.")
        return

    # Create three columns for charts
    col1, col2, col3 = st.columns(3)

    # Weekly profit chart (smooth line)
    with col1:
        weekly_data = _group_by_week(analyzed)

        if weekly_data:
            sorted_weeks = sorted(weekly_data.items(), key=lambda x: int(x[0].split()[1]))
            weeks = [w[0] for w in sorted_weeks]
            profits = [w[1] for w in sorted_weeks]

            fig_week = go.Figure(data=[
                go.Scatter(
                    x=weeks,
                    y=profits,
                    mode='lines+markers',
                    line=dict(
                        color='#5F4BB6',
                        width=3,
                        shape='spline'  # Smooth curvy line
                    ),
                    marker=dict(
                        size=8,
                        color=profits,
                        colorscale=[[0, '#f45c43'], [0.5, '#86A5D9'], [1, '#38ef7d']],
                        line=dict(color='white', width=2)
                    ),
                    fill='tozeroy',
                    fillcolor='rgba(95, 75, 182, 0.1)',
                    hovertemplate='<b>%{x}</b><br>Profit: $%{y:+.2f}<extra></extra>'
                )
            ])

            fig_week.update_layout(
                title="Weekly Profit",
                xaxis=dict(
                    gridcolor='rgba(255,255,255,0.05)',
                    color='white',
                    showline=False
                ),
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
                showlegend=False
            )

            st.plotly_chart(fig_week, use_container_width=True)

    # Monthly profit chart (smooth line)
    with col2:
        monthly_data = _group_by_month(analyzed)

        if monthly_data:
            sorted_months = sorted(monthly_data.items(), key=lambda x: datetime.strptime(x[0], "%b %Y"))
            months = [m[0] for m in sorted_months]
            profits = [m[1] for m in sorted_months]

            fig_month = go.Figure(data=[
                go.Scatter(
                    x=months,
                    y=profits,
                    mode='lines+markers',
                    line=dict(
                        color='#86A5D9',
                        width=3,
                        shape='spline'
                    ),
                    marker=dict(
                        size=8,
                        color=profits,
                        colorscale=[[0, '#f45c43'], [0.5, '#86A5D9'], [1, '#38ef7d']],
                        line=dict(color='white', width=2)
                    ),
                    fill='tozeroy',
                    fillcolor='rgba(134, 165, 217, 0.1)',
                    hovertemplate='<b>%{x}</b><br>Profit: $%{y:+.2f}<extra></extra>'
                )
            ])

            fig_month.update_layout(
                title="Monthly Profit",
                xaxis=dict(
                    gridcolor='rgba(255,255,255,0.05)',
                    color='white',
                    showline=False
                ),
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
                showlegend=False
            )

            st.plotly_chart(fig_month, use_container_width=True)

    # ROI chart (smooth line)
    with col3:
        roi_data = _group_roi_by_week(analyzed)

        if roi_data:
            sorted_roi = sorted(roi_data.items(), key=lambda x: int(x[0].split()[1]))
            weeks = [w[0] for w in sorted_roi]
            roi_values = [w[1] for w in sorted_roi]

            fig_roi = go.Figure(data=[
                go.Scatter(
                    x=weeks,
                    y=roi_values,
                    mode='lines+markers',
                    line=dict(
                        color='#38ef7d',
                        width=3,
                        shape='spline'
                    ),
                    marker=dict(
                        size=8,
                        color=roi_values,
                        colorscale=[[0, '#f45c43'], [0.5, '#86A5D9'], [1, '#38ef7d']],
                        line=dict(color='white', width=2)
                    ),
                    fill='tozeroy',
                    fillcolor='rgba(56, 239, 125, 0.1)',
                    hovertemplate='<b>%{x}</b><br>ROI: %{y:+.1f}%<extra></extra>'
                )
            ])

            fig_roi.update_layout(
                title="Weekly ROI",
                xaxis=dict(
                    gridcolor='rgba(255,255,255,0.05)',
                    color='white',
                    showline=False
                ),
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
                showlegend=False
            )

            st.plotly_chart(fig_roi, use_container_width=True)

    st.divider()
