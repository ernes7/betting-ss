"""Fetch results CLI commands for NBA - Refactored with services."""

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
from shared.config import get_metadata_path

from nba.nba_config import NBAConfig
from nba.nba_results_fetcher import NBAResultsFetcher
from nba.nba_analyzer import NBAAnalyzer
from nba.teams import DK_TO_PBR_ABBR

# Initialize services
console = Console()
predictions_metadata_service = PredictionsMetadataService(get_metadata_path("nba", "predictions"))
ev_predictions_metadata_service = MetadataService(get_metadata_path("nba", "predictions_ev"))
results_repo = ResultsRepository("nba")


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
        config: NBAConfig instance
        fetcher: NBAResultsFetcher instance
        game_date: Game date string (YYYY-MM-DD)
        home_team_abbr_dk: Home team DraftKings abbreviation

    Returns:
        tuple: (result_data, abbreviation_used) or raises exception
    """
    # Fallback mapping for teams with multiple abbreviations
    FALLBACK_ABBRS = {
        "bkn": ["bkn", "njn"],                 # Brooklyn Nets (formerly New Jersey)
        "cha": ["cha", "cho"],                 # Charlotte Hornets
        "nop": ["nop", "no"],                  # New Orleans Pelicans
        "okc": ["okc", "sea"],                 # Oklahoma City Thunder (formerly Seattle)
        "mem": ["mem", "van"],                 # Memphis Grizzlies (formerly Vancouver)
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
    """Fetch results for all NBA games that have predictions but no results yet.

    Workflow:
    1. Load predictions metadata
    2. Filter games where results_fetched != true (all dates/weeks)
    3. Display count of games to fetch
    4. Confirm with user
    5. Use NBAResultsFetcher to fetch results from Basketball-Reference
    6. Save results to nba/results/{date}/{game}.json
    7. Update predictions metadata: results_fetched = true
    8. Display summary (success/failed counts)
    """
    print_header("📊 NBA RESULTS FETCHER 📊")

    # Load predictions metadata using service
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

    # Filter games that need results fetched
    games_to_fetch = []
    for game_key, game_meta in metadata.items():
        # Check if results already fetched
        if game_meta.get("results_fetched", False):
            continue

        # Validate metadata has required fields
        if not game_meta.get("home_team_abbr") or not game_meta.get("game_date"):
            console.print(f"[dim]Skipping {game_key}: missing required metadata[/dim]")
            continue

        games_to_fetch.append({
            "key": game_key,
            "meta": game_meta
        })

    if not games_to_fetch:
        console.print()
        console.print(Panel(
            "[green]All games already have results fetched![/green]\n\n"
            "No pending games need results.",
            title="[bold green]✅ Up to Date ✅[/bold green]",
            border_style="green",
            padding=(1, 2)
        ))
        return

    # Group games by date/week for display
    games_by_date = defaultdict(list)
    for game in games_to_fetch:
        date = game["meta"].get("game_date", "unknown")
        matchup = f"{game['meta']['teams'][0]} vs {game['meta']['teams'][1]}"
        games_by_date[date].append(matchup)

    # Display games to fetch
    console.print()
    console.print(f"[bold]Found {len(games_to_fetch)} game(s) needing results:[/bold]\n")

    for date, matchups in sorted(games_by_date.items()):
        console.print(f"  [cyan]{date}[/cyan]")
        for matchup in matchups:
            console.print(f"    • {matchup}")
    console.print()

    # Confirm with user
    questions = [
        inquirer.Confirm(
            "proceed",
            message=f"Fetch results for {len(games_to_fetch)} game(s)?",
            default=True
        )
    ]
    answers = inquirer.prompt(questions)

    if not answers or not answers["proceed"]:
        print_cancelled()
        return

    # Initialize fetcher, analyzer, and config
    config = NBAConfig()
    fetcher = NBAResultsFetcher(config)
    analyzer = NBAAnalyzer(config)

    # Fetch results with rate limiting
    console.print()
    console.print("[bold]Fetching results...[/bold]\n")

    success_count = 0
    failed_count = 0
    skipped_count = 0
    analysis_success_count = 0
    analysis_failed_count = 0
    errors = []
    total_cost = 0.0
    total_tokens = 0
    start_time = datetime.now()

    for idx, game in enumerate(games_to_fetch, 1):
        game_key = game["key"]
        game_meta = game["meta"]

        # Extract metadata
        game_date = game_meta["game_date"]
        home_team_abbr = game_meta["home_team_abbr"]
        teams = game_meta["teams"]

        matchup = f"{teams[0]} vs {teams[1]}"
        console.print(f"\n[bold cyan]━━━ Game {idx}/{len(games_to_fetch)}: {matchup} ━━━[/bold cyan]")

        try:
            # Fetch game result with fallback abbreviations
            console.print(f"  [dim]→ Fetching results from Basketball-Reference...[/dim]")
            result_data, abbr_used = fetch_game_result_with_fallback(config, fetcher, game_date, home_team_abbr)

            # Add game_date to result (in case it's not already there)
            result_data["game_date"] = game_date

            # Save result using repository
            # Extract team abbreviations from game_key for save
            # game_key format: "{date}_{home_abbr}_{away_abbr}" (e.g., "2025-11-02_cin_chi")
            parts = game_key.split("_")
            if parts[0] == game_date:
                # Remove date prefix - remaining parts are home and away abbrs
                home_abbr = parts[1] if len(parts) > 1 else home_team_abbr
                away_abbr = parts[2] if len(parts) > 2 else "unknown"
            else:
                # Fallback: use metadata
                home_abbr = home_team_abbr
                away_abbr = "unknown"

            results_repo.save_result(game_date, away_abbr, home_abbr, result_data)

            # Update metadata using service
            metadata[game_key]["results_fetched"] = True
            metadata[game_key]["results_fetched_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            predictions_metadata_service.save_metadata(metadata)

            success_count += 1
            console.print(f"  [green]✅ Result: {result_data['final_score']['away']}-{result_data['final_score']['home']} ({result_data.get('winner', 'Unknown')} wins)[/green]")

            # Generate analysis automatically
            # Parlay analysis disabled - use EV singles analysis instead
            console.print(f"  [dim]→ Parlay analysis disabled (use EV singles for analysis)[/dim]")

        except Exception as e:
            error_msg = str(e)

            # Check if game not played yet
            if "404" in error_msg or "not found" in error_msg.lower():
                skipped_count += 1
                console.print(f"  [yellow]⏭️  Not played yet[/yellow]")
            else:
                failed_count += 1
                errors.append({
                    "game": matchup,
                    "error": error_msg
                })
                console.print(f"  [red]❌ Error: {error_msg}[/red]")

        # No rate limiting needed - parlay analysis is disabled

    # Calculate total time
    end_time = datetime.now()
    total_time = end_time - start_time
    total_minutes = int(total_time.total_seconds() / 60)
    total_seconds = int(total_time.total_seconds() % 60)

    # Display summary
    console.print()
    console.print("[bold green]" + "═" * 60 + "[/bold green]")
    console.print(Panel.fit(
        f"[bold]RESULTS FETCHING COMPLETE[/bold]\n\n"
        f"[green]✅ Successfully fetched: {success_count} game(s)[/green]\n"
        f"[yellow]⏭️  Skipped (not played): {skipped_count} game(s)[/yellow]\n"
        f"[red]❌ Failed: {failed_count} game(s)[/red]\n\n"
        f"[bold]ANALYSIS RESULTS[/bold]\n"
        f"[green]✅ Analyzed: {analysis_success_count} game(s)[/green]\n"
        f"[red]❌ Analysis failed: {analysis_failed_count} game(s)[/red]\n\n"
        f"[bold cyan]💰 Total API cost: ${total_cost:.4f}[/bold cyan]\n"
        f"[dim]Total tokens: {total_tokens:,}[/dim]\n"
        f"[dim]⏱️  Total time: {total_minutes}m {total_seconds}s[/dim]",
        title="[bold cyan]Summary[/bold cyan]",
        border_style="cyan",
        padding=(1, 2)
    ))
    console.print("[bold green]" + "═" * 60 + "[/bold green]")

    # Display errors if any
    if errors:
        console.print()
        console.print("[bold red]Errors:[/bold red]")
        for error in errors:
            console.print(f"  • {error['game']}: {error['error']}")


def fetch_ev_results():
    """Fetch results for EV+ Singles predictions and calculate P&L.

    Workflow:
    1. Load EV predictions metadata
    2. Filter games where results_fetched != true
    3. For each game:
       - Fetch game results from Basketball-Reference
       - Load prediction JSON to get the 5 bets
       - Analyze each bet (win/loss)
       - Calculate P&L: Win = FIXED_BET_AMOUNT * (odds/100), Loss = -FIXED_BET_AMOUNT
       - Save to nba/data/results_ev/{date}/{game}.json
    4. Update predictions_ev metadata
    """
    from nba.constants import FIXED_BET_AMOUNT

    print_header("💰 NBA EV+ RESULTS & P/L TRACKER 💰")

    # Load metadata using service
    metadata = ev_predictions_metadata_service.load_metadata()

    if not metadata:
        console.print()
        console.print(Panel(
            "[yellow]No EV+ predictions found[/yellow]\n\n"
            "Generate some EV+ predictions first using the 'Predict Game (EV+ Singles)' option.",
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
            "[green]All EV+ predictions already have results![/green]\n\n"
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
    config = NBAConfig()
    fetcher = NBAResultsFetcher(config)
    from nba.nba_ev_analyzer import NBAEVAnalyzer
    ev_analyzer = NBAEVAnalyzer(config)

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
                metadata[game_key]["results_fetched_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ev_predictions_metadata_service.save_metadata(metadata)
            else:
                console.print("  ├─ [dim]Results already fetched, skipping...[/dim]")

            # Generate Claude AI analysis (only if needed)
            if game.get("needs_analysis", True):
                console.print("  ├─ Analyzing with Claude AI...", style="dim")

                try:
                    analysis_data = ev_analyzer.generate_analysis(game_key, game_meta)
                    anthropic_api_called = True

                    # Update metadata using service
                    metadata[game_key]["analysis_generated"] = True
                    metadata[game_key]["analysis_generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ev_predictions_metadata_service.save_metadata(metadata)

                    # Display P/L summary
                    summary = analysis_data.get('summary', {})
                    total_profit = summary.get('total_profit', 0)
                    win_rate = summary.get('win_rate', 0)
                    bets_won = summary.get('bets_won', 0)
                    total_bets = summary.get('total_bets', 5)

                    console.print(f"  ├─ [green]✓ Analysis complete[/green]", style="dim")
                    console.print(f"  └─ [green]✓ P/L: ${total_profit:+.2f} | {bets_won}/{total_bets} wins ({win_rate:.1f}%)[/green]")
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
