"""Multi-Sport Betting Analysis CLI

Interactive menu-based interface for generating betting predictions across multiple sports.
"""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

from nfl.cli_utils.predict import predict_game as nfl_predict_game, predict_all_games as nfl_predict_all_games
from nfl.cli_utils.fetch_odds import fetch_odds_command as nfl_fetch_odds
from nfl.cli_utils.fetch_results import fetch_results as nfl_fetch_results
from nba.cli_utils.fetch_odds import fetch_odds_command as nba_fetch_odds

# Initialize Rich console
console = Console()

# Sport configurations
SPORTS = {
    "1": {
        "name": "NFL",
        "emoji": "🏈",
        "predict_fn": nfl_predict_game,
        "predict_all_fn": nfl_predict_all_games,
        "fetch_odds_fn": nfl_fetch_odds,
        "fetch_results_fn": nfl_fetch_results,
    },
    "2": {
        "name": "NBA",
        "emoji": "🏀",
        "predict_fn": None,  # NBA not yet implemented for EV betting
        "predict_all_fn": None,  # NBA not yet implemented for EV betting
        "fetch_odds_fn": nba_fetch_odds,
        "fetch_results_fn": None,  # NBA not yet implemented for EV betting
    },
}


def select_sport():
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


def display_menu(sport_config):
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
    menu_text.append("Predict Game\n", style="white")
    menu_text.append("   ", style="dim")
    menu_text.append("[Single game EV+ analysis]\n", style="dim")
    menu_text.append("2. ", style="bold yellow")
    menu_text.append("Predict All Games (Batch)\n", style="white")
    menu_text.append("   ", style="dim")
    menu_text.append("[Predict all games for a date automatically]\n", style="dim")
    menu_text.append("3. ", style="bold yellow")
    menu_text.append("Fetch Odds\n", style="white")
    menu_text.append("   ", style="dim")
    menu_text.append("[Fetch betting odds from DraftKings]\n", style="dim")
    menu_text.append("4. ", style="bold yellow")
    menu_text.append("Fetch Results\n", style="white")
    menu_text.append("   ", style="dim")
    menu_text.append("[Calculate P/L with EV analysis]\n", style="dim")
    menu_text.append("5. ", style="bold yellow")
    menu_text.append("Change Sport\n", style="white")
    menu_text.append("6. ", style="bold yellow")
    menu_text.append("Exit\n", style="white")

    # Display in panel
    console.print(Panel(menu_text, title=header, border_style="cyan", padding=(1, 2)))


def main():
    """Main CLI entry point with interactive menu."""
    # Clear screen and show welcome
    console.clear()
    console.print("[bold green]Welcome to Multi-Sport Betting Analysis Tool![/bold green]\n")
    console.print("[dim]AI-powered predictions for NFL and NBA[/dim]\n")

    # Select initial sport
    current_sport = select_sport()

    while True:
        display_menu(current_sport)

        # Get user choice with styled prompt
        choice = Prompt.ask(
            "\n[bold cyan]Select option[/bold cyan]",
            choices=["1", "2", "3", "4", "5", "6"],
            default="1"
        )

        if choice == "1":
            # Predict Game
            if current_sport["predict_fn"]:
                current_sport["predict_fn"]()
            else:
                console.print("\n[yellow]⚠ Predictions not yet available for this sport[/yellow]")
                console.print("[dim]Currently only NFL is supported[/dim]")
            Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")

        elif choice == "2":
            # Predict All Games (Batch)
            if current_sport.get("predict_all_fn"):
                current_sport["predict_all_fn"]()
            else:
                console.print("\n[yellow]⚠ Batch predictions not yet available for this sport[/yellow]")
                console.print("[dim]Currently only NFL is supported[/dim]")
            Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")

        elif choice == "3":
            # Fetch Odds
            current_sport["fetch_odds_fn"]()
            Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")

        elif choice == "4":
            # Fetch Results
            if current_sport["fetch_results_fn"]:
                current_sport["fetch_results_fn"]()
            else:
                console.print("\n[yellow]⚠ Results fetching not yet available for this sport[/yellow]")
                console.print("[dim]Currently only NFL is supported[/dim]")
            Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")

        elif choice == "5":
            # Change Sport
            current_sport = select_sport()

        elif choice == "6":
            # Exit
            console.print("\n[bold green]Exiting... Good luck with your bets! 🎰[/bold green]\n")
            break


if __name__ == "__main__":
    main()
