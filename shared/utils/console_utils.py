"""Console utilities for consistent CLI formatting.

This module provides reusable Rich console formatting functions
to ensure consistent output across all CLI commands.
"""

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import Optional


# Global console instance
console = Console()


def print_header(title: str, style: str = "cyan") -> None:
    """Print a formatted header panel.

    Args:
        title: Header text to display
        style: Border style color (default: cyan)
    """
    console.print()
    console.print(Panel.fit(
        f"[bold {style}]{title}[/bold {style}]",
        border_style=style
    ))


def print_section(title: str, style: str = "bold cyan") -> None:
    """Print a section header.

    Args:
        title: Section title
        style: Text style (default: bold cyan)
    """
    console.print()
    console.print(f"[{style}]{title}[/{style}]")


def print_success(message: str, prefix: str = "✓") -> None:
    """Print a success message.

    Args:
        message: Success message text
        prefix: Prefix symbol (default: ✓)
    """
    console.print(f"  [green]{prefix} {message}[/green]")


def print_error(message: str, prefix: str = "✗") -> None:
    """Print an error message.

    Args:
        message: Error message text
        prefix: Prefix symbol (default: ✗)
    """
    console.print(f"  [red]{prefix} {message}[/red]")


def print_warning(message: str, prefix: str = "⚠") -> None:
    """Print a warning message.

    Args:
        message: Warning message text
        prefix: Prefix symbol (default: ⚠)
    """
    console.print(f"  [yellow]{prefix} {message}[/yellow]")


def print_info(message: str) -> None:
    """Print an info message.

    Args:
        message: Info message text
    """
    console.print(f"  [cyan]{message}[/cyan]")


def print_dim(message: str) -> None:
    """Print a dimmed message.

    Args:
        message: Message text
    """
    console.print(f"  [dim]{message}[/dim]")


def print_cost_info(
    cost: float,
    input_tokens: int,
    output_tokens: int,
    total_tokens: int
) -> None:
    """Print API cost information in a formatted way.

    Args:
        cost: Total cost in dollars
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        total_tokens: Total tokens used
    """
    from shared.config import format_cost_display

    console.print()
    console.print("[bold]API Usage:[/bold]")
    console.print(f"  Cost: {format_cost_display(cost)}")
    console.print(f"  Tokens: {total_tokens:,} (input: {input_tokens:,}, output: {output_tokens:,})")


def print_markdown(markdown_text: str) -> None:
    """Print markdown-formatted text.

    Args:
        markdown_text: Markdown text to render
    """
    console.print(Markdown(markdown_text))


def print_prediction_summary(
    team_a: str,
    team_b: str,
    home_team: str,
    game_date: str,
    num_parlays: Optional[int] = None,
    num_bets: Optional[int] = None
) -> None:
    """Print a formatted prediction summary.

    Args:
        team_a: First team name
        team_b: Second team name
        home_team: Home team name
        game_date: Game date
        num_parlays: Number of parlays generated (optional)
        num_bets: Number of EV+ bets generated (optional)
    """
    console.print()
    console.print("[bold cyan]═══ Game Summary ═══[/bold cyan]")
    console.print(f"  Away: {team_a if team_a != home_team else team_b}")
    console.print(f"  Home: {home_team}")
    console.print(f"  Date: {game_date}")

    if num_parlays is not None:
        console.print(f"  Parlays Generated: {num_parlays}")
    if num_bets is not None:
        console.print(f"  EV+ Bets Generated: {num_bets}")


def create_spinner_progress(text: str = "Processing..."):
    """Create a progress spinner with text.

    Args:
        text: Progress text to display

    Returns:
        Progress context manager
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True
    )


def print_divider(char: str = "─", length: int = 60) -> None:
    """Print a divider line.

    Args:
        char: Character to use for divider
        length: Length of divider line
    """
    console.print(f"[dim]{char * length}[/dim]")


def print_cancelled() -> None:
    """Print a cancellation message."""
    console.print("[yellow]Selection cancelled.[/yellow]")


def print_file_saved(filepath: str, file_type: str = "File") -> None:
    """Print a file saved message.

    Args:
        filepath: Path to saved file
        file_type: Type of file (e.g., "Prediction", "Analysis")
    """
    print_success(f"{file_type} saved: {filepath}")


def print_loading_message(item: str) -> None:
    """Print a loading message.

    Args:
        item: Item being loaded (e.g., "profiles", "odds")
    """
    print_info(f"Loading {item}...")
