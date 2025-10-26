"""Streamlit web interface for Sports Betting Analysis Tool."""

import json
import streamlit as st
from pathlib import Path
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Sports Betting Analysis",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)


def load_all_predictions() -> list[dict]:
    """Load all prediction JSON files from NFL and NBA directories.

    Returns:
        List of prediction dictionaries sorted by generated_at (newest first)
    """
    predictions = []
    base_dir = Path(__file__).parent

    # Scan NFL predictions
    nfl_dir = base_dir / "nfl" / "predictions"
    if nfl_dir.exists():
        for json_file in nfl_dir.rglob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    predictions.append(data)
            except Exception as e:
                st.error(f"Error loading {json_file}: {e}")

    # Scan NBA predictions
    nba_dir = base_dir / "nba" / "predictions"
    if nba_dir.exists():
        for json_file in nba_dir.rglob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    predictions.append(data)
            except Exception as e:
                st.error(f"Error loading {json_file}: {e}")

    # Sort by generated_at (newest first)
    predictions.sort(
        key=lambda x: x.get("generated_at", ""),
        reverse=True
    )

    return predictions


def get_confidence_color(confidence: int) -> str:
    """Get color code based on confidence level.

    Args:
        confidence: Confidence percentage

    Returns:
        Color name for styling
    """
    if confidence >= 90:
        return "green"
    elif confidence >= 80:
        return "blue"
    elif confidence >= 70:
        return "orange"
    else:
        return "red"


def render_parlay_card(parlay: dict, index: int):
    """Render a single parlay within an expander.

    Args:
        parlay: Parlay dictionary with name, confidence, bets, reasoning, odds
        index: Parlay index for unique key
    """
    confidence = parlay.get("confidence", 0)
    color = get_confidence_color(confidence)

    # Use columns for parlay header
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        st.markdown(f"**{parlay.get('name', 'Unknown Parlay')}**")

    with col2:
        st.markdown(f":{color}[**{confidence}%** Confidence]")

    with col3:
        if parlay.get("odds"):
            st.markdown(f"**Odds:** {parlay['odds']}")

    # Bets list
    st.markdown("**Bets:**")
    for i, bet in enumerate(parlay.get("bets", []), 1):
        st.markdown(f"{i}. {bet}")

    # Reasoning
    st.markdown("**Reasoning:**")
    st.markdown(parlay.get("reasoning", "No reasoning provided"))

    st.divider()


def render_prediction_card(prediction: dict, index: int):
    """Render a prediction card with expandable details.

    Args:
        prediction: Prediction dictionary
        index: Card index for unique keys
    """
    # Get teams and matchup info
    teams = prediction.get("teams", ["Unknown", "Unknown"])
    home_team = prediction.get("home_team", "Unknown")
    sport = prediction.get("sport", "unknown").upper()
    date = prediction.get("date", "Unknown")

    # Sport emoji
    sport_emoji = "🏈" if sport == "NFL" else "🏀" if sport == "NBA" else "🎯"

    # Get highest confidence for display
    parlays = prediction.get("parlays", [])
    max_confidence = max([p.get("confidence", 0) for p in parlays], default=0)

    # Build matchup string
    matchup = f"{teams[0]} vs {teams[1]}"

    # Create expander with summary
    expander_title = f"{sport_emoji} **{matchup}** | {date} | Top: {max_confidence}% confidence"

    with st.expander(expander_title, expanded=False):
        # Header info
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Home Team", home_team)

        with col2:
            st.metric("Generated", prediction.get("generated_at", "Unknown"))

        with col3:
            api_cost = prediction.get("api_cost", 0)
            st.metric("API Cost", f"${api_cost:.4f}")

        st.divider()

        # Render all parlays
        for i, parlay in enumerate(parlays):
            render_parlay_card(parlay, f"{index}_{i}")


def main():
    """Main Streamlit app."""

    # Header
    st.title("🎯 Sports Betting Analysis Dashboard")
    st.markdown("AI-powered betting predictions using Claude Sonnet 4.5")

    # Load predictions
    all_predictions = load_all_predictions()

    # Sidebar filters
    st.sidebar.header("🔍 Filters")

    # Sport filter
    sport_options = ["All", "NFL", "NBA"]
    selected_sport = st.sidebar.selectbox("Sport", sport_options, index=0)

    # Date/Week filter
    unique_dates = sorted(set([p.get("date", "") for p in all_predictions]), reverse=True)
    date_options = ["All"] + unique_dates
    selected_date = st.sidebar.selectbox("Date/Week", date_options, index=0)

    # Reset filters button
    if st.sidebar.button("Reset Filters"):
        st.rerun()

    st.sidebar.divider()

    # Generate new prediction button (placeholder)
    st.sidebar.header("➕ Generate Prediction")
    if st.sidebar.button("Generate New Prediction", type="primary"):
        st.sidebar.info("Feature coming soon! Use the CLI for now:\n\n`poetry run python cli.py`")

    # Apply filters
    filtered_predictions = all_predictions

    if selected_sport != "All":
        filtered_predictions = [
            p for p in filtered_predictions
            if p.get("sport", "").upper() == selected_sport
        ]

    if selected_date != "All":
        filtered_predictions = [
            p for p in filtered_predictions
            if p.get("date", "") == selected_date
        ]

    # Summary stats
    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Predictions",
            len(filtered_predictions),
            delta=f"{len(all_predictions)} total" if filtered_predictions != all_predictions else None
        )

    with col2:
        if filtered_predictions:
            avg_confidence = sum([
                max([p.get("confidence", 0) for p in pred.get("parlays", [])], default=0)
                for pred in filtered_predictions
            ]) / len(filtered_predictions)
            st.metric("Avg Top Confidence", f"{avg_confidence:.1f}%")
        else:
            st.metric("Avg Top Confidence", "N/A")

    with col3:
        total_cost = sum([p.get("api_cost", 0) for p in filtered_predictions])
        st.metric("Total API Cost", f"${total_cost:.4f}")

    with col4:
        # Count by sport
        nfl_count = len([p for p in filtered_predictions if p.get("sport") == "nfl"])
        nba_count = len([p for p in filtered_predictions if p.get("sport") == "nba"])
        st.metric("NFL / NBA", f"{nfl_count} / {nba_count}")

    st.divider()

    # Display predictions
    if not filtered_predictions:
        st.info("No predictions found. Try adjusting your filters or generate a new prediction!")
    else:
        st.subheader(f"📊 {len(filtered_predictions)} Prediction{'s' if len(filtered_predictions) != 1 else ''}")

        # Render each prediction card
        for i, prediction in enumerate(filtered_predictions):
            render_prediction_card(prediction, i)

    # Footer
    st.divider()
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray; font-size: 0.9em;'>
        Built with Claude Code | Powered by Claude Sonnet 4.5
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
