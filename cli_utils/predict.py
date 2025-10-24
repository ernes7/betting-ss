"""Prediction CLI commands."""

import json
import os
from datetime import date, datetime

import inquirer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from extract_profiles import extract_team_profile
from extract_rankings import extract_all_rankings, was_rankings_scraped_today
from predict import generate_parlays, load_ranking_tables
from teams import TEAMS, TEAM_NAMES

# Initialize Rich console
console = Console()

# Metadata file paths
METADATA_FILE = "data/profiles/.metadata.json"
PREDICTIONS_METADATA_FILE = "predictions/.metadata.json"


def load_metadata() -> dict:
    """Load metadata file tracking when teams were last scraped."""
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE) as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load metadata file: {str(e)}")
            return {}
    return {}


def save_metadata(metadata: dict):
    """Save metadata file."""
    os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)
    try:
        with open(METADATA_FILE, "w") as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save metadata file: {str(e)}")


def was_scraped_today(team_folder: str, metadata: dict) -> bool:
    """Check if a team was scraped today."""
    today = date.today().isoformat()
    return metadata.get(team_folder) == today


def load_predictions_metadata() -> dict:
    """Load predictions metadata file tracking when games were predicted."""
    if os.path.exists(PREDICTIONS_METADATA_FILE):
        try:
            with open(PREDICTIONS_METADATA_FILE) as f:
                return json.load(f)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load predictions metadata: {str(e)}[/yellow]")
            return {}
    return {}


def save_predictions_metadata(metadata: dict):
    """Save predictions metadata file."""
    os.makedirs(os.path.dirname(PREDICTIONS_METADATA_FILE), exist_ok=True)
    try:
        with open(PREDICTIONS_METADATA_FILE, "w") as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        console.print(f"[yellow]Warning: Could not save predictions metadata: {str(e)}[/yellow]")


def was_game_predicted_today(week: int, team_a: str, team_b: str, home_team: str) -> tuple[bool, str]:
    """
    Check if a game was already predicted today.

    Returns:
        Tuple of (was_predicted, filepath)
    """
    metadata = load_predictions_metadata()
    today = date.today().isoformat()

    # Generate the game key (same format as filename)
    team_a_abbr = get_team_abbreviation(team_a)
    team_b_abbr = get_team_abbreviation(team_b)

    if home_team == team_a:
        game_key = f"w{week}_{team_a_abbr}_{team_b_abbr}"
    else:
        game_key = f"w{week}_{team_b_abbr}_{team_a_abbr}"

    # Check if predicted today
    was_predicted = metadata.get(game_key) == today

    # Build filepath
    filename = f"{team_a_abbr}_{team_b_abbr}.md" if home_team == team_a else f"{team_b_abbr}_{team_a_abbr}.md"
    filepath = os.path.join("predictions", f"w{week}", filename)

    return was_predicted, filepath


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


def get_team_abbreviation(team_name: str) -> str:
    """Get team abbreviation from team name."""
    for team in TEAMS:
        if team["name"] == team_name:
            return team["abbreviation"].lower()
    # Fallback to normalized full name if not found
    return team_name.lower().replace(" ", "_")


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

    # Get team abbreviations
    team_a_abbr = get_team_abbreviation(team_a)
    team_b_abbr = get_team_abbreviation(team_b)

    # Put home team first in filename
    if home_team == team_a:
        filename = f"{team_a_abbr}_{team_b_abbr}.md"
    else:
        filename = f"{team_b_abbr}_{team_a_abbr}.md"

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


def load_team_profiles(team_a: str, team_b: str) -> tuple[dict, dict]:
    """Load team profiles from data/profiles/{team_name}/ folders.

    Always fetches fresh data unless the team was already scraped today.
    Uses metadata tracking to avoid scraping the same team twice in one day.
    """
    # Load metadata to check what was scraped today
    metadata = load_metadata()
    profiles = {}

    for team_name in [team_a, team_b]:
        # Normalize team name to folder name
        team_folder = team_name.lower().replace(" ", "_")
        profile_dir = os.path.join("data/profiles", team_folder)

        # Check if we already scraped this team today
        if was_scraped_today(team_folder, metadata):
            console.print(f"  [dim]Profile for {team_name} already scraped today, using existing data...[/dim]")
        else:
            console.print(f"  [cyan]Fetching fresh profile data for {team_name}...[/cyan]")

            # Get PFR abbreviation from TEAMS
            pfr_abbr = None
            for team in TEAMS:
                if team["name"] == team_name:
                    pfr_abbr = team["pfr_abbr"]
                    break

            if not pfr_abbr:
                console.print(f"  [red]✗ Could not find PFR abbreviation for {team_name}[/red]")
                profiles[team_name] = None
                continue

            # Extract profile from PFR
            try:
                extract_team_profile(team_name, pfr_abbr)
                console.print(f"  [green]✓ Successfully extracted profile for {team_name}[/green]")

                # Update metadata with today's date
                metadata[team_folder] = date.today().isoformat()
                save_metadata(metadata)
            except Exception as e:
                console.print(f"  [red]✗ Failed to extract profile for {team_name}: {str(e)}[/red]")
                profiles[team_name] = None
                continue

        # Check if profile directory exists
        if not os.path.exists(profile_dir):
            console.print(f"  [red]✗ Profile directory not found for {team_name}[/red]")
            profiles[team_name] = None
            continue

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
                    console.print(f"  [yellow]⚠ Warning: Could not load {json_file}: {str(e)}[/yellow]")
                    continue

        profiles[team_name] = team_profile if team_profile else None
        if team_profile:
            console.print(f"  [green]✓ Loaded {len(team_profile)} tables for {team_name}[/green]")

    return profiles[team_a], profiles[team_b]


