"""EV+ Singles prediction CLI commands for NFL."""

import json
import os
from datetime import date, datetime
from pathlib import Path

import inquirer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Import sport factory
from shared.factory import SportFactory
import shared.register_sports

from nfl.teams import TEAMS, TEAM_NAMES
from nfl.odds_scraper import NFLOddsScraper
from shared.utils.web_scraper import WebScraper

# Create NFL sport instance
nfl_sport = SportFactory.create("nfl")

# Initialize Rich console
console = Console()

# Metadata file paths
PREDICTIONS_EV_METADATA_FILE = "nfl/data/predictions_ev/.metadata.json"


def load_predictions_ev_metadata() -> dict:
    """Load EV predictions metadata file."""
    if os.path.exists(PREDICTIONS_EV_METADATA_FILE):
        try:
            with open(PREDICTIONS_EV_METADATA_FILE) as f:
                return json.load(f)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load EV metadata: {str(e)}[/yellow]")
            return {}
    return {}


def save_predictions_ev_metadata(metadata: dict):
    """Save EV predictions metadata file."""
    os.makedirs(os.path.dirname(PREDICTIONS_EV_METADATA_FILE), exist_ok=True)
    try:
        with open(PREDICTIONS_EV_METADATA_FILE, "w") as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        console.print(f"[yellow]Warning: Could not save EV metadata: {str(e)}[/yellow]")


def was_ev_predicted_today(game_date: str, team_a: str, team_b: str, home_team: str) -> tuple[bool, str]:
    """Check if game already has EV prediction today.

    Returns:
        (was_predicted: bool, filepath: str)
    """
    metadata = load_predictions_ev_metadata()
    today = date.today().isoformat()

    team_a_abbr = get_team_abbreviation(team_a)
    team_b_abbr = get_team_abbreviation(team_b)

    if home_team == team_a:
        game_key = f"{game_date}_{team_a_abbr}_{team_b_abbr}"
    else:
        game_key = f"{game_date}_{team_b_abbr}_{team_a_abbr}"

    was_predicted = metadata.get(game_key, {}).get("last_predicted") == today

    filename = f"{team_a_abbr}_{team_b_abbr}.md" if home_team == team_a else f"{team_b_abbr}_{team_a_abbr}.md"
    filepath = os.path.join("nfl/data/predictions_ev", game_date, filename)

    return was_predicted, filepath


def select_team(prompt_text):
    """Display team list with arrow key navigation."""
    questions = [
        inquirer.List("team", message=prompt_text, choices=TEAM_NAMES)
    ]
    answers = inquirer.prompt(questions)
    return answers["team"] if answers else None


def get_team_abbreviation(team_name: str) -> str:
    """Get team abbreviation from team name."""
    for team in TEAMS:
        if team["name"] == team_name:
            return team["abbreviation"].lower()
    return team_name.lower().replace(" ", "_")


