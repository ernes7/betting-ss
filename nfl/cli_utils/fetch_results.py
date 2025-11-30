"""Fetch results CLI commands for NFL - Optimized with programmatic bet checking."""

from datetime import datetime

import inquirer
from rich.console import Console
from rich.panel import Panel

# Import shared services
from shared.services import MetadataService, PredictionsMetadataService
from shared.repositories import ResultsRepository, PredictionRepository, AnalysisRepository, EVResultsRepository
from shared.utils.console_utils import print_header, print_cancelled
from shared.utils.timezone_utils import get_eastern_now
from shared.utils.bet_result_checker import check_bets
from shared.config import get_metadata_path

from nfl.nfl_config import NFLConfig
from nfl.nfl_results_fetcher import NFLResultsFetcher
from nfl.teams import DK_TO_PFR_ABBR

# Initialize services
console = Console()
predictions_metadata_service = PredictionsMetadataService(get_metadata_path("nfl", "predictions"))
results_repo = ResultsRepository("nfl")
prediction_repo = PredictionRepository("nfl")  # For AI predictions (_ai.json)
ev_results_repo = EVResultsRepository("nfl")   # For EV predictions (_ev.json)
analysis_repo = AnalysisRepository("nfl")


def fetch_game_result_with_fallback(config, fetcher, game_date, home_team_abbr_dk):
    """Fetch game result with fallback abbreviation attempts.

    Args:
        config: NFLConfig instance
        fetcher: NFLResultsFetcher instance
        game_date: Game date string (YYYY-MM-DD)
        home_team_abbr_dk: Home team DraftKings abbreviation

    Returns:
        tuple: (result_data, abbreviation_used) or raises exception
    """
    # Fallback mapping for teams with multiple abbreviations
    FALLBACK_ABBRS = {
        "lv": ["rai", "lv", "lvr", "oak"],     # Las Vegas Raiders (formerly Oakland)
        "lar": ["ram", "lar", "stl"],          # LA Rams (formerly St. Louis)
        "lac": ["lac", "sdg"],                 # LA Chargers (formerly San Diego)
        "ari": ["crd", "ari"],                 # Arizona Cardinals
        "ind": ["clt", "ind"],                 # Indianapolis Colts
        "bal": ["rav", "bal"],                 # Baltimore Ravens
        "ten": ["oti", "ten"],                 # Tennessee Titans
    }

    # Get PFR abbreviation from mapping first
    pfr_abbr = DK_TO_PFR_ABBR.get(home_team_abbr_dk.upper())

    # Build list of abbreviations to try
    if pfr_abbr:
        abbreviations_to_try = [pfr_abbr]
    else:
        abbreviations_to_try = [home_team_abbr_dk.lower()]

    # Add fallback variants if available
    if home_team_abbr_dk.lower() in FALLBACK_ABBRS:
        for fallback in FALLBACK_ABBRS[home_team_abbr_dk.lower()]:
            if fallback not in abbreviations_to_try:
                abbreviations_to_try.append(fallback)

    # Try each abbreviation
    last_error = None
    for abbr in abbreviations_to_try:
        try:
            boxscore_url = config.build_boxscore_url(game_date, abbr)
            result_data = fetcher.extract_game_result(boxscore_url)

            # Success! Return the result and which abbreviation worked
            if abbr != abbreviations_to_try[0]:
                console.print(f"  [dim][yellow]→ Used fallback abbreviation '{abbr}' (primary '{abbreviations_to_try[0]}' failed)[/yellow][/dim]")

            return result_data, abbr

        except Exception as e:
            error_str = str(e)
            if "404" in error_str or "not found" in error_str.lower():
                last_error = e
                # Try next abbreviation
                continue
            else:
                # Non-404 error, raise immediately
                raise

    # All attempts failed
    if last_error:
        raise last_error
    else:
        raise Exception(f"Failed to fetch game result for all abbreviation variants: {abbreviations_to_try}")


