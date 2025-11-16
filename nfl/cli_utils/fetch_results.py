"""Fetch results CLI commands for NFL - Refactored with services."""

import time
import select
import sys
from datetime import datetime
from collections import defaultdict

import inquirer
from rich.console import Console
from rich.panel import Panel

# Import shared services
from shared.services import MetadataService, PredictionsMetadataService
from shared.repositories import ResultsRepository
from shared.utils.console_utils import print_header, print_cancelled
from shared.utils.timezone_utils import get_eastern_now
from shared.config import get_metadata_path

from nfl.nfl_config import NFLConfig
from nfl.nfl_results_fetcher import NFLResultsFetcher
from nfl.nfl_analyzer import NFLAnalyzer
from nfl.teams import DK_TO_PFR_ABBR

# Initialize services
console = Console()
predictions_metadata_service = PredictionsMetadataService(get_metadata_path("nfl", "predictions"))
results_repo = ResultsRepository("nfl")


def wait_with_countdown(seconds: int, next_game_info: str, current: int, total: int):
    """Wait with interactive countdown timer that can be skipped.

    Args:
        seconds: Number of seconds to wait
        next_game_info: Description of next game to process
        current: Current game number (completed)
        total: Total number of games
    """
    console.print()
    console.print(f"[bold green]✅ Game {current}/{total} complete[/bold green]")
    console.print()
    console.print(Panel.fit(
        f"[bold yellow]⏸️  Rate Limit Delay ({seconds}s)[/bold yellow]\n\n"
        f"[dim]Next up:[/dim] {next_game_info}\n\n"
        f"[dim][Press Enter to skip wait, or wait for countdown][/dim]",
        border_style="yellow"
    ))

    start_time = time.time()

    while True:
        elapsed = time.time() - start_time
        remaining = int(seconds - elapsed)

        if remaining <= 0:
            break

        # Check if Enter was pressed (non-blocking)
        if sys.platform != 'win32':
            # Unix-like systems
            i, o, e = select.select([sys.stdin], [], [], 0.1)
            if i:
                sys.stdin.readline()
                console.print("\n[cyan]⏭️  Skipping wait...[/cyan]")
                break
        else:
            # Windows fallback - just wait
            time.sleep(0.1)

        # Update countdown display with simple counter
        console.print(f"\r  ⏱️  {remaining}s remaining", end="", style="dim")

        time.sleep(0.1)

    console.print("\n")


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

    # Initialize fetcher and analyzer
    config = NFLConfig()
    fetcher = NFLResultsFetcher(config)
    analyzer = NFLAnalyzer(config)

    # Process each game
    console.print()
    console.print(f"[bold]Processing {len(games_to_fetch)} game(s)...[/bold]\n")

    success_count = 0
    failed_count = 0
    anthropic_api_called = False

    for i, game in enumerate(games_to_fetch, 1):
        game_meta = game["meta"]
        game_date = game_meta["game_date"]
        home_abbr = game_meta["home_team_abbr"]
        game_key = game["key"]
        teams = game_meta["teams"]

        console.print(f"[{i}/{len(games_to_fetch)}] {teams[0]} vs {teams[1]} ({game_date})")

        try:
            # Fetch game results from PFR (only if needed)
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
                # Extract team abbreviations from game_key
                # game_key format: "{date}_{home_abbr}_{away_abbr}" (e.g., "2025-11-02_cin_chi")
                parts = game_key.split("_")
                if parts[0] == game_date:
                    # Remove date prefix - remaining parts are home and away abbrs
                    home_abbr_extracted = parts[1] if len(parts) > 1 else home_abbr
                    away_abbr = parts[2] if len(parts) > 2 else "unknown"
                else:
                    # Fallback: use metadata
                    home_abbr_extracted = home_abbr
                    away_abbr = "unknown"

                results_repo.save_result(game_date, away_abbr, home_abbr_extracted, result_data)

                # Update metadata using service
                metadata[game_key]["results_fetched"] = True
                metadata[game_key]["results_fetched_at"] = get_eastern_now().strftime("%Y-%m-%d %H:%M:%S")
                predictions_metadata_service.save_metadata(metadata)
            else:
                console.print("  ├─ [dim]Results already fetched, skipping...[/dim]")

            # Generate Claude AI analysis (only if needed)
            if game.get("needs_analysis", True):
                console.print("  ├─ Analyzing with Claude AI...", style="dim")

                try:
                    # Check which prediction types exist
                    prediction_types = analyzer.check_prediction_types(game_key, game_meta)
                    has_ai = prediction_types.get("has_ai", False)
                    has_ev = prediction_types.get("has_ev", False)

                    # Run appropriate analysis based on what exists
                    if has_ai and has_ev:
                        console.print("  ├─ [cyan]Both AI & EV predictions found - analyzing both systems[/cyan]", style="dim")
                        analysis_data = analyzer.generate_dual_analysis(game_key, game_meta)
                        anthropic_api_called = True

                        # Display P/L summary for both systems
                        ai_summary = analysis_data.get('ai_system', {}).get('summary', {})
                        ev_summary = analysis_data.get('ev_system', {}).get('summary', {})

                        console.print(f"  ├─ [green]✓ Dual analysis complete[/green]", style="dim")
                        console.print(f"  ├─ [cyan]AI System:[/cyan] ${ai_summary.get('total_profit', 0):+.2f} | "
                                    f"{ai_summary.get('bets_won', 0)}/{ai_summary.get('total_bets', 5)} wins "
                                    f"({ai_summary.get('win_rate', 0):.1f}%)")
                        console.print(f"  └─ [cyan]EV System:[/cyan] ${ev_summary.get('total_profit', 0):+.2f} | "
                                    f"{ev_summary.get('bets_won', 0)}/{ev_summary.get('total_bets', 5)} wins "
                                    f"({ev_summary.get('win_rate', 0):.1f}%)")

                    elif has_ai:
                        console.print("  ├─ [cyan]AI prediction found - analyzing AI system[/cyan]", style="dim")
                        analysis_data = analyzer.generate_analysis(game_key, game_meta)
                        anthropic_api_called = True

                        # Display P/L summary
                        summary = analysis_data.get('summary', {})
                        total_profit = summary.get('total_profit', 0)
                        win_rate = summary.get('win_rate', 0)
                        bets_won = summary.get('bets_won', 0)
                        total_bets = summary.get('total_bets', 5)

                        console.print(f"  ├─ [green]✓ Analysis complete[/green]", style="dim")
                        console.print(f"  └─ [green]✓ P/L: ${total_profit:+.2f} | {bets_won}/{total_bets} wins ({win_rate:.1f}%)[/green]")

                    elif has_ev:
                        console.print("  ├─ [cyan]EV prediction found - analyzing EV system[/cyan]", style="dim")
                        analysis_data = analyzer.generate_dual_analysis(game_key, game_meta)
                        anthropic_api_called = True

                        # Display P/L summary
                        ev_summary = analysis_data.get('ev_system', {}).get('summary', {})
                        console.print(f"  ├─ [green]✓ Analysis complete[/green]", style="dim")
                        console.print(f"  └─ [green]✓ P/L: ${ev_summary.get('total_profit', 0):+.2f} | "
                                    f"{ev_summary.get('bets_won', 0)}/{ev_summary.get('total_bets', 5)} wins "
                                    f"({ev_summary.get('win_rate', 0):.1f}%)[/green]")

                    else:
                        console.print("  └─ [yellow]⚠ No predictions found (neither AI nor EV)[/yellow]")
                        failed_count += 1
                        continue

                    # Update metadata using service
                    metadata[game_key]["analysis_generated"] = True
                    metadata[game_key]["analysis_generated_at"] = get_eastern_now().strftime("%Y-%m-%d %H:%M:%S")
                    predictions_metadata_service.save_metadata(metadata)
                    success_count += 1

                except Exception as analysis_error:
                    console.print(f"  └─ [red]✗ Analysis failed: {str(analysis_error)}[/red]")
                    console.print(f"     [dim]Results saved, but analysis incomplete[/dim]")
                    failed_count += 1
                    continue
            else:
                console.print("  └─ [dim]Analysis already generated, skipping...[/dim]")
                success_count += 1

            # Rate limiting for Claude API (60 seconds between calls)
            if anthropic_api_called and i < len(games_to_fetch):
                next_game_info = f"{games_to_fetch[i]['meta']['teams'][0]} vs {games_to_fetch[i]['meta']['teams'][1]}"
                wait_with_countdown(60, next_game_info, i, len(games_to_fetch))
                anthropic_api_called = False

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
