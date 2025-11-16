"""NFL EV Calculator CLI commands."""

import os
import inquirer
from datetime import datetime
from rich.table import Table
from rich.panel import Panel

from shared.models.ev_calculator import EVCalculator
from shared.repositories.ev_results_repository import EVResultsRepository
from shared.repositories.odds_repository import OddsRepository
from shared.services import create_team_service_for_sport
from shared.utils.console_utils import (
    print_header,
    print_success,
    print_error,
    print_info,
    print_warning,
    console
)
from shared.utils.validation_utils import is_valid_inquirer_date
from shared.config import get_data_path
from nfl.nfl_config import NFLConfig


# Initialize services
team_service = create_team_service_for_sport("nfl")
nfl_config = NFLConfig()
ev_repo = EVResultsRepository("nfl")
odds_repo = OddsRepository("nfl")


def ev_analyze_game():
    """Run EV Calculator analysis for a single game."""
    print_header("EV Calculator Analysis")

    # Team selection
    print_info("Select teams for EV analysis")

    away_team = team_service.select_team("Select AWAY team")
    if not away_team:
        print_error("Invalid team selection")
        return

    home_team = team_service.select_team("Select HOME team")
    if not home_team:
        print_error("Invalid team selection")
        return

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
        print_warning("Analysis cancelled")
        return

    game_date = answers["game_date"]

    # Get team abbreviations
    away_abbr = team_service.get_pfr_abbreviation(away_team).lower()
    home_abbr = team_service.get_pfr_abbreviation(home_team).lower()

    print_info(f"\n🎲 Analyzing: {away_team} @ {home_team} ({game_date})")

    # Check if EV results already exist
    existing_results = ev_repo.load_ev_results(game_date, home_abbr, away_abbr)
    if existing_results:
        print_warning("⚠️  EV results already exist for this game")
        questions = [
            inquirer.Confirm(
                "reanalyze",
                message="Reanalyze anyway?",
                default=False
            )
        ]
        answers = inquirer.prompt(questions)
        if not answers or not answers["reanalyze"]:
            print_info("Displaying existing results...")
            _display_ev_results(existing_results)
            return

    # Load odds
    print_info("📊 Loading odds data...")
    odds_data = odds_repo.load_odds(game_date, away_abbr, home_abbr)

    if not odds_data:
        print_error(f"No odds found for this game. Please fetch odds first.")
        return

    print_success("Odds loaded successfully")

    # Run EV Calculator
    print_info("🧮 Running EV Calculator...")

    try:
        ev_calculator = EVCalculator(
            odds_data=odds_data,
            sport_config=nfl_config,
            base_dir=".",
            conservative_adjustment=0.85  # 15% reduction
        )

        # Get top 5 bets
        top_bets = ev_calculator.get_top_n(
            n=5,
            min_ev_threshold=3.0,
            deduplicate_players=True
        )

        if not top_bets:
            print_warning("No bets found with EV >= 3.0%")
            print_info("Try lowering the threshold or check if odds data is complete")
            return

        # Get total bets analyzed
        all_bets = ev_calculator.calculate_all_ev(min_ev_threshold=0.0)
        total_analyzed = len(all_bets)

        print_success(f"✅ Analysis complete! Found {len(top_bets)} high-EV bets (analyzed {total_analyzed} total)")

        # Format results
        ev_results = ev_repo.format_ev_results_for_save(
            ev_calculator_output=top_bets,
            teams=[away_team, home_team],
            home_team=home_team,
            game_date=game_date,
            total_bets_analyzed=total_analyzed,
            conservative_adjustment=0.85
        )

        # Display results
        _display_ev_results(ev_results)

        # Ask to save
        questions = [
            inquirer.Confirm(
                "save",
                message="Save EV results?",
                default=True
            )
        ]
        answers = inquirer.prompt(questions)

        if answers and answers["save"]:
            # Save JSON
            ev_repo.save_ev_results(game_date, home_abbr, away_abbr, ev_results, "json")

            # Save markdown
            ev_markdown = ev_repo.format_ev_results_to_markdown(ev_results)
            ev_repo.save_ev_results(game_date, home_abbr, away_abbr, ev_markdown, "md")

            print_success(f"✅ Results saved:")
            print_success(f"   - {home_abbr}_{away_abbr}_ev.json")
            print_success(f"   - {home_abbr}_{away_abbr}_ev.md")

    except Exception as e:
        print_error(f"Error running EV calculator: {str(e)}")
        import traceback
        traceback.print_exc()


def _display_ev_results(ev_results: dict):
    """Display EV results in a formatted table.

    Args:
        ev_results: EV results dictionary
    """
    bets = ev_results.get("bets", [])
    summary = ev_results.get("summary", {})

    # Display summary
    console.print("\n" + "=" * 70)
    console.print(Panel.fit(
        f"[bold cyan]EV Calculator Summary[/bold cyan]\n\n"
        f"Total bets analyzed: {summary.get('total_bets_analyzed', 0)}\n"
        f"Bets above 3% EV: {summary.get('bets_above_3_percent', 0)}\n"
        f"Top 5 average EV: {summary.get('top_5_avg_ev', 0):.2f}%\n"
        f"Conservative adjustment: {ev_results.get('conservative_adjustment', 0.85) * 100:.0f}%",
        title="📊 Summary",
        border_style="cyan"
    ))

    # Create table for bets
    table = Table(title="\n🎯 Top 5 EV+ Bets", show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=3)
    table.add_column("Bet", style="cyan", width=35)
    table.add_column("Odds", justify="right", style="yellow", width=7)
    table.add_column("Impl%", justify="right", width=7)
    table.add_column("True%", justify="right", width=7)
    table.add_column("Adj%", justify="right", width=7)
    table.add_column("EV%", justify="right", style="bold green", width=8)

    for bet in bets:
        rank = str(bet.get("rank", ""))
        description = bet.get("description", "")
        odds = bet.get("odds", 0)
        implied = f"{bet.get('implied_prob', 0):.1f}"
        true = f"{bet.get('true_prob', 0):.1f}"
        adjusted = f"{bet.get('adjusted_prob', 0):.1f}"
        ev = bet.get("ev_percent", 0)

        # Color code EV
        if ev >= 10:
            ev_str = f"[bold green]+{ev:.2f}%[/bold green]"
        elif ev >= 5:
            ev_str = f"[green]+{ev:.2f}%[/green]"
        else:
            ev_str = f"[yellow]+{ev:.2f}%[/yellow]"

        table.add_row(
            rank,
            description[:35],  # Truncate if too long
            f"{odds:+d}",
            implied,
            true,
            adjusted,
            ev_str
        )

    console.print(table)

    # Display reasoning for top bet
    if bets:
        top_bet = bets[0]
        console.print("\n" + "=" * 70)
        console.print(Panel.fit(
            f"[bold]Bet #{top_bet.get('rank')}:[/bold] {top_bet.get('description')}\n\n"
            f"[dim]{top_bet.get('reasoning', 'No reasoning available')}[/dim]",
            title="💡 Top Bet Reasoning",
            border_style="green"
        ))

    console.print("=" * 70 + "\n")
