"""NFL prediction CLI commands - EV+ betting analysis with services."""

import os
import re
import json
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
from shared.services.batch_prediction_service import BatchPredictionService
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
from shared.utils.timezone_utils import get_eastern_now
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
predictions_metadata_service = PredictionsMetadataService(get_metadata_path("nfl", "predictions"))
profile_metadata_service = MetadataService(get_metadata_path("nfl", "profiles"))
profile_service = ProfileService("nfl", nfl_sport.scraper, profile_metadata_service)
odds_service = OddsService("nfl")
prediction_repo = PredictionRepository("nfl")
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

    # Pattern to match EV singles output format (updated to match "Calculation" field)
    bet_pattern = r'## Bet (\d+):.+?\n\*\*Bet\*\*: (.+?)\n\*\*Odds\*\*: ([+-]?\d+)\n\*\*Implied Probability\*\*: ([\d.]+)%[^\n]*\n\*\*True Probability\*\*: ([\d.]+)%[^\n]*\n\*\*Expected Value\*\*: \+?([\d.]+)%[^\n]*\n\*\*Kelly Criterion\*\*: ([\d.]+)%[^:]+half: ([\d.]+)%[^\n]*\n\n\*\*Calculation\*\*:\n(.+?)(?=\n##|\Z)'

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

    # Validation: warn if less than 5 bets were parsed
    if len(bets) < 5:
        print(f"[yellow]⚠ Warning: Only parsed {len(bets)} bets out of expected 5[/yellow]")
        print("[yellow]  This may indicate a truncated or malformed response[/yellow]")

    return bets


def save_ev_prediction_to_files(
    game_date: str,
    team_a: str,
    team_b: str,
    home_team: str,
    team_a_pfr_abbr: str,
    team_b_pfr_abbr: str,
    prediction_text: str,
    cost: float,
    model: str,
    tokens: dict
):
    """Save EV prediction to markdown and JSON files using repository.

    Note: Uses PFR abbreviations for file naming consistency with odds files.
    """
    # Build markdown content
    timestamp = get_eastern_now().strftime("%Y-%m-%d %H:%M:%S")
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

    # Determine correct order (home team first) - using PFR abbreviations
    if home_team == team_a:
        home_pfr, away_pfr = team_a_pfr_abbr, team_b_pfr_abbr
    else:
        home_pfr, away_pfr = team_b_pfr_abbr, team_a_pfr_abbr

    # Save using repository (with PFR abbreviations for consistency with odds files)
    prediction_repo.save_prediction(game_date, home_pfr, away_pfr, markdown, file_format="md")
    prediction_repo.save_prediction(game_date, home_pfr, away_pfr, prediction_data, file_format="json")