def load_odds_file(game_date: str, team_a: str, team_b: str, home_team: str) -> dict | None:
    """Load odds file for a game."""
    team_a_abbr = get_team_abbreviation(team_a)
    team_b_abbr = get_team_abbreviation(team_b)

    if home_team == team_a:
        filename = f"{team_a_abbr}_{team_b_abbr}.json"
    else:
        filename = f"{team_b_abbr}_{team_a_abbr}.json"

    odds_filepath = os.path.join("nfl/data/odds", game_date, filename)

    if not os.path.exists(odds_filepath):
        return None

    try:
        with open(odds_filepath, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        console.print(f"[yellow]⚠ Warning: Could not load odds: {str(e)}[/yellow]")
        return None


def fetch_and_save_odds_from_url(url: str, game_date: str, team_a: str, team_b: str, home_team: str) -> dict | None:
    """Fetch DraftKings HTML from URL and extract odds.

    Args:
        url: DraftKings game URL
        game_date: Game date in YYYY-MM-DD format
        team_a: First team name
        team_b: Second team name
        home_team: Home team name

    Returns:
        Odds dictionary if successful, None otherwise
    """
    try:
        console.print("\n[cyan]🌐 Fetching DraftKings page...[/cyan]")

        # Fetch HTML using Playwright
        scraper = WebScraper(headless=True, timeout=30000)
        with scraper.launch() as page:
            scraper.navigate_and_wait(page, url, wait_time=3000)  # Wait 3s for JS to load
            html_content = page.content()

        console.print("[green]✓[/green] Page fetched successfully")

        # Save HTML to temp file for odds scraper
        temp_html_path = Path("nfl/data/odds") / "temp_dk_page.html"
        temp_html_path.parent.mkdir(parents=True, exist_ok=True)
        temp_html_path.write_text(html_content, encoding='utf-8')

        # Extract odds using existing scraper
        console.print("[cyan]📊 Extracting odds from page...[/cyan]")
        odds_scraper = NFLOddsScraper()
        odds_data = odds_scraper.extract_odds(str(temp_html_path))

        # Clean up temp file
        temp_html_path.unlink()

        # Save odds to proper location
        team_a_abbr = get_team_abbreviation(team_a)
        team_b_abbr = get_team_abbreviation(team_b)

        if home_team == team_a:
            filename = f"{team_a_abbr}_{team_b_abbr}.json"
        else:
            filename = f"{team_b_abbr}_{team_a_abbr}.json"

        odds_dir = Path("nfl/data/odds") / game_date
        odds_dir.mkdir(parents=True, exist_ok=True)
        odds_filepath = odds_dir / filename

        with open(odds_filepath, 'w', encoding='utf-8') as f:
            json.dump(odds_data, f, indent=2)

        console.print(f"[green]✓[/green] Odds saved to {odds_filepath}")

        return odds_data

    except Exception as e:
        console.print(f"[bold red]✗ Error fetching odds from URL:[/bold red] {str(e)}")
        console.print("[yellow]Please check the URL and try again, or use the fetch-odds command with a saved HTML file.[/yellow]")
        return None


def parse_ev_singles_text(prediction_text: str) -> list[dict]:
    """Parse EV singles prediction text to extract structured bet data.

    Returns:
        List of 5 bet dictionaries with EV analysis
    """
    import re

    bets = []

    # Pattern to match EV singles output format
    # Note: Fields may have explanatory text in parentheses, so we use [^\n]* to skip to end of line
    bet_pattern = r'## Bet (\d+):.+?\n\*\*Bet\*\*: (.+?)\n\*\*Odds\*\*: ([+-]?\d+)\n\*\*Implied Probability\*\*: ([\d.]+)%[^\n]*\n\*\*True Probability\*\*: ([\d.]+)%[^\n]*\n\*\*Expected Value\*\*: \+?([\d.]+)%[^\n]*\n\*\*Kelly Criterion\*\*: ([\d.]+)%[^:]+half: ([\d.]+)%[^\n]*\n\*\*Reasoning\*\*: (.+?)(?=\n##|\Z)'

    for match in re.finditer(bet_pattern, prediction_text, re.DOTALL):
        bets.append({
            "rank": int(match.group(1)),
            "bet": match.group(2).strip(),
            "odds": int(match.group(3)),
            "implied_probability": float(match.group(4)),
            "true_probability": float(match.group(5)),
            "expected_value": float(match.group(6)),
            "kelly_full": float(match.group(7)),
            "kelly_half": float(match.group(8)),
            "reasoning": match.group(9).strip()
        })

    return bets


def save_ev_prediction_to_files(
    game_date: str,
    team_a: str,
    team_b: str,
    home_team: str,
    prediction_text: str,
    cost: float,
    model: str,
    tokens: dict
):
    """Save EV prediction to markdown and JSON files."""

    # Create predictions_ev directory structure
    predictions_dir = "nfl/data/predictions_ev"
    date_dir = os.path.join(predictions_dir, game_date)
    os.makedirs(date_dir, exist_ok=True)

    # Get team abbreviations
    team_a_abbr = get_team_abbreviation(team_a)
    team_b_abbr = get_team_abbreviation(team_b)

    # Put home team first in filename
    if home_team == team_a:
        base_filename = f"{team_a_abbr}_{team_b_abbr}"
    else:
        base_filename = f"{team_b_abbr}_{team_a_abbr}"

    md_filepath = os.path.join(date_dir, f"{base_filename}.md")
    json_filepath = os.path.join(date_dir, f"{base_filename}.json")

    # Build markdown content
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    markdown = f"""# {team_a} vs {team_b} - EV+ Singles - {game_date}

**Home Team**: {home_team}
**Prediction Type**: EV+ Singles (Expected Value Analysis)
**Generated**: {timestamp}
**Model**: {model}
**API Cost**: ${cost:.4f}

---

{prediction_text}

---

## NOTES
- **EV%**: Expected Value percentage (edge over implied probability)
- **Kelly Criterion**: Optimal bet sizing as % of bankroll
- **Half Kelly**: Recommended conservative stake (safer than full Kelly)
- **Minimum EV**: All bets have +3% or higher expected value
"""

    # Save markdown
    with open(md_filepath, "w", encoding="utf-8") as f:
        f.write(markdown)

    # Parse prediction to extract structured data
    bets = parse_ev_singles_text(prediction_text)

    # Calculate summary stats
    if bets:
        ev_values = [bet["expected_value"] for bet in bets]
        kelly_halfs = [bet["kelly_half"] for bet in bets]
        summary = {
            "total_bets": len(bets),
            "avg_ev": round(sum(ev_values) / len(ev_values), 2),
            "ev_range": [round(min(ev_values), 2), round(max(ev_values), 2)],
            "avg_kelly_half": round(sum(kelly_halfs) / len(kelly_halfs), 2)
        }
    else:
        summary = {"total_bets": 0, "avg_ev": 0, "ev_range": [0, 0], "avg_kelly_half": 0}

    # Build JSON structure
    prediction_data = {
        "sport": "nfl",
        "prediction_type": "ev_singles",
        "teams": [team_a, team_b],
        "home_team": home_team,
        "date": game_date,
        "generated_at": timestamp,
        "model": model,
        "api_cost": cost,
        "tokens": tokens,
        "bets": bets,
        "summary": summary
    }

    # Save JSON
    with open(json_filepath, "w", encoding="utf-8") as f:
        json.dump(prediction_data, f, indent=2, ensure_ascii=False)


def load_team_profiles(team_a: str, team_b: str) -> tuple[dict, dict]:
    """Load team profiles (same logic as predict.py)."""
    from nfl.cli_utils.predict import load_team_profiles as load_profiles
    return load_profiles(team_a, team_b)


def predict_ev_singles():
    """Generate 5 EV+ individual bets ranked by expected value."""

    console.print()
    console.print(Panel.fit(
        "[bold cyan]📊 NFL EV+ SINGLES GENERATOR 📊[/bold cyan]",
        border_style="cyan"
    ))
    console.print()
    console.print("[dim]Analyzes betting odds vs stats to find +EV opportunities[/dim]")
    console.print("[dim]Includes Kelly Criterion stake sizing recommendations[/dim]")

    # Ask for game date
    today = date.today().isoformat()
    date_questions = [
        inquirer.Text(
            "game_date",
            message=f"Enter game date (YYYY-MM-DD) [default: {today}]",
            default=today,
            validate=lambda _, x: len(x.split("-")) == 3 and all(p.isdigit() for p in x.split("-"))
        )
    ]
    date_answers = inquirer.prompt(date_questions)
    if not date_answers:
        console.print("[yellow]Selection cancelled.[/yellow]")
        return

    game_date = date_answers["game_date"]

    # Team selection
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
        inquirer.List("home", message="Select home team", choices=[team_a, team_b])
    ]
    home_answers = inquirer.prompt(home_questions)
    if not home_answers:
        console.print("[yellow]Selection cancelled.[/yellow]")
        return

    home_team = home_answers["home"]

    # Display matchup
    console.print()
    matchup_text = f"[bold white]{team_a}[/bold white] @ [bold white]{team_b}[/bold white] - {game_date}\n"
    matchup_text += f"[dim]HOME: {home_team}[/dim]"
    console.print(Panel(matchup_text, title="[bold green]⚡ MATCHUP ⚡[/bold green]", border_style="green"))

    # Check if already predicted today
    was_predicted, filepath = was_ev_predicted_today(game_date, team_a, team_b, home_team)

    if was_predicted and os.path.exists(filepath):
        console.print()
        console.print("[cyan]📋 EV+ Singles already generated for this game today.[/cyan]\n")

        try:
            with open(filepath, encoding="utf-8") as f:
                content = f.read()
                prediction_content = content.split("---\n", 1)[1] if "---\n" in content else content

            console.print(Panel(Markdown(prediction_content),
                               title="[bold green]📊 TOP 5 EV+ BETS 📊[/bold green]",
                               border_style="green", padding=(1, 2)))
            console.print(f"\n[green]✓[/green] [dim]Using prediction from {filepath}[/dim]")
            return
        except Exception as e:
            console.print(f"[yellow]⚠ Could not load existing: {str(e)}[/yellow]")
            console.print("[cyan]Generating new prediction...[/cyan]\n")

    # Check if odds already exist
    existing_odds = load_odds_file(game_date, team_a, team_b, home_team)

    if not existing_odds:
        # Prompt for DraftKings URL
        console.print()
        console.print("[cyan]📊 Betting odds required for EV analysis[/cyan]")
        console.print("[dim]Please provide the DraftKings game URL to fetch odds[/dim]\n")

        url_questions = [
            inquirer.Text(
                "dk_url",
                message="Enter DraftKings URL (or press Enter to skip)",
                validate=lambda _, x: len(x.strip()) == 0 or "draftkings.com" in x.lower(),
            )
        ]
        url_answers = inquirer.prompt(url_questions)

        if not url_answers:
            console.print("[yellow]Selection cancelled.[/yellow]")
            return

        dk_url = url_answers["dk_url"].strip()

        if dk_url:
            # Fetch and save odds from URL
            odds_data = fetch_and_save_odds_from_url(dk_url, game_date, team_a, team_b, home_team)
            if not odds_data:
                console.print("[bold red]✗ Failed to fetch odds. Cannot generate EV predictions without odds.[/bold red]")
                return
        else:
            console.print("[yellow]⚠ No URL provided. Cannot generate EV predictions without odds.[/yellow]")
            return
    else:
        console.print()
        console.print("[green]✓[/green] [dim]Using existing odds file[/dim]")

    # Auto-fetch rankings if needed
    if not nfl_sport.scraper.rankings_metadata_mgr.was_scraped_today():
        console.print()
        console.print("[cyan]📊 Fetching fresh rankings data...[/cyan]")
        nfl_sport.scraper.extract_rankings()

    # Load rankings
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task(description="Loading ranking data...", total=None)
        rankings = nfl_sport.predictor.load_ranking_tables()

    if not rankings:
        console.print("[bold red]✗ Error:[/bold red] Could not load ranking data.")
        return

    # Load team profiles
    console.print()
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task(description="Loading team profile data...", total=None)
        profile_a, profile_b = load_team_profiles(team_a, team_b)

    # Validate profiles
    if not profile_a or not profile_b:
        console.print()
        error_text = "[bold red]ERROR: Failed to load team profile data[/bold red]\n\n"
        if not profile_a:
            error_text += f"[red]✗[/red] No profile data for {team_a}\n"
        if not profile_b:
            error_text += f"[red]✗[/red] No profile data for {team_b}\n"
        console.print(Panel(error_text, border_style="red", padding=(1, 2)))
        return

    # Load odds (REQUIRED for EV analysis)
    console.print()
    console.print("[cyan]📊 Loading betting odds (required for EV analysis)...[/cyan]")
    odds_data = load_odds_file(game_date, team_a, team_b, home_team)

    if not odds_data:
        console.print()
        team_a_abbr = get_team_abbreviation(team_a)
        team_b_abbr = get_team_abbreviation(team_b)
        home_abbr = team_a_abbr if home_team == team_a else team_b_abbr
        away_abbr = team_b_abbr if home_team == team_a else team_a_abbr

        error_text = "[bold red]ERROR: Odds required for EV+ analysis[/bold red]\n\n"
        error_text += "[yellow]EV+ mode calculates expected value by comparing odds to stats.[/yellow]\n"
        error_text += "Odds data is required.\n\n"
        error_text += "Please fetch odds first:\n"
        error_text += "1. Save DraftKings HTML from game page\n"
        error_text += f"2. Run: [cyan]python main.py → NFL → Fetch Odds[/cyan]\n\n"
        error_text += f"[dim]Expected: nfl/data/odds/{game_date}/{home_abbr}_{away_abbr}.json[/dim]"
        console.print(Panel(error_text, border_style="red", padding=(1, 2)))
        return

    console.print("[green]✓[/green] [dim]Loaded betting odds from DraftKings[/dim]")
    game_lines_count = len(odds_data.get("game_lines", {}))
    player_props_count = len(odds_data.get("player_props", []))
    console.print(f"[dim]  • Game lines: {game_lines_count}[/dim]")
    console.print(f"[dim]  • Player props: {player_props_count} players[/dim]")

    # Generate EV+ singles
    console.print()
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task(description="Analyzing EV+ opportunities with Kelly Criterion...", total=None)
        result = nfl_sport.predictor.generate_ev_singles(
            team_a, team_b, home_team,
            rankings, profile_a, profile_b,
            odds_data
        )

    # Check if API call succeeded
    if not result.get("success", False):
        console.print()
        error_msg = result.get("error", "Unknown error")
        console.print(Panel(
            f"[bold red]API Call Failed[/bold red]\n\n{error_msg}",
            border_style="red",
            padding=(1, 2)
        ))
        return

    # Extract result
    prediction_text = result["prediction"]
    cost = result["cost"]
    model = result["model"]
    tokens = result["tokens"]

    # Display result
    console.print()
    console.print(Panel(Markdown(prediction_text),
                       title="[bold green]📊 TOP 5 EV+ BETS 📊[/bold green]",
                       border_style="green", padding=(1, 2)))

    # Display cost
    console.print(f"\n[dim]Model: {model}[/dim]")
    console.print(f"[dim]Tokens: {tokens['input']:,} input, {tokens['output']:,} output ({tokens['total']:,} total)[/dim]")
    console.print(f"[bold cyan]API Cost: ${cost:.4f}[/bold cyan]")

    # Save files and metadata
    try:
        save_ev_prediction_to_files(game_date, team_a, team_b, home_team,
                                     prediction_text, cost, model, tokens)

        # Update metadata
        metadata = load_predictions_ev_metadata()
        team_a_abbr = get_team_abbreviation(team_a)
        team_b_abbr = get_team_abbreviation(team_b)

        if home_team == team_a:
            game_key = f"{game_date}_{team_a_abbr}_{team_b_abbr}"
        else:
            game_key = f"{game_date}_{team_b_abbr}_{team_a_abbr}"

        # Get home team PFR abbreviation
        home_team_pfr_abbr = None
        for team in TEAMS:
            if team["name"] == home_team:
                home_team_pfr_abbr = team["pfr_abbr"]
                break

        metadata[game_key] = {
            "last_predicted": date.today().isoformat(),
            "prediction_type": "ev_singles",
            "results_fetched": False,
            "odds_used": True,
            "odds_source": "draftkings",
            "game_date": game_date,
            "teams": [team_a, team_b],
            "home_team": home_team,
            "home_team_abbr": home_team_pfr_abbr
        }
        save_predictions_ev_metadata(metadata)

        # Display save confirmation
        filename = f"{team_a_abbr}_{team_b_abbr}.md" if home_team == team_a else f"{team_b_abbr}_{team_a_abbr}.md"
        console.print(f"\n[green]✓[/green] [dim]Saved to nfl/data/predictions_ev/{game_date}/{filename}[/dim]")

    except Exception as e:
        console.print()
        console.print(Panel(
            f"[bold red]Failed to Save Prediction[/bold red]\n\n{str(e)}",
            border_style="red",
            padding=(1, 2)
        ))
