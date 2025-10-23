"""NFL Game Prediction Engine

Uses Anthropic Claude API to analyze team data and generate dual parlays.
"""

import json
import os
from pathlib import Path
from typing import Any

import anthropic
from dotenv import load_dotenv

from prompt import build_prediction_prompt

# Load environment variables
load_dotenv()


def load_json_file(filepath: str) -> dict[str, Any] | None:
    """Load a JSON file if it exists."""
    path = Path(filepath)
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def load_ranking_tables() -> dict[str, dict]:
    """Load all ranking tables from data/rankings/."""
    rankings_dir = Path("data/rankings")
    rankings = {}

    if not rankings_dir.exists():
        print("Warning: data/rankings/ folder not found")
        return rankings

    for json_file in rankings_dir.glob("*.json"):
        table_name = json_file.stem
        rankings[table_name] = load_json_file(str(json_file))

    return rankings


def load_team_profile(team_name: str) -> dict[str, Any] | None:
    """Load a team's profile from data/profiles/."""
    # Normalize team name to filename (lowercase, underscores)
    filename = team_name.lower().replace(" ", "_") + ".json"
    filepath = f"data/profiles/{filename}"
    return load_json_file(filepath)


def get_team_from_rankings(rankings: dict, team_name: str) -> dict | None:
    """Extract a specific team's data from ranking tables."""
    team_data = {}

    for table_name, table_data in rankings.items():
        if not table_data or "data" not in table_data:
            continue

        # Find team in this table
        for row in table_data["data"]:
            if row.get("team", "").lower() == team_name.lower():
                team_data[table_name] = row
                break

    return team_data if team_data else None


def generate_parlays(
    team_a: str,
    team_b: str,
    home_team: str,
    rankings: dict,
    profile_a: dict | None = None,
    profile_b: dict | None = None,
) -> str:
    """
    Generate dual parlays using Claude API.

    Args:
        team_a: First team name
        team_b: Second team name
        home_team: Which team is playing at home
        rankings: All ranking tables
        profile_a: Team A's detailed profile (optional)
        profile_b: Team B's detailed profile (optional)

    Returns:
        Formatted parlay suggestions
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return "Error: ANTHROPIC_API_KEY not found in .env file"

    # Extract team data from rankings
    team_a_stats = get_team_from_rankings(rankings, team_a)
    team_b_stats = get_team_from_rankings(rankings, team_b)

    if not team_a_stats or not team_b_stats:
        return f"Error: Could not find stats for {team_a} or {team_b} in rankings"

    # Build the prompt using prompt.py
    prompt = build_prediction_prompt(
        team_a=team_a,
        team_b=team_b,
        home_team=home_team,
        team_a_stats=team_a_stats,
        team_b_stats=team_b_stats,
        profile_a=profile_a,
        profile_b=profile_b,
    )

    # Call Claude API
    client = anthropic.Anthropic(api_key=api_key)

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )

        return message.content[0].text

    except Exception as e:
        return f"Error calling Anthropic API: {str(e)}"


def main():
    """Test the prediction engine."""
    print("Loading rankings...")
    rankings = load_ranking_tables()
    print(f"Loaded {len(rankings)} ranking tables")

    # Test with example teams
    team_a = "Indianapolis Colts"
    team_b = "Dallas Cowboys"
    home_team = team_a

    print(f"\nGenerating parlays for {team_a} vs {team_b}...")
    result = generate_parlays(team_a, team_b, home_team, rankings)
    print("\n" + "=" * 70)
    print(result)
    print("=" * 70)


if __name__ == "__main__":
    main()
