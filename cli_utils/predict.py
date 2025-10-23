"""Prediction CLI commands."""

import inquirer

from predict import generate_parlays, load_ranking_tables
from teams import TEAM_NAMES


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


def predict_game():
    """Generate parlays for a game matchup."""
    print("\n" + "=" * 70)
    print("NFL GAME PARLAY GENERATOR")
    print("=" * 70 + "\n")

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

    # Load ranking data
    print("\nLoading team data...")
    rankings = load_ranking_tables()

    if not rankings:
        print("Error: No ranking data found. Please extract tables first.")
        return

    # Display matchup
    print(f"\n{'=' * 70}")
    print(f"MATCHUP: {team_a} @ {team_b}")
    print(f"HOME: {home_team}")
    print(f"{'=' * 70}\n")

    # Generate parlays
    print("Generating parlays...")
    result = generate_parlays(team_a, team_b, home_team, rankings)

    print("\n" + "=" * 70)
    print(result)
    print("=" * 70 + "\n")
