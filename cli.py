"""Multi-Sport Betting Analysis CLI

Interactive menu-based interface for generating betting predictions across multiple sports.
"""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

from nfl.cli_utils.predict import predict_game as nfl_predict_game
from nfl.cli_utils.predict_ev_singles import predict_ev_singles as nfl_predict_ev_singles
from nba.cli_utils.predict import predict_game as nba_predict_game
from nfl.cli_utils.fetch_results import fetch_results as nfl_fetch_results, fetch_ev_results as nfl_fetch_ev_results
from nba.cli_utils.fetch_results import fetch_results as nba_fetch_results

# Initialize Rich console
console = Console()

# Sport configurations
SPORTS = {
    "1": {
        "name": "NFL",
        "emoji": "🏈",
        "predict_fn": nfl_predict_game,
        "predict_ev_fn": nfl_predict_ev_singles,
        "fetch_results_fn": nfl_fetch_results,
        "fetch_ev_results_fn": nfl_fetch_ev_results,
    },
    "2": {
        "name": "NBA",
        "emoji": "🏀",
        "predict_fn": nba_predict_game,
        "predict_ev_fn": None,  # NBA doesn't have EV singles yet
        "fetch_results_fn": nba_fetch_results,
        "fetch_ev_results_fn": None,  # NBA doesn't have EV singles yet
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
    menu_text.append("Predict Game (Parlays)\n", style="white")

    # Show EV+ Singles option for NFL only
    if sport_config.get("predict_ev_fn"):
        menu_text.append("2. ", style="bold yellow")
        menu_text.append("Predict Game (EV+ Singles)\n", style="white")
        menu_text.append("   ", style="dim")
        menu_text.append("[Expected Value analysis with Kelly Criterion]\n", style="dim")
        menu_text.append("3. ", style="bold yellow")
        menu_text.append("Fetch Results (Parlays)\n", style="white")
        menu_text.append("4. ", style="bold yellow")
        menu_text.append("Fetch Results (EV+ Singles)\n", style="white")
        menu_text.append("   ", style="dim")
        menu_text.append("[Calculate P/L with fixed bet amount]\n", style="dim")
        menu_text.append("5. ", style="bold yellow")
        menu_text.append("Change Sport\n", style="white")
        menu_text.append("6. ", style="bold yellow")
        menu_text.append("Exit\n", style="white")
    else:
        menu_text.append("2. ", style="bold yellow")
        menu_text.append("Fetch Results\n", style="white")
        menu_text.append("3. ", style="bold yellow")
        menu_text.append("Change Sport\n", style="white")
        menu_text.append("4. ", style="bold yellow")
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

        # Dynamic choices based on sport features
        if current_sport.get("predict_ev_fn"):
            choices = ["1", "2", "3", "4", "5", "6"]
        else:
            choices = ["1", "2", "3", "4"]

        # Get user choice with styled prompt
        choice = Prompt.ask(
            "\n[bold cyan]Select option[/bold cyan]",
            choices=choices,
            default="1"
        )

        if choice == "1":
            # Predict Game (Parlays)
            current_sport["predict_fn"]()
            Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")

        elif choice == "2":
            # Handle option 2 based on sport
            if current_sport.get("predict_ev_fn"):
                # NFL: Predict Game (EV+ Singles)
                current_sport["predict_ev_fn"]()
                Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")
            else:
                # NBA: Fetch Results
                current_sport["fetch_results_fn"]()
                Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")

        elif choice == "3":
            # Handle option 3 based on sport
            if current_sport.get("predict_ev_fn"):
                # NFL: Fetch Results (Parlays)
                current_sport["fetch_results_fn"]()
                Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")
            else:
                # NBA: Change Sport
                current_sport = select_sport()

        elif choice == "4":
            # Handle option 4 based on sport
            if current_sport.get("predict_ev_fn"):
                # NFL: Fetch Results (EV+ Singles)
                current_sport["fetch_ev_results_fn"]()
                Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")
            else:
                # NBA: Exit
                console.print("\n[bold green]Exiting... Good luck with your bets! 🎰[/bold green]\n")
                break

        elif choice == "5":
            # NFL only: Change Sport
            current_sport = select_sport()

        elif choice == "6":
            # NFL only: Exit
            console.print("\n[bold green]Exiting... Good luck with your bets! 🎰[/bold green]\n")
            break


if __name__ == "__main__":
    main()
