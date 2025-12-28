"""Multi-Sport Betting Analysis CLI

Interactive menu-based interface for generating betting predictions across multiple sports.
Uses the new services architecture for workflow orchestration.
"""

from typing import List, Optional, Dict, Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

from services.cli import CLIOrchestrator, get_default_config
from shared.factory import SportFactory
import shared.register_sports  # noqa: F401 - triggers sport registration

# Initialize Rich console
console = Console()

# Sport configurations
SPORTS = {
    "1": {
        "name": "NFL",
        "emoji": "🏈",
        "code": "nfl",
    },
    "2": {
        "name": "NBA",
        "emoji": "🏀",
        "code": "nba",
    },
    "3": {
        "name": "Bundesliga",
        "emoji": "⚽",
        "code": "bundesliga",
    },
}


# =============================================================================
# Helper Functions for Game/Date Selection
# =============================================================================


def get_available_dates(orchestrator: CLIOrchestrator) -> List[str]:
    """Get dates that have odds files.

    Args:
        orchestrator: CLI orchestrator instance

    Returns:
        List of dates in YYYY-MM-DD format, newest first
    """
    return orchestrator.odds_service.get_available_dates()


def select_date(orchestrator: CLIOrchestrator, source: str = "odds") -> Optional[str]:
    """Interactive date selection from available data.

    Args:
        orchestrator: CLI orchestrator instance
        source: Data source to check ('odds' or 'predictions')

    Returns:
        Selected date string or None if cancelled
    """
    if source == "predictions":
        dates = get_prediction_dates(orchestrator)
    else:
        dates = get_available_dates(orchestrator)

    if not dates:
        console.print(f"[yellow]No {source} data found for {orchestrator.sport.upper()}[/yellow]")
        return None

    console.print(f"\n[bold cyan]Available Dates ({source}):[/bold cyan]")
    for i, date in enumerate(dates[:15], 1):  # Show max 15 dates
        console.print(f"  {i}. {date}")

    if len(dates) > 15:
        console.print(f"  [dim]... and {len(dates) - 15} more[/dim]")

    choice = Prompt.ask(
        "\n[cyan]Select date number (or type YYYY-MM-DD)[/cyan]",
        default="1"
    )

    # Handle numeric selection
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(dates):
            return dates[idx]
        console.print("[red]Invalid selection[/red]")
        return None

    # Handle direct date input
    if len(choice) == 10 and choice.count("-") == 2:
        return choice

    console.print("[red]Invalid date format[/red]")
    return None


def get_games_for_date(orchestrator: CLIOrchestrator, game_date: str) -> List[Dict[str, Any]]:
    """Get games from odds files for a date.

    Args:
        orchestrator: CLI orchestrator instance
        game_date: Date in YYYY-MM-DD format

    Returns:
        List of game dicts with away_team and home_team
    """
    all_odds = orchestrator.odds_service.get_all_odds_for_date(game_date)
    games = []

    for odds in all_odds:
        teams = odds.get("teams", {})
        away = teams.get("away", {})
        home = teams.get("home", {})

        games.append({
            "away_team": away.get("abbr", away.get("name", "?")),
            "home_team": home.get("abbr", home.get("name", "?")),
            "away_name": away.get("name", ""),
            "home_name": home.get("name", ""),
        })

    return games


def get_prediction_dates(orchestrator: CLIOrchestrator) -> List[str]:
    """Get dates that have prediction files.

    Args:
        orchestrator: CLI orchestrator instance

    Returns:
        List of dates with predictions
    """
    import os
    from pathlib import Path

    pred_dir = Path(f"sports/{orchestrator.sport}/data/predictions")
    if not pred_dir.exists():
        return []

    dates = []
    for d in pred_dir.iterdir():
        if d.is_dir() and len(d.name) == 10:  # YYYY-MM-DD format
            dates.append(d.name)

    return sorted(dates, reverse=True)


