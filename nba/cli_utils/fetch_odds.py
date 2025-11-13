"""Fetch odds CLI commands for NBA - Refactored with services."""

from datetime import datetime
from pathlib import Path
import inquirer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Import shared services
from shared.services import MetadataService
from shared.repositories import OddsRepository
from shared.utils.console_utils import print_header, print_success, print_cancelled, print_info, print_error
from shared.utils.web_scraper import WebScraper
from shared.utils.timezone_utils import get_eastern_now, iso_to_eastern_date_folder
from shared.utils.odds_formatting import format_odds, format_spread
from shared.utils.odds_display import display_odds_summary
from shared.config import get_metadata_path

# Import NBA specific
from nba.odds_scraper import NBAOddsScraper
from nba.teams import DK_TO_PBR_ABBR

# Initialize services
console = Console()
odds_metadata_service = MetadataService(get_metadata_path("nba", "odds"))
odds_repo = OddsRepository("nba")


def fetch_odds_command():
    """Fetch odds from a DraftKings URL.

    Workflow:
    1. Prompt for DraftKings game URL
    2. Fetch HTML using WebScraper (Playwright)
    3. Extract odds using NBAOddsScraper
    4. Display summary of extracted odds
    5. Save to nba/data/odds/{date}/{home_abbr}_{away_abbr}.json
    """
    print_header("🏀 NBA ODDS FETCHER 🏀")
    console.print()
    console.print("[dim]Fetches betting odds directly from DraftKings URL[/dim]")
    console.print()

    # Prompt for DraftKings URL
    questions = [
        inquirer.Text(
            "dk_url",
            message="Enter DraftKings game URL",
            validate=lambda _, x: len(x.strip()) > 0 and "draftkings.com" in x.lower(),
        )
    ]
    answers = inquirer.prompt(questions)

    if not answers:
        print_cancelled()
        return

    dk_url = answers["dk_url"].strip()

    try:
        # Fetch HTML from URL
        console.print()
        print_info("🌐 Fetching DraftKings page...")

        scraper = WebScraper(headless=True, timeout=30000)
        with scraper.launch() as page:
            scraper.navigate_and_wait(page, dk_url, wait_time=3000)
            html_content = page.content()

        print_success("Page fetched successfully")

        # Save HTML to temp file for odds scraper
        temp_html_path = Path("nba/data/odds") / "temp_dk_page.html"
        temp_html_path.parent.mkdir(parents=True, exist_ok=True)
        temp_html_path.write_text(html_content, encoding='utf-8')

        # Extract odds
        console.print()
        print_info("📊 Extracting odds from page...")

        odds_scraper = NBAOddsScraper()
        odds_data = odds_scraper.extract_odds(str(temp_html_path))

        # Clean up temp file
        temp_html_path.unlink()

        # Display summary
        display_odds_summary(odds_data, console)

        # Save to file using repository
        save_odds_to_json(odds_data)

        console.print()
        console.print(Panel.fit(
            "[bold green]✅ Odds extracted successfully![/bold green]",
            border_style="green"
        ))

    except Exception as e:
        console.print()
        print_error(f"Error fetching odds: {str(e)}")
        console.print()
        console.print(Panel(
            f"[red]Failed to fetch odds from URL[/red]\n\n"
            f"[dim]Error details:[/dim]\n{str(e)}\n\n"
            f"[yellow]Please check:[/yellow]\n"
            f"• URL is valid and contains 'draftkings.com'\n"
            f"• URL points to a specific game page\n"
            f"• You have internet connection",
            title="[bold red]❌ Error ❌[/bold red]",
            border_style="red",
            padding=(1, 2)
        ))


