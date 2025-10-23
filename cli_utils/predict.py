"""Prediction CLI commands."""

import json
import os
from datetime import datetime

import inquirer

from predict import generate_parlays, load_ranking_tables
from teams import TEAMS, TEAM_NAMES


def select_team(prompt):
    """Display team list with arrow key navigation."""
    questions = [
        inquirer.List(
            "team",
            message=prompt,
            choices=TEAM_NAMES,
        ),
    ]
    answers = inquirer.prompt(questions)
    return answers["team"] if answers else None


def save_prediction_to_markdown(
    week: int,
    team_a: str,
    team_b: str,
    home_team: str,
    prediction_text: str,
):
    """Save prediction to markdown file."""
    # Create predictions directory structure
    predictions_dir = "predictions"
    week_dir = os.path.join(predictions_dir, f"w{week}")
    os.makedirs(week_dir, exist_ok=True)

    # Normalize team names for filename
    team_a_normalized = team_a.lower().replace(" ", "_")
    team_b_normalized = team_b.lower().replace(" ", "_")
    filename = f"{team_a_normalized}_{team_b_normalized}.md"
    filepath = os.path.join(week_dir, filename)

    # Build markdown content
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    markdown = f"""# {team_a} vs {team_b} - Week {week}

**Home Team**: {home_team}
**Generated**: {timestamp}

---

{prediction_text}
"""

    # Save to file
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"\n✓ Prediction saved to: {filepath}")


def load_team_profiles(team_a: str, team_b: str) -> tuple[dict, dict]:
    """Load team profiles from data/profiles/{team_name}/ folders."""
    profiles = {}

    for team_name in [team_a, team_b]:
        # Normalize team name to folder name
        team_folder = team_name.lower().replace(" ", "_")
        profile_dir = os.path.join("data/profiles", team_folder)

        # Check if profile folder exists
        if not os.path.exists(profile_dir):
            print(f"Warning: No profile folder found for {team_name} at {profile_dir}")
            profiles[team_name] = {}
            continue

        print(f"Loading profile data for {team_name} from {profile_dir}/")

        # Load all JSON files in the team's folder
        team_profile = {}
        for json_file in os.listdir(profile_dir):
            if json_file.endswith(".json"):
                table_name = json_file.replace(".json", "")
                filepath = os.path.join(profile_dir, json_file)
                try:
                    with open(filepath) as f:
                        team_profile[table_name] = json.load(f)
                except Exception as e:
                    print(f"  Warning: Could not load {json_file}: {str(e)}")
                    continue

        profiles[team_name] = team_profile
        print(f"✓ Loaded {len(team_profile)} tables for {team_name}")

    return profiles[team_a], profiles[team_b]


def predict_game():
    """Generate parlays for a game matchup."""
    print("\n" + "=" * 70)
    print("NFL GAME PARLAY GENERATOR")
    print("=" * 70 + "\n")

    # Ask for week number
    week_questions = [
        inquirer.Text(
            "week",
            message="Enter NFL week number (1-18)",
            validate=lambda _, x: x.isdigit() and 1 <= int(x) <= 18,
        ),
    ]
    week_answers = inquirer.prompt(week_questions)
    if not week_answers:
        print("Selection cancelled.")
        return

    week = int(week_answers["week"])

    # Team selection using arrow keys
    print("\n")
    team_a = select_team("Select Team A (use arrow keys)")
    if not team_a:
        print("Selection cancelled.")
        return

    team_b = select_team("Select Team B (use arrow keys)")
    if not team_b:
        print("Selection cancelled.")
        return

    # Home team selection
    home_questions = [
        inquirer.List(
            "home",
            message="Select home team",
            choices=[team_a, team_b],
        ),
    ]
    home_answers = inquirer.prompt(home_questions)
    if not home_answers:
        print("Selection cancelled.")
        return

    home_team = home_answers["home"]

    # Display matchup
    print(f"\n{'=' * 70}")
    print(f"MATCHUP: {team_a} @ {team_b} - Week {week}")
    print(f"HOME: {home_team}")
    print(f"{'=' * 70}\n")

    # Load ranking data
    print("Loading ranking data...")
    rankings = load_ranking_tables()

    if not rankings:
        print("Error: No ranking data found. Please extract rankings first.")
        return

    # Load or extract team profiles
    print("\nLoading team profile data...")
    profile_a, profile_b = load_team_profiles(team_a, team_b)

    # Validate that we have profile data
    if not profile_a or not profile_b:
        print("\n" + "=" * 70)
        print("ERROR: Failed to load team profile data")
        print("=" * 70)
        if not profile_a:
            print(f"✗ No profile data for {team_a}")
        if not profile_b:
            print(f"✗ No profile data for {team_b}")
        print("\nThis may be due to:")
        print("- Rate limiting from Pro-Football-Reference")
        print("- Network issues")
        print("- Invalid team abbreviations")
        print("\nPlease try again in a few minutes.")
        print("=" * 70 + "\n")
        return

    # Generate parlays
    print("\nGenerating AI parlays with 75%+ confidence...")
    result = generate_parlays(team_a, team_b, home_team, rankings, profile_a, profile_b)

    # Display result
    print("\n" + "=" * 70)
    print(result)
    print("=" * 70 + "\n")

    # Save to markdown
    save_prediction_to_markdown(week, team_a, team_b, home_team, result)