def predict_game():
    """Generate 5 EV+ individual bets ranked by expected value."""

    print_header("📊 NFL PREDICTION GENERATOR 📊")
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

    # Get PFR abbreviations for odds file operations
    team_a_pfr = team_service.get_team_pfr_abbreviation(team_a)
    team_b_pfr = team_service.get_team_pfr_abbreviation(team_b)
    home_pfr = team_a_pfr if home_team == team_a else team_b_pfr
    away_pfr = team_b_pfr if home_team == team_a else team_a_pfr

    # Display matchup
    console.print()
    matchup_text = f"[bold white]{team_a}[/bold white] @ [bold white]{team_b}[/bold white] - {game_date}\n"
    matchup_text += f"[dim]HOME: {home_team}[/dim]"
    console.print(Panel(matchup_text, title="[bold green]⚡ MATCHUP ⚡[/bold green]", border_style="green"))

    # Check if already predicted today using metadata service
    was_predicted, game_key = predictions_metadata_service.was_game_predicted_today(
        game_date, team_a_abbr, team_b_abbr, home_abbr
    )

    if was_predicted:
        # Try to load existing prediction
        filepath = get_file_path("nfl", "predictions", "prediction", game_date=game_date, team_a_abbr=home_abbr, team_b_abbr=away_abbr)
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

    # Check if odds already exist using odds service (use PFR abbreviations)
    existing_odds = odds_service.load_odds_for_game(game_date, team_a_pfr, team_b_pfr, home_pfr)

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
            # Fetch and save odds from URL (use PFR abbreviations)
            odds_data = fetch_and_save_odds_from_url(dk_url, game_date, team_a_pfr, team_b_pfr, home_pfr)
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

    # Load odds (REQUIRED for EV analysis) using odds service (use PFR abbreviations)
    console.print()
    print_info("📊 Loading betting odds (required for EV analysis)...")
    odds_data = odds_service.load_odds_for_game(game_date, team_a_pfr, team_b_pfr, home_pfr)

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

    # Generate predictions
    console.print()
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task(description="Analyzing EV+ opportunities with Kelly Criterion...", total=None)
        result = nfl_sport.predictor.generate_predictions(
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
            team_a_pfr, team_b_pfr,
            prediction_text, cost, model, tokens
        )

        # Update metadata using service
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
        print_success(f"Saved to nfl/data/predictions/{game_date}/{filename}")

        # Offer to run EV Calculator
        console.print()
        console.print("[cyan]━" * 40 + "[/cyan]")
        console.print()
        ev_questions = [
            inquirer.Confirm(
                "run_ev",
                message="Run EV Calculator too? (Statistical model, fast & free)",
                default=True
            )
        ]
        ev_answers = inquirer.prompt(ev_questions)

        if ev_answers and ev_answers["run_ev"]:
            console.print()
            print_info("🧮 Running EV Calculator...")

            try:
                from shared.models.ev_calculator import EVCalculator
                from shared.repositories.ev_results_repository import EVResultsRepository
                from shared.services.comparison_service import ComparisonService
                from shared.repositories.comparison_repository import ComparisonRepository

                # Initialize repositories
                ev_repo = EVResultsRepository("nfl")
                comparison_repo = ComparisonRepository("nfl")
                comparison_service = ComparisonService()

                # Run EV Calculator
                ev_calculator = EVCalculator(
                    odds_data=odds_data,
                    sport_config=nfl_sport.config,
                    base_dir=".",
                    conservative_adjustment=0.85
                )

                top_ev_bets = ev_calculator.get_top_n(n=5, min_ev_threshold=3.0)
                all_bets = ev_calculator.calculate_all_ev(min_ev_threshold=0.0)

                # Format and save EV results
                ev_results = ev_repo.format_ev_results_for_save(
                    ev_calculator_output=top_ev_bets,
                    teams=[team_a, team_b],
                    home_team=home_team,
                    game_date=game_date,
                    total_bets_analyzed=len(all_bets),
                    conservative_adjustment=0.85
                )

                ev_repo.save_ev_results(game_date, home_pfr, away_pfr, ev_results, "json")
                ev_markdown = ev_repo.format_ev_results_to_markdown(ev_results)
                ev_repo.save_ev_results(game_date, home_pfr, away_pfr, ev_markdown, "md")

                print_success(f"✅ EV results saved: {home_pfr}_{away_pfr}_ev.json")

                # Generate comparison
                ai_data = result.get("prediction_data", {})
                comparison = comparison_service.compare_predictions(ev_results, ai_data)
                comparison_repo.save_comparison(game_date, home_pfr, away_pfr, comparison)

                print_success(f"✅ Comparison saved: {home_pfr}_{away_pfr}_comparison.json")

                # Display agreement
                agreement_rate = comparison.get("agreement_rate", 0)
                consensus = len(comparison.get("overlapping_bets", []))

                console.print()
                console.print(Panel.fit(
                    f"[bold cyan]Comparison Results[/bold cyan]\n\n"
                    f"Agreement rate: {agreement_rate:.1%}\n"
                    f"Consensus picks: {consensus}/5 bets\n"
                    f"EV-only picks: {len(comparison.get('ev_only_bets', []))}\n"
                    f"AI-only picks: {len(comparison.get('ai_only_bets', []))}",
                    title="📊 Systems Comparison",
                    border_style="green"
                ))

            except Exception as ev_error:
                print_error(f"EV Calculator failed: {str(ev_error)}")

    except Exception as e:
        console.print()
        console.print(Panel(
            f"[bold red]Failed to Save Prediction[/bold red]\n\n{str(e)}",
            border_style="red",
            padding=(1, 2)
        ))


