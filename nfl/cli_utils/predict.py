"""Prediction CLI commands."""

import json
import os
from datetime import date, datetime

import inquirer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Import sport factory for OOP architecture
from shared.factory import SportFactory
import shared.register_sports  # Auto-register sports

from nfl.teams import TEAMS, TEAM_NAMES

# Create NFL sport instance
nfl_sport = SportFactory.create("nfl")

# Initialize Rich console
console = Console()

# Metadata file paths
METADATA_FILE = "nfl/data/profiles/.metadata.json"
PREDICTIONS_METADATA_FILE = "nfl/predictions/.metadata.json"


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
    """Load predictions metadata file tracking when games were predicted.

    Automatically migrates old format (string) to new format (dict) if needed.
    """
    if os.path.exists(PREDICTIONS_METADATA_FILE):
        try:
            with open(PREDICTIONS_METADATA_FILE) as f:
                metadata = json.load(f)

            # Migrate old format to new format
            migrated = False
            for game_key, value in metadata.items():
                if isinstance(value, str):  # Old format: just date string
                    metadata[game_key] = {
                        "last_predicted": value,
                        "results_fetched": False,
                        "game_date": None,  # Can't recover from old format
                        "teams": None,
                        "home_team": None,
                        "home_team_abbr": None
                    }
                    migrated = True

            # Save migrated version
            if migrated:
                save_predictions_metadata(metadata)
                console.print("[dim]Migrated predictions metadata to new format[/dim]")

            return metadata
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


def was_game_predicted_today(game_date: str, team_a: str, team_b: str, home_team: str) -> tuple[bool, str]:
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
        game_key = f"{game_date}_{team_a_abbr}_{team_b_abbr}"
    else:
        game_key = f"{game_date}_{team_b_abbr}_{team_a_abbr}"

    # Check if predicted today
    was_predicted = metadata.get(game_key) == today

    # Build filepath
    filename = f"{team_a_abbr}_{team_b_abbr}.md" if home_team == team_a else f"{team_b_abbr}_{team_a_abbr}.md"
    filepath = os.path.join("nfl/predictions", game_date, filename)

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
    game_date: str,
    team_a: str,
    team_b: str,
    home_team: str,
    prediction_text: str,
    cost: float = 0.0,
    model: str = "unknown",
):
    """Save prediction to markdown file."""
    # Create predictions directory structure
    predictions_dir = "nfl/predictions"
    date_dir = os.path.join(predictions_dir, game_date)
    os.makedirs(date_dir, exist_ok=True)

    # Get team abbreviations
    team_a_abbr = get_team_abbreviation(team_a)
    team_b_abbr = get_team_abbreviation(team_b)

    # Put home team first in filename
    if home_team == team_a:
        filename = f"{team_a_abbr}_{team_b_abbr}.md"
    else:
        filename = f"{team_b_abbr}_{team_a_abbr}.md"

    filepath = os.path.join(date_dir, filename)

    # Build markdown content
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    markdown = f"""# {team_a} vs {team_b} - {game_date}

**Home Team**: {home_team}
**Generated**: {timestamp}
**Model**: {model}
**API Cost**: ${cost:.4f}

---

{prediction_text}

---

## ACTUAL ODDS

**PARLAY 1 ODDS:**

**PARLAY 2 ODDS:**

**PARLAY 3 ODDS:**
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
        profile_dir = os.path.join("nfl/data/profiles", team_folder)

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

            # Extract profile from PFR using OOP architecture
            try:
                nfl_sport.scraper.extract_team_profile(team_name)
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

    # Ask for game date (default to today)
    today = date.today().isoformat()
    date_questions = [
        inquirer.Text(
            "game_date",
            message=f"Enter game date (YYYY-MM-DD) [default: {today}]",
            default=today,
            validate=lambda _, x: len(x.split("-")) == 3 and all(p.isdigit() for p in x.split("-")),
        ),
    ]
    date_answers = inquirer.prompt(date_questions)
    if not date_answers:
        console.print("[yellow]Selection cancelled.[/yellow]")
        return

    game_date = date_answers["game_date"]

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
    matchup_text = f"[bold white]{team_a}[/bold white] @ [bold white]{team_b}[/bold white] - {game_date}\n"
    matchup_text += f"[dim]HOME: {home_team}[/dim]"
    console.print(Panel(matchup_text, title="[bold green]⚡ MATCHUP ⚡[/bold green]", border_style="green"))

    # Check if this game was already predicted today
    was_predicted, filepath = was_game_predicted_today(game_date, team_a, team_b, home_team)

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

    # Auto-fetch rankings if needed using OOP architecture
    if not nfl_sport.scraper.rankings_metadata_mgr.was_scraped_today():
        console.print()
        console.print("[cyan]📊 Fetching fresh rankings data...[/cyan]")
        nfl_sport.scraper.extract_rankings()

    # Load ranking data with spinner using OOP architecture
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        progress.add_task(description="Loading ranking data...", total=None)
        rankings = nfl_sport.predictor.load_ranking_tables()

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

    # Generate parlays with spinner using OOP architecture
    console.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        progress.add_task(description="Generating AI parlays with 80%+ confidence...", total=None)
        result = nfl_sport.predictor.generate_parlays(team_a, team_b, home_team, rankings, profile_a, profile_b)

    # Extract prediction details from result dictionary
    prediction_text = result["prediction"]
    cost = result["cost"]
    model = result["model"]
    tokens = result["tokens"]

    # Display result with markdown rendering
    console.print()
    console.print(Panel(Markdown(prediction_text), title="[bold green]🎯 PARLAYS 🎯[/bold green]", border_style="green", padding=(1, 2)))

    # Display cost information
    console.print(f"\n[dim]Model: {model}[/dim]")
    console.print(f"[dim]Tokens: {tokens['input']:,} input, {tokens['output']:,} output ({tokens['total']:,} total)[/dim]")
    console.print(f"[bold cyan]API Cost: ${cost:.4f}[/bold cyan]")

    # Save to markdown
    save_prediction_to_markdown(game_date, team_a, team_b, home_team, prediction_text, cost, model)

    # Update predictions metadata
    metadata = load_predictions_metadata()
    team_a_abbr = get_team_abbreviation(team_a)
    team_b_abbr = get_team_abbreviation(team_b)

    if home_team == team_a:
        game_key = f"{game_date}_{team_a_abbr}_{team_b_abbr}"
    else:
        game_key = f"{game_date}_{team_b_abbr}_{team_a_abbr}"

    # Get home team PFR abbreviation for boxscore URL
    home_team_pfr_abbr = None
    for team in TEAMS:
        if team["name"] == home_team:
            home_team_pfr_abbr = team["pfr_abbr"]
            break

    # Save enhanced metadata structure
    metadata[game_key] = {
        "last_predicted": date.today().isoformat(),
        "results_fetched": False,
        "game_date": game_date,
        "teams": [team_a, team_b],
        "home_team": home_team,
        "home_team_abbr": home_team_pfr_abbr
    }
    save_predictions_metadata(metadata)

    # Display save confirmation with correct filename format (home team first, abbreviations)
    filename = f"{team_a_abbr}_{team_b_abbr}.md" if home_team == team_a else f"{team_b_abbr}_{team_a_abbr}.md"
    console.print(f"\n[green]✓[/green] [dim]Saved to nfl/predictions/{game_date}/{filename}[/dim]")
