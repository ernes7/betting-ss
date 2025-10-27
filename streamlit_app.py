"""Modern Sports Betting Analytics Dashboard with Glassmorphism Design."""

import json
import streamlit as st
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
from collections import defaultdict


def format_date(date_str: str) -> str:
    """Convert '2025-10-26' to 'Oct-26' format.

    Args:
        date_str: Date string in YYYY-MM-DD format

    Returns:
        Formatted date string like 'Oct-26'
    """
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%b-%d")
    except Exception:
        return date_str

# Page configuration
st.set_page_config(
    page_title="Sports Betting Analytics",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Glassmorphism CSS
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global Styles */
    * {
        font-family: 'Inter', sans-serif;
    }

    /* Main Background Gradient */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }

    /* Glass Card */
    .glass-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.18);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        padding: 20px;
        margin: 10px 0;
    }

    /* Metric Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
    }

    /* Hit/Miss Badges */
    .badge-hit {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
        box-shadow: 0 4px 12px rgba(17, 153, 142, 0.4);
    }

    .badge-miss {
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
        box-shadow: 0 4px 12px rgba(235, 51, 73, 0.4);
    }

    .badge-pending {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
    }

    /* Prediction Card */
    .prediction-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(15px);
        border-radius: 20px;
        padding: 25px;
        margin: 15px 0;
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
    }

    .prediction-card-hit {
        border-left: 5px solid #38ef7d;
    }

    .prediction-card-miss {
        border-left: 5px solid #f45c43;
    }

    .prediction-card-pending {
        border-left: 5px solid #667eea;
    }

    /* Custom metric styling */
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: white;
    }

    div[data-testid="stMetricLabel"] {
        color: rgba(255, 255, 255, 0.8);
        font-size: 0.9rem;
        font-weight: 500;
    }

    /* Headers */
    h1, h2, h3 {
        color: white !important;
        font-weight: 700 !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        color: white !important;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


def load_all_predictions() -> list[dict]:
    """Load all prediction JSON files from NFL and NBA data directories.

    Returns:
        List of prediction dictionaries with file paths
    """
    predictions = []
    base_dir = Path(__file__).parent

    # Scan NFL predictions
    nfl_dir = base_dir / "nfl" / "data" / "predictions"
    if nfl_dir.exists():
        for json_file in nfl_dir.rglob("*.json"):
            if json_file.name == ".metadata.json":
                continue
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['file_path'] = str(json_file)
                    # Extract game key from path
                    data['game_key'] = json_file.stem
                    data['game_date'] = json_file.parent.name
                    predictions.append(data)
            except Exception as e:
                st.error(f"Error loading {json_file}: {e}")

    # Scan NBA predictions
    nba_dir = base_dir / "nba" / "data" / "predictions"
    if nba_dir.exists():
        for json_file in nba_dir.rglob("*.json"):
            if json_file.name == ".metadata.json":
                continue
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['file_path'] = str(json_file)
                    data['game_key'] = json_file.stem
                    data['game_date'] = json_file.parent.name
                    predictions.append(data)
            except Exception as e:
                st.error(f"Error loading {json_file}: {e}")

    return predictions


def load_all_analyses() -> dict:
    """Load all analysis JSON files and create lookup by game key.

    Returns:
        Dictionary mapping game_key to analysis data
    """
    analyses = {}
    base_dir = Path(__file__).parent

    # Scan NFL analyses
    nfl_dir = base_dir / "nfl" / "data" / "analysis"
    if nfl_dir.exists():
        for json_file in nfl_dir.rglob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    game_key = json_file.stem
                    analyses[game_key] = data
            except Exception as e:
                pass  # Silently skip errors

    # Scan NBA analyses
    nba_dir = base_dir / "nba" / "data" / "analysis"
    if nba_dir.exists():
        for json_file in nba_dir.rglob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    game_key = json_file.stem
                    analyses[game_key] = data
            except Exception as e:
                pass  # Silently skip errors

    return analyses


def merge_predictions_with_analyses(predictions: list[dict], analyses: dict) -> list[dict]:
    """Merge prediction data with analysis results.

    Args:
        predictions: List of prediction dictionaries
        analyses: Dictionary of analyses by game_key

    Returns:
        List of predictions with analysis data merged
    """
    for pred in predictions:
        game_key = pred.get('game_key')
        if game_key in analyses:
            pred['analysis'] = analyses[game_key]
        else:
            pred['analysis'] = None
    return predictions


def calculate_daily_metrics(predictions: list[dict]) -> dict:
    """Calculate parlay hit rate and stats per day.

    Args:
        predictions: List of predictions with analysis data

    Returns:
        Dictionary with date -> metrics mapping
    """
    daily_data = defaultdict(lambda: {
        'parlays_total': 0,
        'parlays_hit': 0,
        'legs_total': 0,
        'legs_hit': 0,
        'games': 0
    })

    for pred in predictions:
        analysis = pred.get('analysis')
        if not analysis:
            continue

        date = pred.get('game_date', 'unknown')
        summary = analysis.get('summary', {})

        daily_data[date]['games'] += 1
        daily_data[date]['parlays_total'] += summary.get('parlays_total', 0)
        daily_data[date]['parlays_hit'] += summary.get('parlays_hit', 0)
        daily_data[date]['legs_total'] += summary.get('total_legs', 0)
        daily_data[date]['legs_hit'] += summary.get('legs_hit', 0)

    # Calculate hit rates
    for date, data in daily_data.items():
        if data['parlays_total'] > 0:
            data['parlay_hit_rate'] = (data['parlays_hit'] / data['parlays_total']) * 100
        else:
            data['parlay_hit_rate'] = 0

        if data['legs_total'] > 0:
            data['leg_hit_rate'] = (data['legs_hit'] / data['legs_total']) * 100
        else:
            data['leg_hit_rate'] = 0

    return dict(daily_data)


def create_daily_performance_chart(daily_metrics: dict) -> go.Figure:
    """Create horizontal bar chart showing daily parlay hit rates with 25% benchmark.

    Args:
        daily_metrics: Dictionary with daily performance data

    Returns:
        Plotly figure object
    """
    if not daily_metrics:
        # Empty chart
        fig = go.Figure()
        fig.add_annotation(
            text="No analyzed games yet",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="white")
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=300
        )
        return fig

    # Sort by date
    dates = sorted(daily_metrics.keys(), reverse=True)
    formatted_dates = [format_date(d) for d in dates]
    hit_rates = [daily_metrics[d]['parlay_hit_rate'] for d in dates]
    parlays_hit = [daily_metrics[d]['parlays_hit'] for d in dates]
    parlays_total = [daily_metrics[d]['parlays_total'] for d in dates]

    # Color bars: green if >= 25%, red if < 25%
    colors = ['#38ef7d' if rate >= 25 else '#f45c43' for rate in hit_rates]

    fig = go.Figure()

    # Add bars
    fig.add_trace(go.Bar(
        y=formatted_dates,
        x=hit_rates,
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(color='rgba(255,255,255,0.3)', width=2)
        ),
        text=[f"{rate:.1f}%" for rate in hit_rates],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>' +
                      'Hit Rate: %{x:.1f}%<br>' +
                      'Parlays: %{customdata[0]}/%{customdata[1]}<br>' +
                      '<extra></extra>',
        customdata=list(zip(parlays_hit, parlays_total))
    ))

    # Add 25% benchmark line
    fig.add_vline(
        x=25,
        line=dict(color='#ffd700', width=3, dash='dash'),
        annotation=dict(
            text="25% Target",
            font=dict(size=12, color='#ffd700'),
            yanchor='top'
        )
    )

    fig.update_layout(
        title=dict(
            text="Daily Parlay Performance",
            font=dict(size=24, color='white', family='Inter'),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title="Parlay Hit Rate (%)",
            gridcolor='rgba(255,255,255,0.1)',
            color='white',
            range=[0, max(100, max(hit_rates) + 10) if hit_rates else 100]
        ),
        yaxis=dict(
            title="Date",
            gridcolor='rgba(255,255,255,0.1)',
            color='white'
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=max(400, len(formatted_dates) * 50),
        font=dict(family='Inter', color='white'),
        showlegend=False,
        margin=dict(l=100, r=100, t=80, b=60)
    )

    return fig


def render_analysis_summary(analysis: dict):
    """Render analysis results summary."""
    if not analysis:
        return

    summary = analysis.get('summary', {})

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        parlays_hit = summary.get('parlays_hit', 0)
        parlays_total = summary.get('parlays_total', 0)
        st.metric("Parlays Hit", f"{parlays_hit}/{parlays_total}")

    with col2:
        hit_rate = summary.get('parlay_hit_rate', 0)
        st.metric("Parlay Hit Rate", f"{hit_rate:.1f}%")

    with col3:
        legs_hit = summary.get('legs_hit', 0)
        total_legs = summary.get('total_legs', 0)
        st.metric("Legs Hit", f"{legs_hit}/{total_legs}")

    with col4:
        leg_rate = summary.get('legs_hit_rate', 0)
        st.metric("Leg Hit Rate", f"{leg_rate:.1f}%")

    # Show insights
    insights = analysis.get('insights', [])
    if insights:
        st.markdown("**🎯 Key Insights:**")
        for insight in insights:
            st.markdown(f"- {insight}")


def render_parlay_with_analysis(parlay: dict, parlay_result: dict = None, index: int = 0):
    """Render a single parlay with analysis results if available."""
    confidence = parlay.get("confidence", 0)
    name = parlay.get("name", "Unknown Parlay")

    # Determine status
    if parlay_result:
        hit = parlay_result.get('hit', False)
        status_badge = '<span class="badge-hit">✅ HIT</span>' if hit else '<span class="badge-miss">❌ MISS</span>'
        legs_hit = parlay_result.get('legs_hit', 0)
        legs_total = parlay_result.get('legs_total', 0)
    else:
        status_badge = '<span class="badge-pending">⏳ PENDING</span>'
        legs_hit = legs_total = None

    # Header
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        st.markdown(f"**{name}**")

    with col2:
        color = "#38ef7d" if confidence >= 90 else "#667eea" if confidence >= 80 else "#f45c43"
        st.markdown(f'<span style="color: {color}; font-weight: 600;">{confidence}% Confidence</span>', unsafe_allow_html=True)

    with col3:
        st.markdown(status_badge, unsafe_allow_html=True)

    # Show legs hit if available
    if legs_hit is not None:
        st.markdown(f"**Legs: {legs_hit}/{legs_total}** ({(legs_hit/legs_total*100) if legs_total else 0:.0f}%)")

    # Bets with results
    st.markdown("**Bets:**")

    if parlay_result and parlay_result.get('legs'):
        # Show detailed leg analysis
        for i, leg in enumerate(parlay_result['legs'], 1):
            bet_text = leg.get('bet', '')
            hit = leg.get('hit', False)
            actual = leg.get('actual_value', '')
            margin = leg.get('margin')

            icon = "✅" if hit else "❌"
            st.markdown(f"{i}. {icon} **{bet_text}**")
            st.markdown(f"   *Actual: {actual}*")
            if margin is not None:
                margin_pct = leg.get('margin_pct')
                if margin_pct is not None:
                    st.markdown(f"   *Margin: {margin:+.1f} ({margin_pct:+.1f}%)*")
                else:
                    st.markdown(f"   *Margin: {margin:+.1f}*")
    else:
        # Just show bets
        for i, bet in enumerate(parlay.get("bets", []), 1):
            st.markdown(f"{i}. {bet}")

    # Reasoning
    st.markdown("**Reasoning:**")
    if parlay_result and parlay_result.get('parlay_reasoning'):
        st.markdown(parlay_result['parlay_reasoning'])
    else:
        st.markdown(parlay.get("reasoning", "No reasoning provided"))

    st.divider()


def render_prediction_card(prediction: dict, index: int):
    """Render modern prediction card with glassmorphism and analysis integration."""
    # Extract data
    teams = prediction.get("teams", ["Unknown", "Unknown"])
    home_team = prediction.get("home_team", "Unknown")
    sport = prediction.get("sport", "unknown").upper()
    date = prediction.get("date", prediction.get("game_date", "Unknown"))
    analysis = prediction.get("analysis")

    # Sport emoji
    sport_emoji = "🏈" if sport == "NFL" else "🏀" if sport == "NBA" else "🎯"

    # Determine card status class
    if analysis:
        summary = analysis.get('summary', {})
        hit_rate = summary.get('parlay_hit_rate', 0)
        card_class = "prediction-card-hit" if hit_rate > 0 else "prediction-card-miss"
    else:
        card_class = "prediction-card-pending"

    # Build matchup string
    matchup = f"{teams[0]} vs {teams[1]}"

    # Expander title
    if analysis:
        summary = analysis.get('summary', {})
        parlays_hit = summary.get('parlays_hit', 0)
        parlays_total = summary.get('parlays_total', 0)
        status_text = f"{'✅' if parlays_hit > 0 else '❌'} {parlays_hit}/{parlays_total} Hit"
    else:
        status_text = "⏳ Pending Analysis"

    formatted_date = format_date(date)
    expander_title = f"{sport_emoji} **{matchup}** | {formatted_date} | {status_text}"

    with st.expander(expander_title, expanded=False):
        # Header metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Home Team", home_team)

        with col2:
            st.metric("Generated", prediction.get("generated_at", "Unknown"))

        with col3:
            api_cost = prediction.get("api_cost", 0)
            st.metric("API Cost", f"${api_cost:.4f}")

        with col4:
            if analysis:
                final_score = analysis.get('final_score', {})
                away_score = final_score.get('away', '?')
                home_score = final_score.get('home', '?')
                st.metric("Final Score", f"{away_score}-{home_score}")

        st.divider()

        # Show analysis summary if available
        if analysis:
            render_analysis_summary(analysis)
            st.divider()

        # Render all parlays with analysis
        parlays = prediction.get("parlays", [])
        parlay_results = analysis.get('parlay_results', []) if analysis else []

        for i, parlay in enumerate(parlays):
            # Match parlay with result by name
            parlay_result = None
            if parlay_results:
                parlay_name = parlay.get('name', '')
                for pr in parlay_results:
                    if pr.get('parlay_name', '').strip() == parlay_name.strip():
                        parlay_result = pr
                        break

            render_parlay_with_analysis(parlay, parlay_result, f"{index}_{i}")


def main():
    """Main Streamlit app."""

    # Hero header
    st.markdown("""
        <div style='text-align: center; padding: 20px 0;'>
            <h1 style='font-size: 3rem; margin: 0;'>🎯 Sports Betting Analytics</h1>
            <p style='font-size: 1.2rem; color: rgba(255,255,255,0.8); margin-top: 10px;'>
                AI-Powered Predictions & Performance Tracking
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Load all data
    predictions = load_all_predictions()
    analyses = load_all_analyses()
    predictions = merge_predictions_with_analyses(predictions, analyses)

    # Sort by date (newest first)
    predictions.sort(key=lambda x: x.get("generated_at", ""), reverse=True)

    # Calculate metrics
    daily_metrics = calculate_daily_metrics(predictions)

    # Calculate overall stats
    analyzed_preds = [p for p in predictions if p.get('analysis')]
    total_parlays = sum([p['analysis']['summary']['parlays_total'] for p in analyzed_preds]) if analyzed_preds else 0
    total_hit = sum([p['analysis']['summary']['parlays_hit'] for p in analyzed_preds]) if analyzed_preds else 0
    total_legs = sum([p['analysis']['summary']['total_legs'] for p in analyzed_preds]) if analyzed_preds else 0
    legs_hit = sum([p['analysis']['summary']['legs_hit'] for p in analyzed_preds]) if analyzed_preds else 0

    overall_hit_rate = (total_hit / total_parlays * 100) if total_parlays > 0 else 0
    leg_hit_rate = (legs_hit / total_legs * 100) if total_legs > 0 else 0

    # Hero metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Predictions",
            len(predictions),
            delta=f"{len(analyzed_preds)} analyzed"
        )

    with col2:
        color = "#38ef7d" if overall_hit_rate >= 25 else "#f45c43"
        st.markdown(f"""
            <div style='text-align: center;'>
                <div style='font-size: 0.9rem; color: rgba(255,255,255,0.8);'>Parlay Hit Rate</div>
                <div style='font-size: 2rem; font-weight: 700; color: {color};'>{overall_hit_rate:.1f}%</div>
                <div style='font-size: 0.8rem; color: rgba(255,255,255,0.6);'>{total_hit}/{total_parlays} parlays</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.metric(
            "Leg Accuracy",
            f"{leg_hit_rate:.1f}%",
            delta=f"{legs_hit}/{total_legs} legs"
        )

    with col4:
        total_cost = sum([p.get('api_cost', 0) for p in predictions])
        st.metric("Total API Cost", f"${total_cost:.2f}")

    st.divider()

    # Daily performance chart
    if daily_metrics:
        st.markdown("### 📊 Daily Performance")
        fig = create_daily_performance_chart(daily_metrics)
        st.plotly_chart(fig, use_container_width=True)
        st.divider()

    # Sidebar filters
    st.sidebar.header("🔍 Filters")

    # Sport filter
    sport_options = ["All", "NFL", "NBA"]
    selected_sport = st.sidebar.selectbox("Sport", sport_options, index=0)

    # Date filter
    unique_dates = sorted(set([p.get("game_date", p.get("date", "")) for p in predictions]), reverse=True)
    # Create formatted date options for display
    date_display_map = {d: format_date(d) for d in unique_dates}
    date_options_display = ["All"] + [date_display_map[d] for d in unique_dates]
    selected_date_display = st.sidebar.selectbox("Date", date_options_display, index=0)
    # Map back to actual date format for filtering
    if selected_date_display == "All":
        selected_date = "All"
    else:
        # Find the original date that matches the selected formatted date
        selected_date = next((d for d, fmt in date_display_map.items() if fmt == selected_date_display), "All")

    # Status filter
    status_options = ["All", "Analyzed", "Pending", "Hit", "Miss"]
    selected_status = st.sidebar.selectbox("Status", status_options, index=0)

    # Reset button
    if st.sidebar.button("Reset Filters"):
        st.rerun()

    # Apply filters
    filtered_predictions = predictions

    if selected_sport != "All":
        filtered_predictions = [
            p for p in filtered_predictions
            if p.get("sport", "").upper() == selected_sport
        ]

    if selected_date != "All":
        filtered_predictions = [
            p for p in filtered_predictions
            if p.get("game_date", p.get("date", "")) == selected_date
        ]

    if selected_status != "All":
        if selected_status == "Analyzed":
            filtered_predictions = [p for p in filtered_predictions if p.get('analysis')]
        elif selected_status == "Pending":
            filtered_predictions = [p for p in filtered_predictions if not p.get('analysis')]
        elif selected_status == "Hit":
            filtered_predictions = [p for p in filtered_predictions if p.get('analysis') and p['analysis']['summary']['parlays_hit'] > 0]
        elif selected_status == "Miss":
            filtered_predictions = [p for p in filtered_predictions if p.get('analysis') and p['analysis']['summary']['parlays_hit'] == 0]

    # Display predictions
    st.markdown(f"### 📋 {len(filtered_predictions)} Prediction{'s' if len(filtered_predictions) != 1 else ''}")

    if not filtered_predictions:
        st.info("No predictions match your filters. Try adjusting the filters above.")
    else:
        for i, prediction in enumerate(filtered_predictions):
            render_prediction_card(prediction, i)

    # Footer
    st.divider()
    st.markdown("""
        <div style='text-align: center; color: rgba(255,255,255,0.6); font-size: 0.9rem; padding: 20px 0;'>
            Built with Claude Code | Powered by Claude Sonnet 4.5 | Modern Glassmorphism Design
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