def fetch_results():
    """Fetch results for NFL predictions and calculate P&L.

    Workflow:
    1. Load predictions metadata
    2. Filter games where results_fetched != true
    3. For each game:
       - Fetch game results from Pro-Football-Reference
       - Load prediction JSON to get the 5 bets
       - Analyze each bet (win/loss)
       - Calculate P&L: Win = FIXED_BET_AMOUNT * (odds/100), Loss = -FIXED_BET_AMOUNT
       - Save to nfl/data/results/{date}/{game}.json
    4. Update predictions metadata
    """
    from nfl.constants import FIXED_BET_AMOUNT

    print_header("💰 NFL RESULTS & P/L TRACKER 💰")

    # Load metadata using service
    metadata = predictions_metadata_service.load_metadata()

    if not metadata:
        console.print()
        console.print(Panel(
            "[yellow]No predictions found[/yellow]\n\n"
            "Generate some predictions first using the 'Predict Game' option.",
            title="[bold yellow]⚠ No Data ⚠[/bold yellow]",
            border_style="yellow",
            padding=(1, 2)
        ))
        return

    # Filter games needing results or analysis
    games_to_fetch = []
    for game_key, game_meta in metadata.items():
        # Skip if both results AND analysis are done
        if game_meta.get("results_fetched", False) and game_meta.get("analysis_generated", False):
            continue

        if not game_meta.get("home_team_abbr") or not game_meta.get("game_date"):
            console.print(f"[dim]Skipping {game_key}: missing required metadata[/dim]")
            continue

        games_to_fetch.append({
            "key": game_key,
            "meta": game_meta,
            "needs_results": not game_meta.get("results_fetched", False),
            "needs_analysis": not game_meta.get("analysis_generated", False)
        })

    if not games_to_fetch:
        console.print()
        console.print(Panel(
            "[green]All predictions already have results![/green]\n\n"
            "No pending games need results.",
            title="[bold green]✅ Up to Date ✅[/bold green]",
            border_style="green",
            padding=(1, 2)
        ))
        return

    # Display games
    console.print()
    console.print(f"[bold]Found {len(games_to_fetch)} game(s) needing results:[/bold]\n")

    for game in games_to_fetch:
        date = game["meta"].get("game_date", "unknown")
        matchup = f"{game['meta']['teams'][0]} vs {game['meta']['teams'][1]}"
        console.print(f"  [cyan]{date}[/cyan]: {matchup}")
    console.print()

    # Confirm
    questions = [
        inquirer.Confirm(
            "proceed",
            message=f"Fetch results and calculate P/L for {len(games_to_fetch)} game(s)?",
            default=True
        )
    ]
    answers = inquirer.prompt(questions)

    if not answers or not answers["proceed"]:
        print_cancelled()
        return

    # Initialize fetcher (no AI analyzer needed - using programmatic checker)
    config = NFLConfig()
    fetcher = NFLResultsFetcher(config)

    # Process each game
    console.print()
    console.print(f"[bold]Processing {len(games_to_fetch)} game(s)...[/bold]\n")

    success_count = 0
    failed_count = 0

    for i, game in enumerate(games_to_fetch, 1):
        game_meta = game["meta"]
        game_date = game_meta["game_date"]
        home_abbr = game_meta["home_team_abbr"]
        game_key = game["key"]
        teams = game_meta["teams"]

        console.print(f"[{i}/{len(games_to_fetch)}] {teams[0]} vs {teams[1]} ({game_date})")

        # Extract team abbreviations from game_key (needed for both results and analysis)
        # game_key format: "{date}_{home_abbr}_{away_abbr}" (e.g., "2025-11-02_cin_chi")
        parts = game_key.split("_")
        if parts[0] == game_date:
            home_abbr_extracted = parts[1] if len(parts) > 1 else home_abbr
            away_abbr = parts[2] if len(parts) > 2 else "unknown"
        else:
            home_abbr_extracted = home_abbr
            away_abbr = "unknown"

        try:
            # Fetch game results from PFR (only if needed)
            result_data = None
            if game.get("needs_results", True):
                console.print("  ├─ Fetching game results...", style="dim")

                # Fetch with fallback abbreviations
                result_data, abbr_used = fetch_game_result_with_fallback(config, fetcher, game_date, home_abbr)

                if not result_data:
                    console.print("  └─ [red]✗ No results found (game may not have been played yet)[/red]")
                    failed_count += 1
                    continue

                # Save results using repository
                console.print("  ├─ Saving game results...", style="dim")
                results_repo.save_result(game_date, away_abbr, home_abbr_extracted, result_data)

                # Update metadata using service
                metadata[game_key]["results_fetched"] = True
                metadata[game_key]["results_fetched_at"] = get_eastern_now().strftime("%Y-%m-%d %H:%M:%S")
                predictions_metadata_service.save_metadata(metadata)
            else:
                console.print("  ├─ [dim]Results already fetched, skipping...[/dim]")

            # Programmatic bet analysis (no AI needed)
            if game.get("needs_analysis", True):
                console.print("  ├─ Checking bet results...", style="dim")

                try:
                    # Load result data (either from just-fetched or previously saved)
                    if not game.get("needs_results", True):
                        # Load previously saved results
                        result_data = results_repo.load_result(game_date, away_abbr, home_abbr_extracted)
                        if not result_data:
                            console.print("  └─ [red]✗ Could not load saved results[/red]")
                            failed_count += 1
                            continue

                    # Try to load EV prediction first, then AI prediction
                    prediction_data = None
                    prediction_type_used = None

                    # Try EV prediction (uses _ev.json files)
                    ev_prediction = ev_results_repo.load_ev_results(game_date, home_abbr_extracted, away_abbr)
                    if not ev_prediction:
                        ev_prediction = ev_results_repo.load_ev_results(game_date, away_abbr, home_abbr_extracted)

                    # Try AI prediction (uses _ai.json files)
                    ai_prediction = prediction_repo.load_prediction(game_date, home_abbr_extracted, away_abbr)
                    if not ai_prediction:
                        ai_prediction = prediction_repo.load_prediction(game_date, away_abbr, home_abbr_extracted)

                    # Process both if available, otherwise just one
                    analysis_results = {}

                    if ev_prediction and ev_prediction.get("bets"):
                        ev_analysis = check_bets(ev_prediction, result_data)
                        analysis_results["ev_system"] = ev_analysis
                        prediction_type_used = "EV"

                    if ai_prediction and ai_prediction.get("bets"):
                        ai_analysis = check_bets(ai_prediction, result_data)
                        analysis_results["ai_system"] = ai_analysis
                        if prediction_type_used:
                            prediction_type_used = "AI+EV"
                        else:
                            prediction_type_used = "AI"

                    if not analysis_results:
                        console.print("  └─ [yellow]⚠ No predictions found[/yellow]")
                        failed_count += 1
                        continue

                    # Save analysis
                    analysis_repo.save_analysis(game_date, home_abbr_extracted, away_abbr, analysis_results)

                    # Display P/L summary
                    if "ai_system" in analysis_results and "ev_system" in analysis_results:
                        ai_summary = analysis_results["ai_system"]["summary"]
                        ev_summary = analysis_results["ev_system"]["summary"]
                        console.print(f"  ├─ [green]✓ Analysis complete ({prediction_type_used})[/green]")
                        console.print(f"  ├─ [cyan]AI:[/cyan] ${ai_summary['total_profit']:+.2f} | "
                                    f"{ai_summary['bets_won']}/{ai_summary['total_bets']} wins "
                                    f"({ai_summary['win_rate']:.1f}%)")
                        console.print(f"  └─ [cyan]EV:[/cyan] ${ev_summary['total_profit']:+.2f} | "
                                    f"{ev_summary['bets_won']}/{ev_summary['total_bets']} wins "
                                    f"({ev_summary['win_rate']:.1f}%)")
                    else:
                        # Single system
                        system_key = "ev_system" if "ev_system" in analysis_results else "ai_system"
                        summary = analysis_results[system_key]["summary"]
                        console.print(f"  └─ [green]✓ P/L: ${summary['total_profit']:+.2f} | "
                                    f"{summary['bets_won']}/{summary['total_bets']} wins "
                                    f"({summary['win_rate']:.1f}%)[/green]")

                    # Update metadata
                    metadata[game_key]["analysis_generated"] = True
                    metadata[game_key]["analysis_generated_at"] = get_eastern_now().strftime("%Y-%m-%d %H:%M:%S")
                    predictions_metadata_service.save_metadata(metadata)
                    success_count += 1

                except Exception as analysis_error:
                    console.print(f"  └─ [red]✗ Analysis failed: {str(analysis_error)}[/red]")
                    failed_count += 1
                    continue
            else:
                console.print("  └─ [dim]Analysis already generated, skipping...[/dim]")
                success_count += 1

        except Exception as e:
            console.print(f"  └─ [red]✗ Error: {str(e)}[/red]")
            failed_count += 1
            continue

    # Summary
    console.print()
    console.print(Panel(
        f"[bold green]✅ Success:[/bold green] {success_count}\n"
        f"[bold red]✗ Failed:[/bold red] {failed_count}",
        title="[bold]📊 Results Summary 📊[/bold]",
        border_style="cyan",
        padding=(1, 2)
    ))
