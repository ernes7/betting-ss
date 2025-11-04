"""Prediction CLI commands for NBA - Refactored with services."""

import os
import re
import inquirer
from datetime import date, datetime

# Import shared services
from shared.services import (
    create_team_service_for_sport,
    MetadataService,
    PredictionsMetadataService,
    ProfileService,
    OddsService
)
from shared.repositories import PredictionRepository
from shared.utils.console_utils import (
    print_header,
    print_success,
    print_error,
    print_info,
    print_cost_info,
    print_cancelled,
    print_markdown,
    create_spinner_progress,
    console
)
from shared.utils.validation_utils import is_valid_inquirer_date
from shared.config import get_metadata_path, get_file_path

# Import sport factory
from shared.factory import SportFactory
import shared.register_sports

# Initialize services
nba_sport = SportFactory.create("nba")
team_service = create_team_service_for_sport("nba")
profile_metadata_service = MetadataService(get_metadata_path("nba", "profiles"))
predictions_metadata_service = PredictionsMetadataService(get_metadata_path("nba", "predictions"))
profile_service = ProfileService("nba", nba_sport.scraper, profile_metadata_service)
odds_service = OddsService("nba")
prediction_repo = PredictionRepository("nba")


def parse_prediction_text(prediction_text: str) -> list[dict]:
    """Parse prediction text to extract structured parlay data.

    Args:
        prediction_text: Raw prediction text from Claude API

    Returns:
        List of parlay dictionaries with name, confidence, bets, reasoning
    """
    parlays = []
    # Updated pattern to handle confidence like "97%+" (with optional +)
    parlay_pattern = r'## (Parlay \d+: .+?)\n\*\*Confidence\*\*: (\d+)%\+?\n\n\*\*Bets:\*\*\n(.+?)\n\n\*\*Reasoning\*\*: (.+?)(?=\n##|\Z)'

    for match in re.finditer(parlay_pattern, prediction_text, re.DOTALL):
        parlay_name = match.group(1).strip()
        confidence = int(match.group(2))
        bets_text = match.group(3).strip()
        reasoning = match.group(4).strip()

        # Parse bets list (numbered items)
        bets = []
        for bet_match in re.finditer(r'^\d+\.\s+(.+?)$', bets_text, re.MULTILINE):
            bets.append(bet_match.group(1).strip())

        parlays.append({
            "name": parlay_name,
            "confidence": confidence,
            "bets": bets,
            "reasoning": reasoning,
            "odds": None  # To be filled in later
        })

    return parlays


def save_prediction_to_markdown(
    game_date: str,
    team_a: str,
    team_b: str,
    home_team: str,
    team_a_abbr: str,
    team_b_abbr: str,
    prediction_text: str,
    cost: float = 0.0,
    model: str = "unknown",
    tokens: dict = None,
):
    """Save prediction to markdown and JSON files using repository.

    Args:
        game_date: Game date/week identifier
        team_a: First team name
        team_b: Second team name
        home_team: Home team name
        team_a_abbr: Team A abbreviation
        team_b_abbr: Team B abbreviation
        prediction_text: Raw prediction text from API
        cost: API cost in USD
        model: Model name used
        tokens: Token usage dict with input, output, total keys
    """
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

    # Parse prediction text to extract structured data
    parlays = parse_prediction_text(prediction_text)

    # Build JSON structure
    prediction_data = {
        "sport": "nba",
        "teams": [team_a, team_b],
        "home_team": home_team,
        "date": game_date,
        "generated_at": timestamp,
        "model": model,
        "api_cost": cost,
        "tokens": tokens,
        "parlays": parlays
    }

    # Determine correct order (home team first)
    if home_team == team_a:
        home_abbr, away_abbr = team_a_abbr, team_b_abbr
    else:
        home_abbr, away_abbr = team_b_abbr, team_a_abbr

    # Save using repository
    prediction_repo.save_prediction(game_date, home_abbr, away_abbr, markdown, file_format="md")
    prediction_repo.save_prediction(game_date, home_abbr, away_abbr, prediction_data, file_format="json")