def select_games(games: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Interactive game selection.

    Args:
        games: List of available games

    Returns:
        Selected games list
    """
    if not games:
        return []

    console.print(f"\n[bold cyan]Available Games ({len(games)}):[/bold cyan]")
    for i, game in enumerate(games, 1):
        away = game.get("away_team", "?")
        home = game.get("home_team", "?")
        console.print(f"  {i}. {away} @ {home}")

    console.print(f"  A. [bold]All games[/bold]")

    choice = Prompt.ask(
        "\n[cyan]Select games (e.g., '1,2,3' or 'A' for all)[/cyan]",
        default="A"
    )

    if choice.upper() == "A":
        return games

    try:
        indices = [int(x.strip()) - 1 for x in choice.split(",")]
        selected = [games[i] for i in indices if 0 <= i < len(games)]
        return selected
    except (ValueError, IndexError):
        console.print("[yellow]Invalid selection, using all games[/yellow]")
        return games


def display_prediction_results(result: Dict[str, Any], game_info: str):
    """Display prediction results in a formatted panel.

    Args:
        result: Prediction result dictionary
        game_info: Game description string
    """
    if not result.get("success"):
        console.print(f"[red]Prediction failed for {game_info}: {result.get('error')}[/red]")
        return

    # EV Results
    ev_result = result.get("ev_result")
    if ev_result and "error" not in ev_result:
        bets = ev_result.get("bets", [])
        console.print(f"\n[green]EV Calculator - {len(bets)} bets found[/green]")

        if bets:
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("#", width=3)
            table.add_column("Bet", min_width=30)
            table.add_column("Odds", width=8)
            table.add_column("EV%", width=8)

            for i, bet in enumerate(bets[:5], 1):
                table.add_row(
                    str(i),
                    bet.get("bet", bet.get("description", "?")),
                    str(bet.get("odds", "?")),
                    f"+{bet.get('expected_value', bet.get('ev', 0)):.1f}%"
                )
            console.print(table)

    # AI Results
    ai_result = result.get("ai_result")
    if ai_result and "error" not in ai_result:
        picks = ai_result.get("picks", [])
        cost = result.get("total_cost", 0)
        console.print(f"\n[blue]AI Predictor - {len(picks)} picks (${cost:.2f})[/blue]")

        if picks:
            table = Table(show_header=True, header_style="bold blue")
            table.add_column("#", width=3)
            table.add_column("Market", min_width=15)
            table.add_column("Pick", min_width=20)
            table.add_column("Odds", width=8)
            table.add_column("Key Stat", min_width=25)

            for i, pick in enumerate(picks[:5], 1):
                # Handle both old format (bet, expected_value) and new format (market, pick, key_stat)
                market = pick.get("market", pick.get("bet", "?"))
                pick_text = pick.get("pick", "")
                odds = pick.get("odds", "?")
                key_stat = pick.get("key_stat", f"+{pick.get('expected_value', 0):.1f}% EV" if "expected_value" in pick else "")

                table.add_row(
                    str(i),
                    str(market)[:20],
                    str(pick_text)[:25],
                    str(odds),
                    str(key_stat)[:30]
                )
            console.print(table)

    # Comparison
    comparison = result.get("comparison")
    if comparison:
        console.print(f"\n[dim]Agreement: {comparison.get('agreements', 0)} bets, "
                      f"Rate: {comparison.get('agreement_rate', 0):.0%}[/dim]")


# =============================================================================
# Menu Functions
# =============================================================================


def select_sport() -> dict:
    """Display sport selection menu and return selected sport config."""
    console.print()

    # Create sport selection panel
    sport_text = Text()
    sport_text.append("\nSelect Sport:\n\n", style="bold white")

    for key, sport in SPORTS.items():
        sport_text.append(f"{key}. ", style="bold yellow")
        sport_text.append(f"{sport['emoji']}  {sport['name']}\n", style="white")

    console.print(Panel(
        sport_text,
        title=Text("🎯 SPORTS BETTING ANALYSIS 🎯", style="bold cyan", justify="center"),
        border_style="cyan",
        padding=(1, 2)
    ))

    choice = Prompt.ask(
        "\n[bold cyan]Select sport[/bold cyan]",
        choices=list(SPORTS.keys()),
        default="1"
    )

    return SPORTS[choice]


def display_menu(sport_config: dict):
    """Display the main menu with sport-specific formatting."""
    console.print()

    # Create header with sport emoji
    header = Text(
        f"{sport_config['emoji']}  {sport_config['name'].upper()} BETTING ANALYSIS  {sport_config['emoji']}",
        style="bold cyan",
        justify="center"
    )

    # Create menu options
    menu_text = Text()
    menu_text.append("\n1. ", style="bold yellow")
    menu_text.append("Predict Game (AI)\n", style="white")
    menu_text.append("   ", style="dim")
    menu_text.append("[Single game AI prediction ~$0.15]\n", style="dim")
    menu_text.append("2. ", style="bold yellow")
    menu_text.append("EV Calculator Analysis\n", style="white")
    menu_text.append("   ", style="dim")
    menu_text.append("[Statistical EV calculator (FREE)]\n", style="dim")
    menu_text.append("3. ", style="bold yellow")
    menu_text.append("Run Dual Predictions\n", style="white")
    menu_text.append("   ", style="dim")
    menu_text.append("[Run BOTH EV + AI for comparison]\n", style="dim")
    menu_text.append("4. ", style="bold yellow")
    menu_text.append("Predict All Games (AI)\n", style="white")
    menu_text.append("   ", style="dim")
    menu_text.append("[Batch AI predictions for a date]\n", style="dim")
    menu_text.append("5. ", style="bold yellow")
    menu_text.append("Fetch Odds\n", style="white")
    menu_text.append("   ", style="dim")
    menu_text.append("[Scrape DraftKings odds for games]\n", style="dim")
    menu_text.append("6. ", style="bold yellow")
    menu_text.append("Fetch Stats\n", style="white")
    menu_text.append("   ", style="dim")
    menu_text.append("[Scrape FBRef rankings & profiles]\n", style="dim")
    menu_text.append("7. ", style="bold yellow")
    menu_text.append("Fetch Results & Analyze\n", style="white")
    menu_text.append("   ", style="dim")
    menu_text.append("[Get results and calculate P/L]\n", style="dim")
    menu_text.append("8. ", style="bold yellow")
    menu_text.append("View Dashboard\n", style="white")
    menu_text.append("   ", style="dim")
    menu_text.append("[Open Streamlit dashboard]\n", style="dim")
    menu_text.append("9. ", style="bold yellow")
    menu_text.append("Change Sport\n", style="white")
    menu_text.append("0. ", style="bold yellow")
    menu_text.append("Exit\n", style="white")

    # Display in panel
    console.print(Panel(menu_text, title=header, border_style="cyan", padding=(1, 2)))


# =============================================================================
# Menu Option Implementations
# =============================================================================


def run_fetch_odds(orchestrator: CLIOrchestrator):
    """Fetch odds from DraftKings (Menu Option 5)."""
    console.print("\n[bold cyan]Fetch Odds from DraftKings[/bold cyan]")
    console.print("[dim]Fetching upcoming games schedule...[/dim]")

    # Fetch schedule automatically
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Fetching upcoming games...", total=None)
            games = orchestrator.odds_service.fetch_schedule()
    except Exception as e:
        console.print(f"[red]Error fetching schedule: {e}[/red]")
        return

    if not games:
        console.print("[yellow]No upcoming games found[/yellow]")
        return

    # Display games
    console.print(f"\n[bold cyan]Found {len(games)} upcoming games:[/bold cyan]")
    for i, game in enumerate(games, 1):
        start_date = game.get("start_date", "")[:10] if game.get("start_date") else "TBD"
        console.print(f"  {i}. {game.get('matchup', '?')} - {start_date}")

    console.print(f"  A. [bold]All games[/bold]")

    # Select games
    choice = Prompt.ask(
        "\n[cyan]Select games (e.g., '1,2,3' or 'A' for all)[/cyan]",
        default="A"
    )

    # Parse selection
    if choice.upper() == "A":
        selected = games
    else:
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(",")]
            selected = [games[i] for i in indices if 0 <= i < len(games)]
        except (ValueError, IndexError):
            console.print("[yellow]Invalid selection, using all games[/yellow]")
            selected = games

    if not selected:
        console.print("[yellow]No games selected[/yellow]")
        return

    console.print(f"\n[bold]Fetching odds for {len(selected)} game(s)...[/bold]\n")

    # Fetch odds for each selected game
    success_count = 0
    for game in selected:
        matchup = game.get("matchup", "?")
        event_id = game.get("event_id")

        if not event_id:
            console.print(f"[yellow]  Skipping {matchup} - no event ID[/yellow]")
            continue

        console.print(f"[cyan]  Fetching: {matchup}[/cyan]")

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task(f"Fetching odds...", total=None)
                odds_data = orchestrator.odds_service.scraper.fetch_odds_from_api(event_id)

            if odds_data:
                path = orchestrator.odds_service.save_odds(odds_data)
                teams = odds_data.get("teams", {})
                away = teams.get("away", {}).get("name", "?")
                home = teams.get("home", {}).get("name", "?")
                game_date = odds_data.get("game_date", "")[:10]

                console.print(f"    [green]Saved: {away} @ {home} ({game_date})[/green]")
                console.print(f"    [dim]Path: {path}[/dim]")
                success_count += 1
            else:
                console.print(f"    [yellow]No odds data returned[/yellow]")

        except Exception as e:
            console.print(f"    [red]Error: {e}[/red]")

    console.print(f"\n[bold green]Complete! Saved odds for {success_count}/{len(selected)} games[/bold green]")


def run_fetch_stats(orchestrator: CLIOrchestrator):
    """Fetch stats from reference sites for selected teams (Menu Option 6)."""
    # Set source name based on sport
    if orchestrator.sport == "nfl":
        source_name = "Pro-Football-Reference"
    elif orchestrator.sport == "bundesliga":
        source_name = "FBRef"
    else:
        console.print(f"[yellow]Stats fetching not yet implemented for {orchestrator.sport.upper()}[/yellow]")
        return

    console.print(f"\n[bold cyan]Fetch Stats from {source_name}[/bold cyan]")

    console.print("[dim]Fetching upcoming games schedule...[/dim]")

    # Fetch schedule (reuse odds service)
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Fetching upcoming games...", total=None)
            games = orchestrator.odds_service.fetch_schedule()
    except Exception as e:
        console.print(f"[red]Error fetching schedule: {e}[/red]")
        return

    if not games:
        console.print("[yellow]No upcoming games found[/yellow]")
        return

    # Display games
    console.print(f"\n[bold cyan]Found {len(games)} upcoming games:[/bold cyan]")
    for i, game in enumerate(games, 1):
        start_date = game.get("start_date", "")[:10] if game.get("start_date") else "TBD"
        console.print(f"  {i}. {game.get('matchup', '?')} - {start_date}")

    console.print(f"  A. [bold]All games[/bold]")

    # Select games
    choice = Prompt.ask(
        "\n[cyan]Select games (e.g., '1,2,3' or 'A' for all)[/cyan]",
        default="A"
    )

    # Parse selection
    if choice.upper() == "A":
        selected = games
    else:
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(",")]
            selected = [games[i] for i in indices if 0 <= i < len(games)]
        except (ValueError, IndexError):
            console.print("[yellow]Invalid selection, using all games[/yellow]")
            selected = games

    if not selected:
        console.print("[yellow]No games selected[/yellow]")
        return

    # Import team lookup based on sport
    import re
    if orchestrator.sport == "nfl":
        from sports.nfl.teams import find_team_by_abbr as find_nfl_team
    elif orchestrator.sport == "bundesliga":
        from sports.futbol.bundesliga.teams import find_team_by_name as find_bundesliga_team

    # Collect unique teams from selected games
    teams_to_fetch = set()
    for game in selected:
        matchup = game.get("matchup", "")
        away_name, home_name = None, None

        # Parse matchup - handle "Away @ Home" or "Away vs Home"
        if " @ " in matchup:
            away_name, home_name = matchup.split(" @ ", 1)
        elif re.search(r'\s+vs\.?\s+', matchup, re.IGNORECASE):
            # Split on "vs" or "vs." case-insensitive
            parts = re.split(r'\s+vs\.?\s+', matchup, flags=re.IGNORECASE)
            if len(parts) == 2:
                away_name, home_name = parts

        if away_name and home_name:
            teams_to_fetch.add(away_name.strip())
            teams_to_fetch.add(home_name.strip())

    console.print(f"\n[bold]Will fetch stats for {len(teams_to_fetch)} team(s)...[/bold]")

    # Step 1: Fetch rankings (once)
    console.print("\n[cyan]Step 1: Fetching league rankings...[/cyan]")
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(f"Fetching rankings from {source_name}...", total=None)
            rankings = orchestrator.stats_service.fetch_rankings()

        if rankings:
            path = orchestrator.stats_service.save_rankings(rankings)
            tables_data = rankings.get("tables", {})
            table_names = list(tables_data.keys())
            console.print(f"  [green]Saved {len(table_names)} ranking tables[/green]")
            console.print(f"  [dim]Tables: {', '.join(table_names)}[/dim]")
            console.print(f"  [dim]Path: {path}[/dim]")
        else:
            console.print("  [yellow]No rankings data returned[/yellow]")
    except Exception as e:
        console.print(f"  [red]Error fetching rankings: {e}[/red]")

    # Step 2: Fetch team profiles
    console.print(f"\n[cyan]Step 2: Fetching team profiles...[/cyan]")
    success_count = 0

    for team_name in sorted(teams_to_fetch):
        # Resolve team based on sport
        if orchestrator.sport == "nfl":
            team = find_nfl_team(team_name)
            if not team:
                console.print(f"  [yellow]Unknown team: {team_name}[/yellow]")
                continue
            # PFR uses lowercase abbreviations for URLs (e.g., 'atl', 'tam')
            team_id = team["pfr_abbr"]
            # But store profiles by full team name (e.g., 'atlanta_falcons')
            team_slug = team["name"].lower().replace(" ", "_")
            display_name = team["name"]
        elif orchestrator.sport == "bundesliga":
            team = find_bundesliga_team(team_name)
            if not team:
                console.print(f"  [yellow]Unknown team: {team_name}[/yellow]")
                continue
            # FBRef ID for URL (redirects automatically to full URL)
            team_id = team["fbref_id"]
            team_slug = team["slug"]  # Used for folder naming
            display_name = team["name"]
        else:
            console.print(f"  [yellow]Unknown team: {team_name}[/yellow]")
            continue

        console.print(f"  [cyan]Fetching: {display_name}[/cyan]")

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task(f"Fetching {display_name} profile...", total=None)
                profile = orchestrator.stats_service.fetch_team_profile(team_id)

            if profile:
                # Use team slug for folder name
                if orchestrator.sport == "bundesliga":
                    team_slug_clean = team_slug.replace("-Stats", "").lower().replace("-", "_")
                else:
                    # NFL already uses full team name, just ensure lowercase
                    team_slug_clean = team_slug
                path = orchestrator.stats_service.save_team_profile(profile, team_slug_clean)
                tables_data = profile.get("tables", {})
                table_names = list(tables_data.keys())
                console.print(f"    [green]Saved {len(table_names)} table(s): {', '.join(table_names)}[/green]")
                success_count += 1
            else:
                console.print(f"    [yellow]No profile data returned[/yellow]")

        except Exception as e:
            console.print(f"    [red]Error: {e}[/red]")

    console.print(f"\n[bold green]Complete! Fetched profiles for {success_count}/{len(teams_to_fetch)} teams[/bold green]")


def run_ev_calculator(orchestrator: CLIOrchestrator):
    """Run EV Calculator predictions (Menu Option 2)."""
    console.print("\n[bold cyan]EV Calculator Analysis[/bold cyan]")
    console.print("[dim]Free statistical analysis using historical data.[/dim]")

    # Select date
    game_date = select_date(orchestrator, source="odds")
    if not game_date:
        return

    # Get games for date
    games = get_games_for_date(orchestrator, game_date)
    if not games:
        console.print(f"[yellow]No odds found for {game_date}[/yellow]")
        return

    # Select games
    selected = select_games(games)
    if not selected:
        return

    console.print(f"\n[bold]Running EV analysis for {len(selected)} game(s)...[/bold]\n")

    # Get sport config
    sport = SportFactory.create(orchestrator.sport)

    for game in selected:
        away = game["away_team"]
        home = game["home_team"]
        game_info = f"{away} @ {home}"

        console.print(f"[cyan]Processing: {game_info}[/cyan]")

        try:
            # Load odds
            odds = orchestrator.odds_service.load_odds(game_date, home, away)
            if not odds:
                console.print(f"[yellow]  No odds found, skipping[/yellow]")
                continue

            # Run prediction (EV only)
            result = orchestrator.prediction_service.predict_game(
                game_date=game_date,
                away_team=game.get("away_name") or away,
                home_team=game.get("home_name") or home,
                odds=odds,
                run_ev=True,
                run_ai=False,
            )

            display_prediction_results(result, game_info)

            # Save EV prediction
            if result.get("ev_result") and "error" not in result["ev_result"]:
                game_key = f"{home}_{away}".lower()
                orchestrator.prediction_service.save_prediction(
                    result["ev_result"],
                    game_key=game_key,
                    game_date=game_date,
                    prediction_type="ev"
                )
                console.print(f"[dim]  Saved to predictions_ev/[/dim]")

        except Exception as e:
            console.print(f"[red]  Error: {e}[/red]")


def run_ai_prediction(orchestrator: CLIOrchestrator):
    """Run AI predictions for single game (Menu Option 1)."""
    console.print("\n[bold cyan]AI Prediction (Claude)[/bold cyan]")
    console.print("[yellow]Note: AI predictions cost ~$0.10-0.15 per game[/yellow]")

    # Select date
    game_date = select_date(orchestrator, source="odds")
    if not game_date:
        return

    # Get games for date
    games = get_games_for_date(orchestrator, game_date)
    if not games:
        console.print(f"[yellow]No odds found for {game_date}[/yellow]")
        return

    # Select games
    selected = select_games(games)
    if not selected:
        return

    # Confirm cost
    estimated_cost = len(selected) * 0.15
    if not Confirm.ask(f"\n[yellow]Estimated cost: ${estimated_cost:.2f}. Continue?[/yellow]"):
        return

    console.print(f"\n[bold]Running AI predictions for {len(selected)} game(s)...[/bold]\n")

    # Get sport config
    sport = SportFactory.create(orchestrator.sport)
    total_cost = 0.0

    for game in selected:
        away = game["away_team"]
        home = game["home_team"]
        game_info = f"{away} @ {home}"

        console.print(f"[cyan]Processing: {game_info}[/cyan]")

        try:
            # Load odds
            odds = orchestrator.odds_service.load_odds(game_date, home, away)
            if not odds:
                console.print(f"[yellow]  No odds found, skipping[/yellow]")
                continue

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task(f"Calling Claude API...", total=None)

                # Run prediction (AI only)
                # Build odds_dir from raw identifiers (matches folder structure)
                if orchestrator.sport == "bundesliga":
                    odds_dir = f"sports/futbol/bundesliga/data/odds/{game_date}/{home}_{away}".lower()
                else:
                    odds_dir = f"sports/{orchestrator.sport}/data/odds/{game_date}/{home}_{away}".lower()

                result = orchestrator.prediction_service.predict_game(
                    game_date=game_date,
                    away_team=game.get("away_name") or away,
                    home_team=game.get("home_name") or home,
                    odds=odds,
                    run_ev=False,
                    run_ai=True,
                    odds_dir=odds_dir,
                )

            total_cost += result.get("total_cost", 0)
            display_prediction_results(result, game_info)

            # Save AI prediction
            if result.get("ai_result") and "error" not in result["ai_result"]:
                game_key = f"{home}_{away}".lower()
                orchestrator.prediction_service.save_prediction(
                    result["ai_result"],
                    game_key=game_key,
                    game_date=game_date,
                    prediction_type="ai"
                )
                console.print(f"[dim]  Saved to predictions/[/dim]")

        except Exception as e:
            console.print(f"[red]  Error: {e}[/red]")

    console.print(f"\n[bold green]Total API cost: ${total_cost:.2f}[/bold green]")


def run_dual_predictions(orchestrator: CLIOrchestrator):
    """Run both EV and AI predictions (Menu Option 3)."""
    console.print("\n[bold cyan]Dual Predictions (EV + AI)[/bold cyan]")
    console.print("[dim]Run both systems for comparison[/dim]")
    console.print("[yellow]Note: AI predictions cost ~$0.10-0.15 per game[/yellow]")

    # Select date
    game_date = select_date(orchestrator, source="odds")
    if not game_date:
        return

    # Get games for date
    games = get_games_for_date(orchestrator, game_date)
    if not games:
        console.print(f"[yellow]No odds found for {game_date}[/yellow]")
        return

    # Select games
    selected = select_games(games)
    if not selected:
        return

    # Confirm cost
    estimated_cost = len(selected) * 0.15
    if not Confirm.ask(f"\n[yellow]Estimated cost: ${estimated_cost:.2f}. Continue?[/yellow]"):
        return

    console.print(f"\n[bold]Running dual predictions for {len(selected)} game(s)...[/bold]\n")

    # Get sport config
    sport = SportFactory.create(orchestrator.sport)
    total_cost = 0.0

    for game in selected:
        away = game["away_team"]
        home = game["home_team"]
        game_info = f"{away} @ {home}"

        console.print(f"\n[cyan]Processing: {game_info}[/cyan]")

        try:
            # Load odds
            odds = orchestrator.odds_service.load_odds(game_date, home, away)
            if not odds:
                console.print(f"[yellow]  No odds found, skipping[/yellow]")
                continue

            # Build odds_dir from raw identifiers
            if orchestrator.sport == "bundesliga":
                odds_dir = f"sports/futbol/bundesliga/data/odds/{game_date}/{home}_{away}".lower()
            else:
                odds_dir = f"sports/{orchestrator.sport}/data/odds/{game_date}/{home}_{away}".lower()

            # Run EV first (fast)
            console.print("[dim]  Running EV Calculator...[/dim]")
            ev_result = orchestrator.prediction_service.predict_game(
                game_date=game_date,
                away_team=game.get("away_name") or away,
                home_team=game.get("home_name") or home,
                odds=odds,
                run_ev=True,
                run_ai=False,
            )

            # Run AI (slow)
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task(f"Calling Claude API...", total=None)

                ai_result = orchestrator.prediction_service.predict_game(
                    game_date=game_date,
                    away_team=game.get("away_name") or away,
                    home_team=game.get("home_name") or home,
                    odds=odds,
                    run_ev=False,
                    run_ai=True,
                    odds_dir=odds_dir,
                )

            # Combine results
            result = {
                "success": True,
                "ev_result": ev_result.get("ev_result"),
                "ai_result": ai_result.get("ai_result"),
                "total_cost": ai_result.get("total_cost", 0),
            }

            total_cost += result.get("total_cost", 0)
            display_prediction_results(result, game_info)

            # Save both predictions
            game_key = f"{home}_{away}".lower()

            if result.get("ev_result") and "error" not in result["ev_result"]:
                orchestrator.prediction_service.save_prediction(
                    result["ev_result"],
                    game_key=game_key,
                    game_date=game_date,
                    prediction_type="ev"
                )

            if result.get("ai_result") and "error" not in result["ai_result"]:
                orchestrator.prediction_service.save_prediction(
                    result["ai_result"],
                    game_key=game_key,
                    game_date=game_date,
                    prediction_type="ai"
                )

            console.print(f"[dim]  Saved EV and AI predictions[/dim]")

        except Exception as e:
            console.print(f"[red]  Error: {e}[/red]")

    console.print(f"\n[bold green]Total API cost: ${total_cost:.2f}[/bold green]")


def run_batch_ai_predictions(orchestrator: CLIOrchestrator):
    """Run AI predictions for all games on a date (Menu Option 4)."""
    console.print("\n[bold cyan]Batch AI Predictions[/bold cyan]")
    console.print("[dim]Run AI predictions for all games on a date[/dim]")

    # Select date
    game_date = select_date(orchestrator, source="odds")
    if not game_date:
        return

    # Get ALL games for date
    games = get_games_for_date(orchestrator, game_date)
    if not games:
        console.print(f"[yellow]No odds found for {game_date}[/yellow]")
        return

    # Show games and estimate cost
    console.print(f"\n[bold]Found {len(games)} games:[/bold]")
    for game in games:
        console.print(f"  - {game['away_team']} @ {game['home_team']}")

    estimated_cost = len(games) * 0.15
    console.print(f"\n[yellow]Estimated cost: ${estimated_cost:.2f}[/yellow]")

    if not Confirm.ask(f"\nRun AI predictions for all {len(games)} games?"):
        return

    # Use batch prediction
    console.print(f"\n[bold]Starting batch predictions...[/bold]\n")

    def odds_loader(date: str, game: Dict) -> Optional[Dict]:
        return orchestrator.odds_service.load_odds(
            date, game.get("home_team"), game.get("away_team")
        )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Processing {len(games)} games...", total=None)

        result = orchestrator.prediction_service.predict_games_batch(
            game_date=game_date,
            games=games,
            odds_loader=odds_loader,
        )

    # Display summary
    console.print(f"\n[bold green]Batch Complete![/bold green]")
    console.print(f"  Processed: {result.get('games_processed', 0)}")
    console.print(f"  Skipped: {result.get('games_skipped', 0)}")
    console.print(f"  Failed: {result.get('games_failed', 0)}")
    console.print(f"  Total Cost: ${result.get('total_cost', 0):.2f}")

    # Show errors if any
    errors = result.get("errors", [])
    if errors:
        console.print("\n[red]Errors:[/red]")
        for err in errors:
            console.print(f"  - {err.get('game')}: {err.get('error')}")


def run_fetch_results_and_analyze(orchestrator: CLIOrchestrator):
    """Fetch results and run P&L analysis (Menu Option 6)."""
    console.print("\n[bold cyan]Fetch Results & Analyze[/bold cyan]")
    console.print("[dim]Fetch game results and calculate P/L for predictions[/dim]")

    # Select date from predictions (not odds)
    game_date = select_date(orchestrator, source="predictions")
    if not game_date:
        return

    # Get games from predictions folder
    games = get_games_for_date(orchestrator, game_date)
    if not games:
        # Try loading from odds if predictions empty
        games = get_games_for_date(orchestrator, game_date)

    if not games:
        console.print(f"[yellow]No games found for {game_date}[/yellow]")
        return

    selected = select_games(games)
    if not selected:
        return

    console.print(f"\n[bold]Fetching results for {len(selected)} game(s)...[/bold]\n")

    results_fetched = 0
    analyses_completed = 0

    for game in selected:
        away = game["away_team"]
        home = game["home_team"]
        game_info = f"{away} @ {home}"

        console.print(f"[cyan]Processing: {game_info}[/cyan]")

        try:
            # Fetch result from Pro-Football-Reference
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task("Fetching boxscore...", total=None)

                result_data = orchestrator.results_service.fetch_game_result(
                    game_date=game_date,
                    away_team=away,
                    home_team=home,
                )

            if result_data:
                orchestrator.results_service.save_result(
                    result_data, game_date, away, home
                )
                results_fetched += 1

                # Display score
                final_score = result_data.get("final_score", {})
                away_score = final_score.get("away", "?")
                home_score = final_score.get("home", "?")
                console.print(f"  [green]Final: {away} {away_score} - {home_score} {home}[/green]")

                # Run analysis if prediction exists
                try:
                    game_key = f"{home}_{away}".lower()

                    # Try to load EV prediction
                    prediction = orchestrator.prediction_service.load_prediction(
                        game_key=game_key,
                        game_date=game_date,
                        prediction_type="ev"
                    )

                    if prediction:
                        analysis = orchestrator.analysis_service.analyze_game(
                            game_date=game_date,
                            away_team=away,
                            home_team=home,
                            prediction_data=prediction,
                            result_data=result_data,
                        )

                        if analysis:
                            analyses_completed += 1
                            summary = analysis.get("summary", {})
                            profit = summary.get("total_profit", 0)
                            win_rate = summary.get("win_rate", 0)

                            profit_style = "green" if profit > 0 else "red"
                            console.print(f"  [dim]Analysis: ${profit:+.2f} ({win_rate:.0%} win rate)[/dim]")

                except Exception as e:
                    console.print(f"  [dim]No prediction found for analysis[/dim]")

            else:
                console.print(f"  [yellow]No result found (game may not have finished)[/yellow]")

        except Exception as e:
            console.print(f"  [red]Error: {e}[/red]")

    console.print(f"\n[bold green]Complete![/bold green]")
    console.print(f"  Results fetched: {results_fetched}")
    console.print(f"  Analyses completed: {analyses_completed}")


def run_dashboard():
    """Show command to run the Streamlit dashboard."""
    console.print("\n[bold cyan]Streamlit Dashboard[/bold cyan]")
    console.print("\n[white]To start the dashboard, run:[/white]")
    console.print("\n[bold green]  streamlit run frontend/app.py[/bold green]")
    console.print("\n[dim]The dashboard provides full analytics visualization.[/dim]")


# =============================================================================
# Main Entry Point
# =============================================================================


def main():
    """Main CLI entry point with interactive menu."""
    # Clear screen and show welcome
    console.clear()
    console.print("[bold green]Welcome to Multi-Sport Betting Analysis Tool![/bold green]\n")
    console.print("[dim]AI-powered predictions for NFL, NBA, and Bundesliga[/dim]")
    console.print("[dim]Using services architecture[/dim]\n")

    # Select initial sport
    current_sport = select_sport()

    # Create orchestrator for the selected sport
    orchestrator = CLIOrchestrator(sport=current_sport["code"])

    while True:
        display_menu(current_sport)

        # Get user choice with styled prompt
        choice = Prompt.ask(
            "\n[bold cyan]Select option[/bold cyan]",
            choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
            default="2"
        )

        if choice == "1":
            # Predict Game (AI)
            run_ai_prediction(orchestrator)
            Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")

        elif choice == "2":
            # EV Calculator Analysis
            run_ev_calculator(orchestrator)
            Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")

        elif choice == "3":
            # Run Dual Predictions
            run_dual_predictions(orchestrator)
            Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")

        elif choice == "4":
            # Predict All Games (AI Only)
            run_batch_ai_predictions(orchestrator)
            Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")

        elif choice == "5":
            # Fetch Odds
            run_fetch_odds(orchestrator)
            Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")

        elif choice == "6":
            # Fetch Stats
            run_fetch_stats(orchestrator)
            Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")

        elif choice == "7":
            # Fetch Results & Analyze
            run_fetch_results_and_analyze(orchestrator)
            Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")

        elif choice == "8":
            # View Dashboard
            run_dashboard()
            Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")

        elif choice == "9":
            # Change Sport
            current_sport = select_sport()
            orchestrator = CLIOrchestrator(sport=current_sport["code"])

        elif choice == "0":
            # Exit
            console.print("\n[bold green]Exiting... Good luck with your bets! 🎰[/bold green]\n")
            break


if __name__ == "__main__":
    main()