def save_odds_to_json(odds_data: dict):
    """Save odds data to JSON file using repository.

    Uses PFR lowercase abbreviations for consistency with predictions format.

    Args:
        odds_data: Extracted odds dictionary
    """
    # Extract DraftKings team abbreviations
    dk_away_abbr = odds_data["teams"]["away"]["abbr"]
    dk_home_abbr = odds_data["teams"]["home"]["abbr"]

    # Convert DraftKings abbreviations to PFR abbreviations (lowercase)
    try:
        pfr_away_abbr = DK_TO_PFR_ABBR[dk_away_abbr]
        pfr_home_abbr = DK_TO_PFR_ABBR[dk_home_abbr]
    except KeyError as e:
        console.print(f"[yellow]Warning: Unknown DraftKings abbreviation: {e}[/yellow]")
        # Fallback to lowercase DK abbreviations
        pfr_away_abbr = dk_away_abbr.lower()
        pfr_home_abbr = dk_home_abbr.lower()

    # Parse date from ISO format and convert to Eastern time
    game_date_str = odds_data.get("game_date", "")
    try:
        date_folder = iso_to_eastern_date_folder(game_date_str)
    except (ValueError, AttributeError):
        # Fallback to today's date in Eastern time if parsing fails
        date_folder = get_eastern_now().strftime("%Y-%m-%d")

    # Check if this game was already scraped today (duplicate prevention)
    game_key = f"{date_folder}_{pfr_home_abbr}_{pfr_away_abbr}"
    metadata = odds_metadata_service.load_metadata()

    if game_key in metadata:
        existing_entry = metadata[game_key]
        fetched_at_str = existing_entry.get("fetched_at", "")

        # Check if fetched today (using Eastern time)
        try:
            fetched_at = datetime.fromisoformat(fetched_at_str)
            today_str = get_eastern_now().strftime("%Y-%m-%d")
            fetched_date_str = fetched_at.strftime("%Y-%m-%d")

            if fetched_date_str == today_str:
                # Already scraped today - show warning and skip save
                console.print()
                console.print(Panel(
                    f"[yellow]⚠ Odds already fetched today![/yellow]\n\n"
                    f"Game: {pfr_away_abbr.upper()} @ {pfr_home_abbr.upper()}\n"
                    f"Game Date: {date_folder}\n"
                    f"Fetched at: {fetched_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"File: {existing_entry['filepath']}\n\n"
                    f"[dim]Using existing odds data to avoid duplicate scraping.[/dim]",
                    title="[bold yellow]Already Scraped[/bold yellow]",
                    border_style="yellow",
                    padding=(1, 2)
                ))
                return  # Skip saving
        except (ValueError, AttributeError):
            # If we can't parse the date, proceed with save
            pass

    # Update team abbreviations in odds data to use PFR format
    odds_data["teams"]["away"]["pfr_abbr"] = pfr_away_abbr
    odds_data["teams"]["home"]["pfr_abbr"] = pfr_home_abbr

    # Fix team references in player props (replace AWAY/HOME with PFR abbrs)
    for player in odds_data.get("player_props", []):
        if player.get("team") == "AWAY":
            player["team"] = pfr_away_abbr
        elif player.get("team") == "HOME":
            player["team"] = pfr_home_abbr

    # Save using repository
    odds_repo.save_odds(date_folder, pfr_away_abbr, pfr_home_abbr, odds_data)

    # Update metadata using service (with Eastern time)
    filepath = f"nba/data/odds/{date_folder}/{pfr_home_abbr}_{pfr_away_abbr}.json"
    metadata[game_key] = {
        "fetched_at": get_eastern_now().isoformat(),
        "game_date": date_folder,
        "home_team_abbr": pfr_home_abbr,
        "away_team_abbr": pfr_away_abbr,
        "source": "draftkings",
        "filepath": filepath
    }
    odds_metadata_service.save_metadata(metadata)

    console.print()
    print_success(f"Saved to: {filepath}")
    console.print(f"[dim]Format: {{home}}_{{away}} = {pfr_home_abbr}_{pfr_away_abbr}[/dim]")