def predict_game():
    """Generate parlays for a game matchup."""
    print_header("🏀 NBA GAME PARLAY GENERATOR 🏀")

    # Ask for game date (default to today)
    today = date.today().isoformat()
    date_questions = [
        inquirer.Text(
            "game_date",
            message=f"Enter game date (YYYY-MM-DD) [default: {today}]",
            default=today,
            validate=is_valid_inquirer_date,
        ),
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
        inquirer.List(
            "home",
            message="Select home team",
            choices=[team_a, team_b],
        ),
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
    from rich.panel import Panel
    matchup_text = f"[bold white]{team_a}[/bold white] @ [bold white]{team_b}[/bold white] - {game_date}\n"
    matchup_text += f"[dim]HOME: {home_team}[/dim]"
    console.print(Panel(matchup_text, title="[bold green]⚡ MATCHUP ⚡[/bold green]", border_style="green"))

    # Check if this game was already predicted today using metadata service
    was_predicted, game_key = predictions_metadata_service.was_game_predicted_today(
        game_date, team_a_abbr, team_b_abbr, home_abbr
    )

    if was_predicted:
        # Try to load existing prediction
        filepath = get_file_path("nba", "predictions", "prediction", game_date=game_date, team_a_abbr=home_abbr, team_b_abbr=away_abbr)
        if os.path.exists(filepath):
            console.print()
            print_info("📋 This game was already predicted today. Loading existing prediction...")
            console.print()

            try:
                with open(filepath, encoding="utf-8") as f:
                    content = f.read()
                    # Extract just the prediction part (skip header)
                    prediction_content = content.split("---\n", 1)[1] if "---\n" in content else content

                from rich.markdown import Markdown
                console.print(Panel(Markdown(prediction_content), title="[bold green]🎯 PARLAYS 🎯[/bold green]", border_style="green", padding=(1, 2)))
                console.print(f"\n[green]✓[/green] [dim]Using prediction from {filepath}[/dim]")
                return
            except Exception as e:
                print_error(f"Could not load existing prediction: {str(e)}")
                print_info("Generating new prediction...")
                console.print()

    # Auto-fetch rankings if needed
    if not nba_sport.scraper.rankings_metadata_mgr.was_scraped_today():
        console.print()
        print_info("📊 Fetching fresh rankings data...")
        nba_sport.scraper.extract_rankings()

    # Load ranking data with spinner
    with create_spinner_progress():
        print_info("Loading ranking data...")
        rankings = nba_sport.predictor.load_ranking_tables()

    if not rankings:
        print_error("Could not load ranking data. Please check your internet connection.")
        return

    # Load team profiles using profile service
    console.print()
    with create_spinner_progress():
        print_info("Loading team profile data...")
        profiles = profile_service.load_team_profiles(team_a, team_b)
        profile_a = profiles.get(team_a)
        profile_b = profiles.get(team_b)

    # Validate that we have profile data - profiles are REQUIRED
    if not profile_a or not profile_b:
        console.print()
        error_text = "[bold red]ERROR: Failed to load team profile data[/bold red]\n\n"
        if not profile_a:
            error_text += f"[red]✗[/red] No profile data for {team_a}\n"
        if not profile_b:
            error_text += f"[red]✗[/red] No profile data for {team_b}\n"
        error_text += "\n[yellow]Possible causes:[/yellow]\n"
        error_text += "• Rate limiting from Basketball-Reference (wait 5 minutes)\n"
        error_text += "• Network connectivity issues\n"
        error_text += "• Invalid team abbreviation\n\n"
        error_text += "[dim]Profile data is required for predictions.[/dim]"
        console.print(Panel(error_text, border_style="red", padding=(1, 2)))
        return

    # Load betting odds (REQUIRED) using odds service
    console.print()
    print_info("📊 Loading betting odds (required)...")
    odds_data = odds_service.load_odds_for_game(game_date, team_a_abbr, team_b_abbr, home_abbr)

    if not odds_data:
        console.print()
        error_text = "[bold red]ERROR: Betting odds are required[/bold red]\n\n"
        error_text += "[yellow]Predictions now require odds for accurate analysis.[/yellow]\n\n"
        error_text += "Please fetch odds first:\n"
        error_text += "1. Save DraftKings HTML from game page to your desktop\n"
        error_text += f"2. Run: [cyan]python main.py → NBA → Fetch Odds[/cyan]\n"
        error_text += f"3. Select the HTML file\n\n"
        error_text += f"[dim]Expected file: nba/data/odds/{game_date}/{home_abbr}_{away_abbr}.json[/dim]"
        console.print(Panel(error_text, border_style="red", padding=(1, 2)))
        return

    print_success("Loaded betting odds from DraftKings")
    # Display summary of available odds
    game_lines_count = len(odds_data.get("game_lines", {}))
    player_props_count = len(odds_data.get("player_props", []))
    console.print(f"[dim]  • Game lines: {game_lines_count}[/dim]")
    console.print(f"[dim]  • Player props: {player_props_count} players[/dim]")

    # Generate parlays with spinner
    console.print()
    with create_spinner_progress():
        console.print("Generating AI parlays with 80%+ confidence...")
        result = nba_sport.predictor.generate_parlays(team_a, team_b, home_team, rankings, profile_a, profile_b, odds_data)

    # Check if API call was successful
    if not result.get("success", False):
        console.print()
        error_msg = result.get("error", "Unknown error")
        console.print(Panel(
            f"[bold red]API Call Failed[/bold red]\n\n{error_msg}\n\n"
            "[yellow]Possible causes:[/yellow]\n"
            "• Rate limiting (30k tokens/minute exceeded)\n"
            "• Network connectivity issues\n"
            "• API service unavailable\n\n"
            "[dim]No files were saved. Metadata was not updated.[/dim]",
            border_style="red",
            padding=(1, 2)
        ))
        return

    # Extract prediction details from result dictionary
    prediction_text = result["prediction"]
    cost = result["cost"]
    model = result["model"]
    tokens = result["tokens"]

    # Display result with markdown rendering
    console.print()
    from rich.markdown import Markdown
    console.print(Panel(Markdown(prediction_text), title="[bold green]🎯 PARLAYS 🎯[/bold green]", border_style="green", padding=(1, 2)))

    # Display cost information using console utils
    print_cost_info(cost, tokens['input'], tokens['output'], tokens['total'])
    console.print(f"[dim]Model: {model}[/dim]")

    # Wrap file save and metadata update in try-catch
    try:
        # Save to markdown and JSON using repository
        save_prediction_to_markdown(
            game_date, team_a, team_b, home_team,
            team_a_abbr, team_b_abbr,
            prediction_text, cost, model, tokens
        )

        # Update predictions metadata using service
        predictions_metadata_service.mark_game_predicted(
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
        print_success(f"Saved to nba/data/predictions/{game_date}/{filename}")

    except Exception as e:
        console.print()
        console.print(Panel(
            f"[bold red]Failed to Save Prediction[/bold red]\n\n{str(e)}\n\n"
            "[dim]Files may not have been saved. Metadata was not updated.[/dim]",
            border_style="red",
            padding=(1, 2)
        ))
