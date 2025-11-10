#!/usr/bin/env python3
"""End-to-end test script for NFL odds fetching.

Tests the complete flow of fetching odds from DraftKings,
validates data completeness, and generates a comprehensive report.

Usage:
    python scripts/test_odds_fetch.py [--limit N] [--no-delay] [--verbose]

Arguments:
    --limit N     Only test first N games (default: all)
    --no-delay    Skip rate limiting for faster testing
    --verbose     Show detailed validation output
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
import time
import random
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from nfl.cli_utils.fetch_odds import (
    scrape_draftkings_schedule,
    parse_todays_game_links,
    fetch_single_game_odds,
    parse_team_abbrs_from_slug,
    check_odds_exist,
)
from nfl.teams import DK_TO_PFR_ABBR
from shared.utils.timezone_utils import iso_to_eastern_date_folder, get_eastern_now

console = Console()


class ValidationResult:
    """Stores validation results for a game."""

    def __init__(self, game_display: str):
        self.game_display = game_display
        self.passed = True
        self.errors = []
        self.warnings = []
        self.stats = {}

    def add_error(self, message: str):
        """Add validation error."""
        self.errors.append(message)
        self.passed = False

    def add_warning(self, message: str):
        """Add validation warning."""
        self.warnings.append(message)

    def add_stat(self, key: str, value):
        """Add statistics."""
        self.stats[key] = value


def validate_odds_file(odds_data: dict, result: ValidationResult):
    """Validate odds data completeness.

    Args:
        odds_data: Odds data dictionary loaded from JSON
        result: ValidationResult to update
    """
    # Validate metadata
    if "teams" not in odds_data:
        result.add_error("Missing teams data")
    else:
        for side in ["away", "home"]:
            if side not in odds_data["teams"]:
                result.add_error(f"Missing {side} team")
            else:
                team = odds_data["teams"][side]
                if not team.get("name"):
                    result.add_error(f"Missing {side} team name")
                if not team.get("abbr"):
                    result.add_error(f"Missing {side} team abbr")

    if not odds_data.get("game_date"):
        result.add_error("Missing game_date")
    if not odds_data.get("source"):
        result.add_error("Missing source")

    # Validate game lines
    game_lines = odds_data.get("game_lines", {})
    if not game_lines:
        result.add_error("Missing game_lines")
    else:
        # Check moneyline
        ml = game_lines.get("moneyline", {})
        if ml.get("away") is None or ml.get("home") is None:
            result.add_error("Incomplete moneyline data")

        # Check spread
        spread = game_lines.get("spread", {})
        required_spread = ["away", "away_odds", "home", "home_odds"]
        if not all(spread.get(f) is not None for f in required_spread):
            result.add_error("Incomplete spread data")

        # Check total
        total = game_lines.get("total", {})
        required_total = ["line", "over", "under"]
        if not all(total.get(f) is not None for f in required_total):
            result.add_error("Incomplete total data")

    # Validate player props
    player_props = odds_data.get("player_props", [])
    if not player_props:
        result.add_warning("No player props found")
    else:
        result.add_stat("player_count", len(player_props))

        # Count props with milestone data
        total_props = 0
        total_milestones = 0
        props_without_milestones = 0

        for player in player_props:
            if not player.get("player"):
                result.add_error("Player missing name")
            if not player.get("team"):
                result.add_error(f"Player {player.get('player', 'unknown')} missing team")

            for prop in player.get("props", []):
                total_props += 1
                if not prop.get("market"):
                    result.add_error(
                        f"Player {player.get('player')} has prop missing market"
                    )

                # Milestones are optional for some markets (e.g., anytime_td)
                milestones = prop.get("milestones", [])
                if milestones:
                    total_milestones += len(milestones)
                    # Validate milestone structure
                    for ms in milestones:
                        if ms.get("line") is None:
                            result.add_error(
                                f"Player {player['player']} {prop['market']} has milestone missing line"
                            )
                        if ms.get("odds") is None:
                            result.add_error(
                                f"Player {player['player']} {prop['market']} has milestone missing odds"
                            )
                else:
                    # Some markets don't have milestones (binary props)
                    props_without_milestones += 1

        result.add_stat("total_props", total_props)
        result.add_stat("total_milestones", total_milestones)
        result.add_stat("props_without_milestones", props_without_milestones)


def test_game(game: dict, verbose: bool = False) -> ValidationResult:
    """Test fetching odds for a game and validate the saved file.

    Args:
        game: Game dict with url, slug, event_id, teams_display
        verbose: Whether to show detailed output

    Returns:
        ValidationResult with results
    """
    result = ValidationResult(game["teams_display"])

    try:
        # Parse team abbreviations
        away_abbr, home_abbr = parse_team_abbrs_from_slug(game["slug"])

        # Check if already exists
        if away_abbr and home_abbr and check_odds_exist(away_abbr, home_abbr):
            if verbose:
                console.print(f"  [dim]Already have odds for {away_abbr} @ {home_abbr}[/dim]")

            # Load and validate existing file
            pfr_away = DK_TO_PFR_ABBR.get(away_abbr, away_abbr.lower())
            pfr_home = DK_TO_PFR_ABBR.get(home_abbr, home_abbr.lower())
            date_str = datetime.now().strftime("%Y-%m-%d")
            odds_file = Path(f"nfl/data/odds/{date_str}/{pfr_home}_{pfr_away}.json")

            if odds_file.exists():
                with open(odds_file, "r") as f:
                    odds_data = json.load(f)
                validate_odds_file(odds_data, result)
                result.add_stat("status", "validated_existing")
                result.add_stat("file_path", str(odds_file))
            else:
                result.add_error("Metadata says odds exist but file not found")

            return result

        # Fetch using the existing function
        fetch_result = fetch_single_game_odds(game["url"], skip_if_exists=False)

        if fetch_result["status"] == "failed":
            result.add_error(f"Fetch failed: {fetch_result['message']}")
            return result

        # Validate the saved data
        odds_data = fetch_result.get("odds_data")
        if not odds_data:
            result.add_error("No odds data returned")
            return result

        validate_odds_file(odds_data, result)

        # Verify file was saved
        dk_away = odds_data["teams"]["away"]["abbr"]
        dk_home = odds_data["teams"]["home"]["abbr"]
        pfr_away = DK_TO_PFR_ABBR.get(dk_away, dk_away.lower())
        pfr_home = DK_TO_PFR_ABBR.get(dk_home, dk_home.lower())
        game_date_str = odds_data.get("game_date", "")

        try:
            date_folder = iso_to_eastern_date_folder(game_date_str)
        except (ValueError, AttributeError):
            date_folder = get_eastern_now().strftime("%Y-%m-%d")

        odds_file = Path(f"nfl/data/odds/{date_folder}/{pfr_home}_{pfr_away}.json")

        if not odds_file.exists():
            result.add_error(f"Odds file not saved: {odds_file}")
        else:
            result.add_stat("file_path", str(odds_file))
            result.add_stat("status", "fetched_new")

    except Exception as e:
        result.add_error(f"Exception: {str(e)}")

    return result


def print_validation_result(result: ValidationResult, verbose: bool = False):
    """Print validation result for a game.

    Args:
        result: ValidationResult to print
        verbose: Whether to show detailed output
    """
    status = result.stats.get("status", "unknown")

    if result.passed:
        if status == "validated_existing":
            console.print("[cyan]✓ VALIDATED (existing)[/cyan]")
        else:
            console.print("[green]✓ PASSED (new)[/green]")

        if verbose:
            console.print(f"  [dim]Players: {result.stats.get('player_count', 0)}[/dim]")
            console.print(f"  [dim]Props: {result.stats.get('total_props', 0)}[/dim]")
            console.print(
                f"  [dim]Milestones: {result.stats.get('total_milestones', 0)}[/dim]"
            )
            if "file_path" in result.stats:
                console.print(f"  [dim]File: {result.stats['file_path']}[/dim]")
    else:
        console.print("[red]✗ FAILED[/red]")
        if verbose:
            for error in result.errors:
                console.print(f"  [red]• {error}[/red]")
        else:
            console.print(f"  [red]• {len(result.errors)} error(s)[/red]")

    if verbose and result.warnings:
        for warning in result.warnings:
            console.print(f"  [yellow]⚠ {warning}[/yellow]")


def main():
    """Main test function."""
    parser = argparse.ArgumentParser(description="Test NFL odds fetching end-to-end")
    parser.add_argument("--limit", type=int, help="Only test first N games")
    parser.add_argument(
        "--no-delay", action="store_true", help="Skip rate limiting for faster testing"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed validation output"
    )

    args = parser.parse_args()

    # Print header
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]🧪 NFL ODDS FETCH TEST SCRIPT[/bold cyan]", border_style="cyan"
        )
    )
    console.print()

    try:
        # Step 1: Fetch schedule
        console.print("📡 Fetching DraftKings schedule...")
        html_content = scrape_draftkings_schedule()
        console.print("[green]✓ Schedule fetched[/green]")

        # Step 2: Parse games
        console.print("🔍 Parsing game URLs...")
        all_games = parse_todays_game_links(html_content)
        console.print(f"[green]✓ Found {len(all_games)} game(s) total[/green]")

        if not all_games:
            console.print("[yellow]No games found. Test aborted.[/yellow]")
            return 1

        # Filter games into three categories (only test today's games)
        started_games = [g for g in all_games if g.get('has_started', False)]
        upcoming_games = [
            g for g in all_games
            if not g.get('has_started', False)
            and g.get('start_time_str', '').startswith('Today')
        ]
        future_games = [
            g for g in all_games
            if not g.get('has_started', False)
            and not g.get('start_time_str', '').startswith('Today')
        ]

        if started_games or future_games:
            status_parts = []
            if upcoming_games:
                status_parts.append(f"{len(upcoming_games)} today")
            if started_games:
                status_parts.append(f"{len(started_games)} started (skipped)")
            if future_games:
                status_parts.append(f"{len(future_games)} future (skipped)")
            console.print(f"[dim]  • {', '.join(status_parts)}[/dim]")

        if not upcoming_games:
            console.print("[yellow]No games scheduled for today to test. Test aborted.[/yellow]")
            return 1

        # Limit games if requested
        games = upcoming_games
        if args.limit:
            games = games[: args.limit]
            console.print(f"[dim]Limited to first {len(games)} game(s)[/dim]")

        console.print()
        console.print(f"🧪 Testing odds fetch/validation for {len(games)} game(s)...")
        console.print()

        # Step 3: Test each game
        results = []

        for idx, game in enumerate(games, 1):
            console.print(f"[cyan][{idx}/{len(games)}] {game['teams_display']}[/cyan]")

            result = test_game(game, verbose=args.verbose)
            results.append(result)

            print_validation_result(result, verbose=args.verbose)
            console.print()

            # Rate limiting (only for new fetches)
            if not args.no_delay and idx < len(games):
                if result.stats.get("status") == "fetched_new":
                    delay = random.uniform(3, 5)
                    if args.verbose:
                        console.print(f"[dim]Waiting {delay:.1f}s...[/dim]")
                    time.sleep(delay)

        # Step 4: Generate report
        console.print("[bold]═" * 40 + "[/bold]")
        console.print()

        passed_count = sum(1 for r in results if r.passed)
        failed_count = len(results) - passed_count
        validated_existing = sum(
            1 for r in results if r.stats.get("status") == "validated_existing"
        )
        fetched_new = sum(
            1 for r in results if r.stats.get("status") == "fetched_new"
        )
        success_rate = (passed_count / len(results)) * 100 if results else 0

        # Summary table
        table = Table(title="Test Summary", show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")

        table.add_row("Total Games", str(len(results)))
        table.add_row("Validated (existing)", f"[cyan]{validated_existing}[/cyan]")
        table.add_row("Fetched (new)", f"[green]{fetched_new}[/green]")
        table.add_row("Passed Validation", f"[green]{passed_count}[/green]")
        table.add_row("Failed Validation", f"[red]{failed_count}[/red]")
        table.add_row("Success Rate", f"{success_rate:.1f}%")

        console.print(table)

        # Failed games details
        if failed_count > 0:
            console.print()
            console.print("[bold red]Failed Games:[/bold red]")
            for result in results:
                if not result.passed:
                    console.print(
                        f"\n[yellow]{result.game_display}[/yellow] ({len(result.errors)} errors)"
                    )
                    for error in result.errors[:5]:  # Show first 5 errors
                        console.print(f"  [red]• {error}[/red]")
                    if len(result.errors) > 5:
                        console.print(
                            f"  [dim]... and {len(result.errors) - 5} more errors[/dim]"
                        )

        console.print()
        if failed_count == 0:
            console.print(
                Panel.fit(
                    "[bold green]✅ ALL TESTS PASSED[/bold green]",
                    border_style="green",
                )
            )
            return 0
        else:
            console.print(
                Panel.fit(
                    f"[bold red]❌ {failed_count} TEST(S) FAILED[/bold red]",
                    border_style="red",
                )
            )
            return 1

    except Exception as e:
        console.print()
        console.print(
            Panel(
                f"[red]Test script error:[/red]\n\n{str(e)}",
                title="[bold red]Error[/bold red]",
                border_style="red",
            )
        )
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