def predict_all_games():
    """Predict all games for a date using schedule.json (batch mode).

    Workflow:
    1. Load schedule.json for the selected date
    2. Filter games: not started AND odds fetched
    3. Auto-fetch rankings once (shared across all predictions)
    4. For each game:
       - Skip if already predicted today
       - Load profiles (with auto-scrape if needed)
       - Load odds from file
       - Generate prediction
       - Save results
    5. Display summary
    """
    print_header("📊 NFL BATCH PREDICTION 📊")
    console.print()
    console.print("[dim]Predict all games for a date automatically using schedule.json[/dim]")
    console.print()

    # Ask for game date
    today = get_eastern_now().strftime("%Y-%m-%d")
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

    # Load schedule.json
    schedule_path = Path(f"nfl/data/odds/{game_date}/schedule.json")
    if not schedule_path.exists():
        console.print()
        console.print(Panel(
            f"[bold red]Schedule file not found![/bold red]\n\n"
            f"[yellow]Expected location:[/yellow]\n{schedule_path}\n\n"
            f"[cyan]Please run 'Fetch Odds' first to generate the schedule file.[/cyan]\n\n"
            f"[dim]The schedule file is created automatically when you fetch odds for a date.[/dim]",
            border_style="red",
            padding=(1, 2)
        ))
        return

    try:
        with open(schedule_path, 'r', encoding='utf-8') as f:
            schedule = json.load(f)
    except Exception as e:
        print_error(f"Failed to load schedule file: {str(e)}")
        return

    # Filter games: not started AND odds fetched
    games_to_predict = [
        g for g in schedule['games']
        if not g.get('has_started', False) and g.get('odds_fetched', False)
    ]

    # Show status
    console.print()
    if not games_to_predict:
        console.print(Panel(
            f"[bold yellow]No games available for prediction![/bold yellow]\n\n"
            f"[dim]Analyzed {len(schedule['games'])} game(s) in schedule:[/dim]\n"
            f"• Games already started: {sum(1 for g in schedule['games'] if g.get('has_started', False))}\n"
            f"• Games missing odds: {sum(1 for g in schedule['games'] if not g.get('odds_fetched', False))}\n"
            f"• Ready for prediction: {len(games_to_predict)}",
            border_style="yellow",
            padding=(1, 2)
        ))
        return

    # Display games to be predicted
    game_list = "\n".join([
        f"  {idx}. {g['teams']['away']['name']} @ {g['teams']['home']['name']}"
        + (f" ({g.get('game_time_display', 'TBD')})" if g.get('game_time_display') else "")
        for idx, g in enumerate(games_to_predict, 1)
    ])

    console.print(Panel(
        f"[bold]Found {len(games_to_predict)} game(s) ready for prediction:[/bold]\n\n{game_list}",
        title="[bold green]🎯 Batch Prediction Queue[/bold green]",
        border_style="green",
        padding=(1, 2)
    ))

    # Confirm
    confirm_questions = [
        inquirer.Confirm(
            "proceed",
            message=f"Proceed with batch prediction for {len(games_to_predict)} game(s)?",
            default=True
        )
    ]
    confirm_answers = inquirer.prompt(confirm_questions)
    if not confirm_answers or not confirm_answers["proceed"]:
        print_cancelled()
        return

    # Auto-fetch rankings once (shared across all predictions)
    console.print()
    if not nfl_sport.scraper.rankings_metadata_mgr.was_scraped_today():
        print_info("📊 Fetching fresh rankings (shared across all predictions)...")
        nfl_sport.scraper.extract_rankings()
    else:
        print_info("📊 Using today's rankings (shared across all predictions)...")

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task(description="Loading ranking data...", total=None)
        rankings = nfl_sport.predictor.load_ranking_tables()

    if not rankings:
        print_error("Could not load rankings. Cannot proceed.")
        return

    print_success("Rankings loaded successfully")

    # Predict each game
    console.print()
    console.print("[bold cyan]Starting batch prediction...[/bold cyan]")
    console.print()

    success_count = 0
    skipped_count = 0
    failed_games = []
    total_cost = 0.0

    for idx, game in enumerate(games_to_predict, 1):
        away_name = game['teams']['away']['name']
        home_name = game['teams']['home']['name']
        away_pfr = game['teams']['away']['pfr_abbr']
        home_pfr = game['teams']['home']['pfr_abbr']

        console.print(f"[cyan][{idx}/{len(games_to_predict)}][/cyan] {away_name} @ {home_name}...", end=" ")

        try:
            # Check if already predicted today
            was_predicted, _ = predictions_metadata_service.was_game_predicted_today(
                game_date, away_pfr, home_pfr, home_pfr
            )

            if was_predicted:
                console.print("[yellow]⊘ Already predicted (skipping)[/yellow]")
                skipped_count += 1
                continue

            # Load profiles (with auto-scrape if needed)
            profiles = profile_service.load_team_profiles(away_name, home_name)

            if not profiles.get(away_name) or not profiles.get(home_name):
                raise Exception(f"Failed to load team profiles")

            # Load odds from file
            odds_data = odds_service.load_odds_for_game(game_date, away_pfr, home_pfr, home_pfr)

            if not odds_data:
                raise Exception("Odds file not found despite schedule indicating odds_fetched=true")

            # Generate prediction
            result = nfl_sport.predictor.generate_predictions(
                team_a=away_name,
                team_b=home_name,
                home_team=home_name,
                rankings=rankings,
                profile_a=profiles[away_name],
                profile_b=profiles[home_name],
                odds=odds_data
            )

            # Check for errors
            if not result['success']:
                raise Exception(result.get('error', 'Unknown prediction error'))

            # Extract values from result
            prediction_text = result['prediction']
            cost = result['cost']
            tokens = result['tokens']
            model = result['model']

            # Parse bets from prediction
            bets = parse_ev_singles_text(prediction_text)

            # Save prediction files
            save_ev_prediction_to_files(
                game_date, away_name, home_name, home_name,
                away_pfr, home_pfr,
                prediction_text, cost, model, tokens
            )

            # Update metadata
            game_key = f"{game_date}_{home_pfr}_{away_pfr}"
            predictions_metadata_service.mark_game_predicted(
                game_key,
                game_date,
                [away_name, home_name],
                home_name,
                home_pfr,
                odds_used=True,
                odds_source="draftkings"
            )

            console.print(f"[green]✓ Predicted ({len(bets)} bets, ${cost:.3f})[/green]")
            success_count += 1
            total_cost += cost

        except Exception as e:
            console.print(f"[red]✗ Failed: {str(e)[:60]}[/red]")
            failed_games.append({
                "game": f"{away_name} @ {home_name}",
                "error": str(e)
            })

    # Display summary
    console.print()
    console.print("[bold]═" * 40 + "[/bold]")
    console.print()

    summary_text = f"[bold cyan]Batch Prediction Summary:[/bold cyan]\n\n"
    summary_text += f"• Predicted: [green]{success_count}[/green] game(s)\n"
    summary_text += f"• Skipped: [yellow]{skipped_count}[/yellow] (already done today)\n"
    summary_text += f"• Failed: [red]{len(failed_games)}[/red] game(s)\n"
    if success_count > 0:
        summary_text += f"• Total cost: [cyan]${total_cost:.3f}[/cyan]\n"
        summary_text += f"• Avg cost per game: [dim]${total_cost/success_count:.3f}[/dim]"

    if success_count > 0:
        summary_text += f"\n\n[dim]Predictions saved to: nfl/data/predictions/{game_date}/[/dim]"

    console.print(Panel(
        summary_text,
        title="[bold green]✅ Batch Prediction Complete[/bold green]" if not failed_games else "[bold yellow]⚠ Batch Prediction Complete (with errors)[/bold yellow]",
        border_style="green" if not failed_games else "yellow",
        padding=(1, 2)
    ))

    # Show failed games if any
    if failed_games:
        console.print()
        console.print("[bold red]Failed Games:[/bold red]")
        for failed in failed_games:
            console.print(f"  • {failed['game']}")
            console.print(f"    [dim]{failed['error'][:100]}[/dim]")


