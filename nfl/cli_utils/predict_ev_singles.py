"""EV+ Singles prediction CLI commands for NFL - Refactored with services."""

import os
import re
import inquirer
from datetime import date, datetime
from pathlib import Path

# Import shared services and utilities
from shared.services import (
    create_team_service_for_sport,
    MetadataService,
    PredictionsMetadataService,
    ProfileService,
    OddsService
)
from shared.repositories import PredictionRepository, OddsRepository
from shared.utils.console_utils import (
    print_header,
    print_success,
    print_error,
    print_info,
    print_warning,
    print_cost_info,
    print_cancelled,
    console
)
from shared.utils.validation_utils import is_valid_inquirer_date
from shared.config import get_metadata_path, get_file_path

# Import sport factory and scrapers
from shared.factory import SportFactory
import shared.register_sports
from nfl.odds_scraper import NFLOddsScraper
from shared.utils.web_scraper import WebScraper
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Initialize services
nfl_sport = SportFactory.create("nfl")
team_service = create_team_service_for_sport("nfl")
predictions_ev_metadata_service = PredictionsMetadataService(get_metadata_path("nfl", "predictions_ev"))
profile_metadata_service = MetadataService(get_metadata_path("nfl", "profiles"))
profile_service = ProfileService("nfl", nfl_sport.scraper, profile_metadata_service)
odds_service = OddsService("nfl")
prediction_repo = PredictionRepository("nfl", prediction_type="predictions_ev")
odds_repo = OddsRepository("nfl")


def fetch_and_save_odds_from_url(
    url: str,
    game_date: str,
    team_a_abbr: str,
    team_b_abbr: str,
    home_abbr: str
) -> dict | None:
    """Fetch DraftKings HTML from URL and extract odds.

    Args:
        url: DraftKings game URL
        game_date: Game date in YYYY-MM-DD format
        team_a_abbr: First team abbreviation
        team_b_abbr: Second team abbreviation
        home_abbr: Home team abbreviation

    Returns:
        Odds dictionary if successful, None otherwise
    """
    try:
        print_info("🌐 Fetching DraftKings page...")

        # Fetch HTML using Playwright
        scraper = WebScraper(headless=True, timeout=30000)
        with scraper.launch() as page:
            scraper.navigate_and_wait(page, url, wait_time=3000)
            html_content = page.content()

        print_success("Page fetched successfully")

        # Save HTML to temp file for odds scraper
        temp_html_path = Path("nfl/data/odds") / "temp_dk_page.html"
        temp_html_path.parent.mkdir(parents=True, exist_ok=True)
        temp_html_path.write_text(html_content, encoding='utf-8')

        # Extract odds using existing scraper
        print_info("📊 Extracting odds from page...")
        odds_scraper = NFLOddsScraper()
        odds_data = odds_scraper.extract_odds(str(temp_html_path))

        # Clean up temp file
        temp_html_path.unlink()

        # Save odds using repository
        # Determine away/home order
        away_abbr = team_a_abbr if team_a_abbr != home_abbr else team_b_abbr
        odds_repo.save_odds(game_date, away_abbr, home_abbr, odds_data)

        print_success(f"Odds saved successfully")

        return odds_data

    except Exception as e:
        print_error(f"Error fetching odds from URL: {str(e)}")
        print_warning("Please check the URL and try again, or use the fetch-odds command with a saved HTML file.")
        return None


def parse_ev_singles_text(prediction_text: str) -> list[dict]:
    """Parse EV singles prediction text to extract structured bet data.

    Returns:
        List of 5 bet dictionaries with EV analysis
    """
    bets = []

    # Pattern to match EV singles output format
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
    team_a_abbr: str,
    team_b_abbr: str,
    prediction_text: str,
    cost: float,
    model: str,
    tokens: dict
):
    """Save EV prediction to markdown and JSON files using repository."""
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

    # Determine correct order (home team first)
    if home_team == team_a:
        home_abbr, away_abbr = team_a_abbr, team_b_abbr
    else:
        home_abbr, away_abbr = team_b_abbr, team_a_abbr

    # Save using repository
    prediction_repo.save_prediction(game_date, home_abbr, away_abbr, markdown, file_format="md")
    prediction_repo.save_prediction(game_date, home_abbr, away_abbr, prediction_data, file_format="json")


