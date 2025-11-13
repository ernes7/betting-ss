"""Shared utilities for displaying odds information."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from shared.utils.odds_formatting import format_odds, format_spread


def display_odds_summary(odds_data: dict, console: Console):
    """Display a summary of extracted odds.

    Args:
        odds_data: Extracted odds dictionary
        console: Rich Console instance for output
    """
    console.print()
    console.print("[bold]═" * 40 + "[/bold]")

    # Game info
    away_team = odds_data["teams"]["away"]
    home_team = odds_data["teams"]["home"]
    game_date = odds_data.get("game_date", "Unknown")

    console.print()
    console.print(Panel.fit(
        f"[bold cyan]{away_team['name']} @ {home_team['name']}[/bold cyan]\n"
        f"[dim]{game_date}[/dim]",
        border_style="cyan"
    ))

    # Game lines table
    if odds_data.get("game_lines"):
        console.print()
        console.print("[bold]GAME LINES[/bold]")

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Market", style="cyan")
        table.add_column(away_team["abbr"], justify="right")
        table.add_column(home_team["abbr"], justify="right")

        game_lines = odds_data["game_lines"]

        # Moneyline
        if "moneyline" in game_lines:
            ml = game_lines["moneyline"]
            table.add_row(
                "Moneyline",
                format_odds(ml.get("away")),
                format_odds(ml.get("home"))
            )

        # Spread
        if "spread" in game_lines:
            spread = game_lines["spread"]
            away_spread = f"{format_spread(spread.get('away'))} ({format_odds(spread.get('away_odds'))})"
            home_spread = f"{format_spread(spread.get('home'))} ({format_odds(spread.get('home_odds'))})"
            table.add_row("Spread", away_spread, home_spread)

        # Total
        if "total" in game_lines:
            total = game_lines["total"]
            line = total.get("line")
            table.add_row(
                f"Total ({line})",
                f"O {format_odds(total.get('over'))}",
                f"U {format_odds(total.get('under'))}"
            )

        console.print(table)

    # Player props summary
    if odds_data.get("player_props"):
        player_props = odds_data["player_props"]
        console.print()
        console.print(f"[bold]PLAYER PROPS[/bold] ([cyan]{len(player_props)} players[/cyan])")

        # Group by team
        away_players = [p for p in player_props if p.get("team") == "AWAY"]
        home_players = [p for p in player_props if p.get("team") == "HOME"]

        # Display counts by category
        prop_types = {}
        for player in player_props:
            for prop in player.get("props", []):
                market = prop.get("market", "unknown")
                prop_types[market] = prop_types.get(market, 0) + 1

        console.print()
        console.print("[dim]Markets available:[/dim]")
        for market, count in sorted(prop_types.items()):
            market_display = market.replace("_", " ").title()
            console.print(f"  • {market_display}: {count} player(s)")

        # Show sample players with milestone details
        console.print()
        console.print("[dim]Sample players:[/dim]")
        for player in player_props[:5]:  # Show first 5 players
            prop_count = len(player.get("props", []))
            player_display = f"  • {player['player']}: {prop_count} prop(s)"

            # Show milestone ranges for first prop with milestones
            for prop in player.get("props", []):
                if "milestones" in prop and prop["milestones"]:
                    milestones = prop["milestones"]
                    market_name = prop["market"].replace("_", " ").title()
                    min_line = milestones[0]["line"]
                    max_line = milestones[-1]["line"]
                    milestone_count = len(milestones)
                    player_display += f" [{market_name}: {milestone_count} lines from {min_line}+ to {max_line}+]"
                    break

            console.print(player_display)

        if len(player_props) > 5:
            console.print(f"  [dim]... and {len(player_props) - 5} more[/dim]")

    console.print()
    console.print("[bold]═" * 40 + "[/bold]")