def predict_all_games_dual():
    """Run BOTH EV Calculator and AI Predictor for all games on a date."""
    print_header("Dual Prediction System (EV + AI)")
    
    console.print(Panel.fit(
        "[bold cyan]Run BOTH prediction systems for all games[/bold cyan]\n\n"
        "[white]This will run:[/white]\n"
        "  • [yellow]EV Calculator[/yellow] - Statistical model (fast, free)\n"
        "  • [cyan]AI Predictor[/cyan] - Claude analysis (~$0.15/game)\n"
        "  • [green]Comparison[/green] - Agreement analysis\n\n"
        "[dim]Results saved with _ev, _ai, and _comparison suffixes[/dim]",
        title="ℹ️  Info",
        border_style="cyan"
    ))
    
    # Date selection
    questions = [
        inquirer.Text(
            "game_date",
            message="Game date (YYYY-MM-DD)",
            validate=is_valid_inquirer_date
        )
    ]
    answers = inquirer.prompt(questions)
    if not answers:
        print_warning("Cancelled")
        return
    
    game_date = answers["game_date"]
    
    # Confirm cost
    console.print(f"\n[yellow]⚠️  Cost Estimate:[/yellow]")
    console.print(f"  - EV Calculator: [green]FREE[/green]")
    console.print(f"  - AI Predictor: [yellow]~$0.15 per game[/yellow]")
    console.print(f"  - Estimated total: [yellow]depends on # of games[/yellow]\n")
    
    questions = [
        inquirer.Confirm(
            "confirm",
            message="Continue with dual predictions?",
            default=True
        )
    ]
    answers = inquirer.prompt(questions)
    if not answers or not answers["confirm"]:
        print_warning("Cancelled")
        return
    
    # Initialize batch service
    console.print(f"\n[cyan]Initializing batch prediction service...[/cyan]")
    batch_service = BatchPredictionService("nfl", nfl_sport.config)
    
    # Run dual predictions
    try:
        results = batch_service.run_dual_predictions(
            game_date=game_date,
            base_dir=".",
            conservative_adjustment=0.85,
            min_ev_threshold=3.0,
            skip_existing=True
        )
        
        if not results.get("success"):
            print_error(f"Batch processing failed: {results.get('error', 'Unknown error')}")
            return
        
        # Success message is already printed by the service
        
    except Exception as e:
        print_error(f"Error running dual predictions: {str(e)}")
        import traceback
        traceback.print_exc()
