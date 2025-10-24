"""NFL Stats CLI

Interactive menu-based interface for extracting NFL stats and making predictions.
"""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

from cli_utils.predict import predict_game

# Initialize Rich console
console = Console()


def display_menu():
    """Display the main menu with rich formatting."""
    console.print()

    # Create header with football emoji
    header = Text("🏈  NFL BETTING ANALYSIS TOOL  🏈", style="bold cyan", justify="center")

    # Create menu options
    menu_text = Text()
    menu_text.append("\n1. ", style="bold yellow")
    menu_text.append("Predict Game\n", style="white")
    menu_text.append("2. ", style="bold yellow")
    menu_text.append("Exit\n", style="white")

    # Display in panel
    console.print(Panel(menu_text, title=header, border_style="cyan", padding=(1, 2)))


def main():
    """Main CLI entry point with interactive menu."""
    # Clear screen and show welcome
    console.clear()
    console.print("[bold green]Welcome to NFL Betting Analysis Tool![/bold green]\n")
    console.print("[dim]All data is automatically fetched when generating predictions.[/dim]\n")

    while True:
        display_menu()

        # Get user choice with styled prompt
        choice = Prompt.ask(
            "\n[bold cyan]Select option[/bold cyan]",
            choices=["1", "2"],
            default="1"
        )

        if choice == "1":
            predict_game()
            Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")

        elif choice == "2":
            console.print("\n[bold green]Exiting... Good luck with your bets! 🎰[/bold green]\n")
            break


if __name__ == "__main__":
    main()