def predict_ev_singles():
    """Generate 5 EV+ individual bets ranked by expected value."""

    print_header("📊 NFL EV+ SINGLES GENERATOR 📊")
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
            validate=is_valid_inquirer_date
        )
    ]
    date_answers = inquirer.prompt(date_questions)
    if not date_answers:
        print_cancelled()
        return

    game_date = date_answers["game_date"]

    # Team selection using team service
    console.print()
    team_a = team_service.select_team_interactive("Select Team A (use arrow keys)")
    if not team_a:
        print_cancelled()
        return

    team_b = team_service.select_team_interactive("Select Team B (use arrow keys)")
    if not team_b:
        print_cancelled()
        return

    # Home team selection
    home_questions = [
        inquirer.List("home", message="Select home team", choices=[team_a, team_b])
    ]
    home_answers = inquirer.prompt(home_questions)
    if not home_answers:
        print_cancelled()
        return

    home_team = home_answers["home"]

    # Get team abbreviations using team service
    team_a_abbr = team_service.get_team_abbreviation(team_a)
    team_b_abbr = team_service.get_team_abbreviation(team_b)
    home_abbr = team_a_abbr if home_team == team_a else team_b_abbr
    away_abbr = team_b_abbr if home_team == team_a else team_a_abbr

    # Display matchup
    console.print()
    matchup_text = f"[bold white]{team_a}[/bold white] @ [bold white]{team_b}[/bold white] - {game_date}\n"
    matchup_text += f"[dim]HOME: {home_team}[/dim]"
    console.print(Panel(matchup_text, title="[bold green]⚡ MATCHUP ⚡[/bold green]", border_style="green"))

    # Check if already predicted today using metadata service
    was_predicted, game_key = predictions_ev_metadata_service.was_game_predicted_today(
        game_date, team_a_abbr, team_b_abbr, home_abbr
    )

    if was_predicted:
        # Try to load existing prediction
        filepath = get_file_path("nfl", "predictions_ev", "prediction", game_date=game_date, team_a_abbr=home_abbr, team_b_abbr=away_abbr)
        if os.path.exists(filepath):
            console.print()
            print_info("📋 EV+ Singles already generated for this game today.")
            console.print()

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
                print_warning(f"Could not load existing: {str(e)}")
                print_info("Generating new prediction...")
                console.print()

    # Check if odds already exist using odds service
    existing_odds = odds_service.load_odds_for_game(game_date, team_a_abbr, team_b_abbr, home_abbr)

    if not existing_odds:
        # Prompt for DraftKings URL
        console.print()
        print_info("📊 Betting odds required for EV analysis")
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
            print_cancelled()
            return

        dk_url = url_answers["dk_url"].strip()

        if dk_url:
            # Fetch and save odds from URL
            odds_data = fetch_and_save_odds_from_url(dk_url, game_date, team_a_abbr, team_b_abbr, home_abbr)
            if not odds_data:
                print_error("Failed to fetch odds. Cannot generate EV predictions without odds.")
                return
        else:
            print_warning("No URL provided. Cannot generate EV predictions without odds.")
            return
    else:
        console.print()
        print_success("Using existing odds file")

    # Auto-fetch rankings if needed
    if not nfl_sport.scraper.rankings_metadata_mgr.was_scraped_today():
        console.print()
        print_info("📊 Fetching fresh rankings data...")
        nfl_sport.scraper.extract_rankings()

    # Load rankings
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task(description="Loading ranking data...", total=None)
        rankings = nfl_sport.predictor.load_ranking_tables()

    if not rankings:
        print_error("Could not load ranking data.")
        return

    # Load team profiles
    console.print()
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task(description="Loading team profile data...", total=None)
        profiles = profile_service.load_team_profiles(team_a, team_b)
        profile_a = profiles.get(team_a)
        profile_b = profiles.get(team_b)

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

    # Load odds (REQUIRED for EV analysis) using odds service
    console.print()
    print_info("📊 Loading betting odds (required for EV analysis)...")
    odds_data = odds_service.load_odds_for_game(game_date, team_a_abbr, team_b_abbr, home_abbr)

    if not odds_data:
        console.print()
        error_text = "[bold red]ERROR: Odds required for EV+ analysis[/bold red]\n\n"
        error_text += "[yellow]EV+ mode calculates expected value by comparing odds to stats.[/yellow]\n"
        error_text += "Odds data is required but could not be loaded.\n\n"
        error_text += "Please provide a valid DraftKings game URL when prompted, or\n"
        error_text += f"fetch odds first: [cyan]python main.py → NFL → Fetch Odds[/cyan]"
        console.print(Panel(error_text, border_style="red", padding=(1, 2)))
        return

    print_success("Loaded betting odds from DraftKings")
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

    # Display cost information using console utils
    print_cost_info(cost, tokens['input'], tokens['output'], tokens['total'])
    console.print(f"[dim]Model: {model}[/dim]")

    # Save files and metadata
    try:
        save_ev_prediction_to_files(
            game_date, team_a, team_b, home_team,
            team_a_abbr, team_b_abbr,
            prediction_text, cost, model, tokens
        )

        # Update metadata using service
        predictions_ev_metadata_service.mark_game_predicted(
            game_key,
            game_date,
            [team_a, team_b],
            home_team,
            home_abbr,
            odds_used=True,
            odds_source="draftkings"
        )

        # Display save confirmation
        filename = f"{home_abbr}_{away_abbr}.md"
        print_success(f"Saved to nfl/data/predictions_ev/{game_date}/{filename}")

    except Exception as e:
        console.print()
        console.print(Panel(
            f"[bold red]Failed to Save Prediction[/bold red]\n\n{str(e)}",
            border_style="red",
            padding=(1, 2)
        ))
