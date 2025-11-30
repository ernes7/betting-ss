"""Aggregate stats CLI handler for NFL predictions."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from shared.utils.aggregate_stats import AggregateStats

console = Console()


def show_aggregate_stats():
    """Display aggregate performance across all analyzed games."""
    console.print()
    console.print(Panel.fit(
        "[bold cyan]NFL Prediction Performance Summary[/bold cyan]",
        border_style="cyan"
    ))
    console.print()

    # Calculate aggregate stats
    stats = AggregateStats("nfl")
    result = stats.calculate_aggregate()

    games = result["games_analyzed"]
    ai = result["ai_system"]
    ev = result["ev_system"]
    comparison = result["comparison"]
    by_type = result["by_bet_type"]

    if games == 0:
        console.print("[yellow]No analyzed games found.[/yellow]")
        console.print("Run 'fetch_results' first to analyze predictions.")
        return

    console.print(f"[bold]Games Analyzed:[/bold] {games}")
    console.print()

    # Create comparison table
    table = Table(title="System Performance", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="dim", width=16)
    table.add_column("AI System", justify="right", style="cyan", width=14)
    table.add_column("EV System", justify="right", style="yellow", width=14)

    table.add_row("Total Bets", str(ai["total_bets"]), str(ev["total_bets"]))
    table.add_row("Wins", str(ai["bets_won"]), str(ev["bets_won"]))
    table.add_row("Losses", str(ai["bets_lost"]), str(ev["bets_lost"]))
    table.add_row(
        "Hit Rate",
        f"{ai['hit_rate']:.1f}%",
        f"{ev['hit_rate']:.1f}%"
    )
    table.add_row(
        "Total P&L",
        _format_profit(ai["total_profit"]),
        _format_profit(ev["total_profit"])
    )
    table.add_row(
        "ROI",
        _format_roi(ai["roi_percent"]),
        _format_roi(ev["roi_percent"])
    )
    table.add_row(
        "Avg Pred EV",
        f"{ai['avg_predicted_ev']:.1f}%",
        f"{ev['avg_predicted_ev']:.1f}%"
    )

    console.print(table)
    console.print()

    # Bet type breakdown
    if by_type:
        type_table = Table(title="Hit Rate by Bet Type", show_header=True, header_style="bold green")
        type_table.add_column("Bet Type", style="dim", width=14)
        type_table.add_column("AI Hit Rate", justify="right", width=14)
        type_table.add_column("EV Hit Rate", justify="right", width=14)

        # Sort by AI total bets descending
        sorted_types = sorted(
            by_type.items(),
            key=lambda x: x[1]["ai_total"],
            reverse=True
        )

        for bet_type, stats in sorted_types:
            ai_rate = f"{stats['ai_hit_rate']:.1f}% ({stats['ai_wins']}/{stats['ai_total']})"
            ev_rate = f"{stats['ev_hit_rate']:.1f}% ({stats['ev_wins']}/{stats['ev_total']})"
            type_table.add_row(bet_type, ai_rate, ev_rate)

        console.print(type_table)
        console.print()

    # Winner banner
    better = comparison["better_system"].upper()
    advantage = comparison["roi_advantage"]

    if better == "AI":
        winner_style = "bold cyan"
        loser = "EV"
    else:
        winner_style = "bold yellow"
        loser = "AI"

    console.print(Panel.fit(
        f"[{winner_style}]WINNER: {better} System[/{winner_style}]\n"
        f"[dim]+{advantage:.1f}% ROI advantage over {loser}[/dim]\n\n"
        f"[dim]Games won - AI: {comparison['games_ai_won']} | EV: {comparison['games_ev_won']} | Tied: {comparison['games_tied']}[/dim]",
        border_style="green"
    ))
    console.print()


def _format_profit(profit: float) -> str:
    """Format profit with color coding."""
    if profit >= 0:
        return f"[green]+${profit:,.2f}[/green]"
    else:
        return f"[red]-${abs(profit):,.2f}[/red]"


def _format_roi(roi: float) -> str:
    """Format ROI with color coding."""
    if roi >= 0:
        return f"[green]+{roi:.1f}%[/green]"
    else:
        return f"[red]{roi:.1f}%[/red]"


if __name__ == "__main__":
    show_aggregate_stats()
