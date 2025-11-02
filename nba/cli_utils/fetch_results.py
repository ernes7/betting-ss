"""Fetch results CLI commands for NBA."""

import json
import os
import time
import select
import sys
from datetime import datetime, timedelta
from collections import defaultdict

import inquirer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from tqdm import tqdm

from nba.nba_config import NBAConfig
from nba.nba_results_fetcher import NBAResultsFetcher
from nba.nba_analyzer import NBAAnalyzer

# Initialize Rich console
console = Console()

# Constants
PREDICTIONS_METADATA_FILE = "nba/data/predictions/.metadata.json"


def load_predictions_metadata() -> dict:
    """Load predictions metadata file.

    Returns:
        Dictionary mapping game keys to prediction metadata
    """
    if os.path.exists(PREDICTIONS_METADATA_FILE):
        try:
            with open(PREDICTIONS_METADATA_FILE) as f:
                return json.load(f)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load predictions metadata: {str(e)}[/yellow]")
            return {}
    return {}


def save_predictions_metadata(metadata: dict):
    """Save predictions metadata file.

    Args:
        metadata: Updated metadata dictionary
    """
    os.makedirs(os.path.dirname(PREDICTIONS_METADATA_FILE), exist_ok=True)
    try:
        with open(PREDICTIONS_METADATA_FILE, "w") as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        console.print(f"[yellow]Warning: Could not save predictions metadata: {str(e)}[/yellow]")


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


def fetch_results():
    """Fetch results for all NBA games that have predictions but no results yet.

    Workflow:
    1. Load predictions metadata
    2. Filter games where results_fetched != true (all dates)
    3. Display count of games to fetch
    4. Confirm with user
    5. Use NBAResultsFetcher to fetch results from Basketball-Reference
    6. Save results to nba/data/results/{date}/{game}.json
    7. Update predictions metadata: results_fetched = true
    8. Display summary (success/failed counts)
    """
    console.print()
    console.print(Panel.fit(
        "[bold cyan]📊 NBA RESULTS FETCHER 📊[/bold cyan]",
        border_style="cyan"
    ))

    # Load predictions metadata
    metadata = load_predictions_metadata()

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

    # Group games by date for display
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
        console.print("[yellow]Fetch cancelled.[/yellow]")
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

        # Track if we called Anthropic API for this game
        called_anthropic = False

        try:
            # Build boxscore URL
            boxscore_url = config.build_boxscore_url(game_date, home_team_abbr)

            # Extract game result
            console.print(f"  [dim]→ Fetching results from Basketball-Reference...[/dim]")
            result_data = fetcher.extract_game_result(boxscore_url)

            # Add game_date to result (in case it's not already there)
            result_data["game_date"] = game_date

            # Save result to JSON
            save_result_to_json(game_date, game_key, result_data, config)

            # Update metadata
            metadata[game_key]["results_fetched"] = True
            metadata[game_key]["results_fetched_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_predictions_metadata(metadata)

            success_count += 1
            console.print(f"  [green]✅ Result: {result_data['final_score']['away']}-{result_data['final_score']['home']} ({result_data.get('winner', 'Unknown')} wins)[/green]")

            # Generate analysis automatically
            try:
                console.print(f"  [dim]→ Analyzing prediction accuracy...[/dim]")
                analysis_data = analyzer.generate_analysis(game_key, game_meta)

                # Mark that we called Anthropic API
                called_anthropic = True

                # Update metadata with analysis flag
                metadata[game_key]["analysis_generated"] = True
                metadata[game_key]["analysis_generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_predictions_metadata(metadata)

                # Extract costs and tokens
                game_cost = analysis_data.get("api_cost", 0)
                game_tokens = analysis_data.get("tokens", {}).get("total", 0)
                total_cost += game_cost
                total_tokens += game_tokens

                # Display analysis summary
                summary = analysis_data.get("summary", {})
                console.print(f"  [dim]→ Analysis: {summary.get('legs_hit', 0)}/{summary.get('total_legs', 0)} legs hit ({summary.get('legs_hit_rate', 0):.1f}%)[/dim]")
                console.print(f"  [dim]💰 Cost: ${game_cost:.4f} ({game_tokens:,} tokens | Total: ${total_cost:.4f})[/dim]")

                analysis_success_count += 1

            except Exception as analysis_error:
                console.print(f"  [yellow]⚠ Analysis failed: {str(analysis_error)}[/yellow]")
                analysis_failed_count += 1
                # Don't fail the entire fetch if analysis fails
                metadata[game_key]["analysis_generated"] = False
                save_predictions_metadata(metadata)

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

        # Rate limit delay (60 seconds between games, except for last game)
        # Only show countdown if we called Anthropic API
        if idx < len(games_to_fetch) and called_anthropic:
            # Get next game info
            next_game = games_to_fetch[idx]
            next_teams = next_game["meta"]["teams"]
            next_game_info = f"{next_teams[0]} vs {next_teams[1]}"

            # Calculate ETA
            remaining_games = len(games_to_fetch) - idx
            eta_seconds = remaining_games * 60
            eta_time = datetime.now() + timedelta(seconds=eta_seconds)

            console.print(f"\n[dim]Progress: {idx}/{len(games_to_fetch)} games | ETA: {eta_time.strftime('%H:%M:%S')}[/dim]")

            # Show countdown
            wait_with_countdown(60, next_game_info, idx, len(games_to_fetch))

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


def save_result_to_json(game_date: str, game_key: str, result_data: dict, config: NBAConfig):
    """Save game result to JSON file.

    Args:
        game_date: Game date identifier
        game_key: Unique game identifier (e.g., "2025-10-24_tor_mil")
        result_data: Game result dictionary
        config: NBA configuration object
    """
    # Create results directory structure
    date_dir = os.path.join(config.results_dir, game_date)
    os.makedirs(date_dir, exist_ok=True)

    # Extract filename from game_key (remove date prefix)
    parts = game_key.split("_")
    if parts[0] == game_date:
        filename = "_".join(parts[1:]) + ".json"
    else:
        filename = game_key + ".json"

    filepath = os.path.join(date_dir, filename)

    # Save to JSON file
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)