def predict_game():
    """Generate parlays for a game matchup."""
    console.print()
    console.print(Panel.fit(
        "[bold cyan]🎲 NFL GAME PARLAY GENERATOR 🎲[/bold cyan]",
        border_style="cyan"
    ))

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
        console.print("[yellow]Selection cancelled.[/yellow]")
        return

    week = int(week_answers["week"])

    # Team selection using arrow keys
    console.print()
    team_a = select_team("Select Team A (use arrow keys)")
    if not team_a:
        console.print("[yellow]Selection cancelled.[/yellow]")
        return

    team_b = select_team("Select Team B (use arrow keys)")
    if not team_b:
        console.print("[yellow]Selection cancelled.[/yellow]")
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
        console.print("[yellow]Selection cancelled.[/yellow]")
        return

    home_team = home_answers["home"]

    # Display matchup with rich formatting
    console.print()
    matchup_text = f"[bold white]{team_a}[/bold white] @ [bold white]{team_b}[/bold white] - Week {week}\n"
    matchup_text += f"[dim]HOME: {home_team}[/dim]"
    console.print(Panel(matchup_text, title="[bold green]⚡ MATCHUP ⚡[/bold green]", border_style="green"))

    # Check if this game was already predicted today
    was_predicted, filepath = was_game_predicted_today(week, team_a, team_b, home_team)

    if was_predicted and os.path.exists(filepath):
        console.print()
        console.print("[cyan]📋 This game was already predicted today. Loading existing prediction...[/cyan]\n")

        # Load and display existing prediction
        try:
            with open(filepath, encoding="utf-8") as f:
                content = f.read()
                # Extract just the prediction part (skip header)
                prediction_content = content.split("---\n", 1)[1] if "---\n" in content else content

            console.print(Panel(Markdown(prediction_content), title="[bold green]🎯 PARLAYS 🎯[/bold green]", border_style="green", padding=(1, 2)))

            team_a_abbr = get_team_abbreviation(team_a)
            team_b_abbr = get_team_abbreviation(team_b)
            filename = f"{team_a_abbr}_{team_b_abbr}.md" if home_team == team_a else f"{team_b_abbr}_{team_a_abbr}.md"
            console.print(f"\n[green]✓[/green] [dim]Using prediction from {filepath}[/dim]")
            return

        except Exception as e:
            console.print(f"[yellow]⚠ Could not load existing prediction: {str(e)}[/yellow]")
            console.print("[cyan]Generating new prediction...[/cyan]\n")

    # Auto-fetch rankings if needed
    if not was_rankings_scraped_today():
        console.print()
        console.print("[cyan]📊 Fetching fresh rankings data...[/cyan]")
        extract_all_rankings()

    # Load ranking data with spinner
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        progress.add_task(description="Loading ranking data...", total=None)
        rankings = load_ranking_tables()

    if not rankings:
        console.print("[bold red]✗ Error:[/bold red] Could not load ranking data. Please check your internet connection.")
        return

    # Load or extract team profiles
    console.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        progress.add_task(description="Loading team profile data...", total=None)
        profile_a, profile_b = load_team_profiles(team_a, team_b)

    # Validate that we have profile data - profiles are REQUIRED
    if not profile_a or not profile_b:
        console.print()
        error_text = "[bold red]ERROR: Failed to load team profile data[/bold red]\n\n"
        if not profile_a:
            error_text += f"[red]✗[/red] No profile data for {team_a}\n"
        if not profile_b:
            error_text += f"[red]✗[/red] No profile data for {team_b}\n"
        error_text += "\n[yellow]Possible causes:[/yellow]\n"
        error_text += "• Rate limiting from Pro-Football-Reference (wait 5 minutes)\n"
        error_text += "• Network connectivity issues\n"
        error_text += "• Invalid team abbreviation\n\n"
        error_text += "[dim]Profile data is required for predictions.[/dim]"
        console.print(Panel(error_text, border_style="red", padding=(1, 2)))
        return

    # Generate parlays with spinner
    console.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        progress.add_task(description="Generating AI parlays with 80%+ confidence...", total=None)
        result = generate_parlays(team_a, team_b, home_team, rankings, profile_a, profile_b)

    # Display result with markdown rendering
    console.print()
    console.print(Panel(Markdown(result), title="[bold green]🎯 PARLAYS 🎯[/bold green]", border_style="green", padding=(1, 2)))

    # Save to markdown
    save_prediction_to_markdown(week, team_a, team_b, home_team, result)

    # Update predictions metadata
    metadata = load_predictions_metadata()
    team_a_abbr = get_team_abbreviation(team_a)
    team_b_abbr = get_team_abbreviation(team_b)

    if home_team == team_a:
        game_key = f"w{week}_{team_a_abbr}_{team_b_abbr}"
    else:
        game_key = f"w{week}_{team_b_abbr}_{team_a_abbr}"

    metadata[game_key] = date.today().isoformat()
    save_predictions_metadata(metadata)

    # Display save confirmation with correct filename format (home team first, abbreviations)
    filename = f"{team_a_abbr}_{team_b_abbr}.md" if home_team == team_a else f"{team_b_abbr}_{team_a_abbr}.md"
    console.print(f"\n[green]✓[/green] [dim]Prediction saved to predictions/w{week}/{filename}[/dim]")
