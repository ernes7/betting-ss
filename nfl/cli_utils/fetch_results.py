"""Fetch results CLI commands for NFL."""

from datetime import date

import inquirer
from rich.console import Console
from rich.panel import Panel

# Initialize Rich console
console = Console()


def fetch_results():
    """Fetch results for all NFL games on a specific date.

    This is a placeholder implementation. Full functionality will be added in future phase.

    Workflow:
    1. Prompt for date (default to today)
    2. Load predictions metadata
    3. Filter games by date where results_fetched = false
    4. Display count of games to fetch
    5. Confirm with user
    6. Use ResultsFetcher to fetch results from Pro-Football-Reference
    7. Save results to nfl/results/{date}/{game}.json
    8. Update predictions metadata: results_fetched = true
    9. Display summary (success/failed counts)
    """
    console.print()
    console.print(Panel.fit(
        "[bold cyan]📊 NFL RESULTS FETCHER 📊[/bold cyan]",
        border_style="cyan"
    ))

    # Ask for date (default to today)
    today = date.today().isoformat()
    date_questions = [
        inquirer.Text(
            "game_date",
            message=f"Enter date to fetch results (YYYY-MM-DD) [default: {today}]",
            default=today,
            validate=lambda _, x: len(x.split("-")) == 3 and all(p.isdigit() for p in x.split("-")),
        ),
    ]
    date_answers = inquirer.prompt(date_questions)
    if not date_answers:
        console.print("[yellow]Selection cancelled.[/yellow]")
        return

    target_date = date_answers["game_date"]

    # Placeholder message
    console.print()
    console.print(Panel(
        f"[yellow]Results fetching not yet implemented[/yellow]\n\n"
        f"Target date: {target_date}\n\n"
        f"[dim]This feature will fetch game results from Pro-Football-Reference\n"
        f"and save them to nfl/results/{target_date}/[/dim]",
        title="[bold yellow]⚠ Coming Soon ⚠[/bold yellow]",
        border_style="yellow",
        padding=(1, 2)
    ))
