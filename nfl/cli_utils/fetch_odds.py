"""Fetch odds CLI commands for NFL - Refactored with services."""

from datetime import datetime
from pathlib import Path
import inquirer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from bs4 import BeautifulSoup
import time
import random
import re
from collections import defaultdict

# Import shared services
from shared.services import MetadataService
from shared.repositories import OddsRepository
from shared.utils.console_utils import print_header, print_success, print_cancelled, print_info, print_error, print_warning
from shared.utils.web_scraper import WebScraper
from shared.utils.timezone_utils import get_eastern_now, iso_to_eastern_date_folder, EASTERN_TZ
from shared.utils.odds_formatting import format_odds, format_spread
from shared.utils.odds_display import display_odds_summary
from shared.config import get_metadata_path

# Import NFL specific
from nfl.odds_scraper import NFLOddsScraper
from nfl.teams import DK_TO_PFR_ABBR, TEAMS
import json

# Initialize services
console = Console()
odds_metadata_service = MetadataService(get_metadata_path("nfl", "odds"))
odds_repo = OddsRepository("nfl")

# Build DK abbreviation to team info lookup for schedule generation
DK_ABBR_TO_TEAM = {team["abbreviation"]: team for team in TEAMS}


def scrape_draftkings_schedule():
    """Scrape DraftKings NFL schedule page to get HTML content.

    Returns:
        str: HTML content of the schedule page

    Raises:
        Exception: If unable to fetch the page
    """
    dk_schedule_url = "https://sportsbook.draftkings.com/leagues/football/nfl"

    scraper = WebScraper(headless=True, timeout=30000)
    with scraper.launch() as page:
        scraper.navigate_and_wait(page, dk_schedule_url, wait_time=3000)
        html_content = page.content()

    return html_content


def parse_dk_time_string(time_str: str, reference_date: datetime = None) -> datetime | None:
    """Parse DraftKings time strings to datetime objects.

    Args:
        time_str: Time string like "Today 1:00 PM", "Tomorrow 8:15 PM", etc.
        reference_date: Reference date for "Today" (defaults to now in Eastern time)

    Returns:
        datetime object representing game start time, or None if parsing fails
    """
    if reference_date is None:
        reference_date = get_eastern_now()

    time_str = time_str.strip()

    # Pattern 1: "Today HH:MM AM/PM"
    if time_str.startswith("Today"):
        match = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM)', time_str)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            am_pm = match.group(3)

            # Convert to 24-hour format
            if am_pm == "PM" and hour != 12:
                hour += 12
            elif am_pm == "AM" and hour == 12:
                hour = 0

            # Return timezone-aware datetime
            return reference_date.replace(hour=hour, minute=minute, second=0, microsecond=0, tzinfo=EASTERN_TZ)

    # Pattern 2: "Tomorrow HH:MM AM/PM"
    elif time_str.startswith("Tomorrow"):
        match = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM)', time_str)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            am_pm = match.group(3)

            if am_pm == "PM" and hour != 12:
                hour += 12
            elif am_pm == "AM" and hour == 12:
                hour = 0

            from datetime import timedelta
            tomorrow = reference_date + timedelta(days=1)
            # Return timezone-aware datetime
            return tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0, tzinfo=EASTERN_TZ)

    # Pattern 3: "Day Mon DDth HH:MM AM/PM" (e.g., "Thu Nov 13th 8:15 PM")
    else:
        match = re.search(r'(\w{3})\s+(\w{3})\s+(\d{1,2})\w*\s+(\d{1,2}):(\d{2})\s*(AM|PM)', time_str)
        if match:
            month_str = match.group(2)
            day = int(match.group(3))
            hour = int(match.group(4))
            minute = int(match.group(5))
            am_pm = match.group(6)

            if am_pm == "PM" and hour != 12:
                hour += 12
            elif am_pm == "AM" and hour == 12:
                hour = 0

            # Parse month name to month number
            month_map = {
                'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
            }
            month = month_map.get(month_str)

            if month:
                # Use current year, but if the month/day has passed, use next year
                year = reference_date.year
                game_date = datetime(year, month, day, hour, minute, 0, 0, tzinfo=EASTERN_TZ)

                # Need to compare with reference_date (timezone-aware)
                if game_date < reference_date:
                    game_date = datetime(year + 1, month, day, hour, minute, 0, 0, tzinfo=EASTERN_TZ)

                return game_date

    return None  # Could not parse


def parse_todays_game_links(html_content: str) -> list[dict]:
    """Parse DraftKings schedule HTML to extract game URLs and metadata.

    Args:
        html_content: HTML content from DraftKings schedule page

    Returns:
        List of dicts with game info:
        [
            {
                'url': 'https://sportsbook.draftkings.com/event/...',
                'slug': 'atl-falcons-%40-ind-colts',
                'event_id': '32225651',
                'teams_display': 'ATL @ IND',
                'start_time_str': 'Today 1:00 PM',
                'start_time': datetime_object,
                'has_started': True/False
            },
            ...
        ]
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    games = []
    seen_event_ids = set()
    current_time = get_eastern_now()

    # Find all status-wrapper containers (one per game)
    containers = soup.find_all(class_='cb-event-cell__status-wrapper')

    for container in containers:
        # Find the event link within this container
        link = container.find('a', class_='event-nav-link')
        if not link:
            continue

        href = link.get('href')
        if not href or '/event/' not in href:
            continue

        # Extract slug and event ID from URL
        # Pattern: /event/{slug}/{event_id} or https://sportsbook.draftkings.com/event/{slug}/{event_id}
        match = re.search(r'/event/([^/]+)/(\d+)', href)
        if not match:
            continue

        slug = match.group(1)
        event_id = match.group(2)

        # Skip duplicates
        if event_id in seen_event_ids:
            continue
        seen_event_ids.add(event_id)

        # Build full URL with SGP mode
        if href.startswith('http'):
            base_url = href
        else:
            base_url = f"https://sportsbook.draftkings.com{href}"

        sgp_url = f"{base_url}?sgpmode=true" if '?' not in base_url else f"{base_url}&sgpmode=true"

        # Parse team abbreviations from slug for display
        # Example slug: "atl-falcons-%40-ind-colts" -> "ATL @ IND"
        teams_display = slug.replace('-', ' ').replace('%40', '@').upper()

        # Extract start time from container
        start_time_str = None
        start_time = None
        has_started = False

        time_elem = container.find(class_='cb-event-cell__start-time')
        if time_elem:
            start_time_str = time_elem.get_text(strip=True)
            start_time = parse_dk_time_string(start_time_str, current_time)

            if start_time:
                has_started = current_time >= start_time
        else:
            # No start time element - check if game is live
            # If there's a live icon or clock, game has started
            live_icon = container.find(class_='sc-icon-live')
            clock_elem = container.find(class_='cb-event-cell__clock')
            if live_icon or clock_elem:
                has_started = True
                start_time_str = "LIVE" if live_icon else "In Progress"

        games.append({
            'url': sgp_url,
            'slug': slug,
            'event_id': event_id,
            'teams_display': teams_display,
            'start_time_str': start_time_str,
            'start_time': start_time,
            'has_started': has_started
        })

    return games


def parse_team_abbrs_from_slug(slug: str) -> tuple[str, str]:
    """Parse team abbreviations from DraftKings game slug.

    Handles special cases for teams that share city abbreviations:
    - LA teams (Chargers/Rams): "la-chargers" → "LAC", "la-rams" → "LAR"
    - NY teams (Giants/Jets): "ny-giants" → "NYG", "ny-jets" → "NYJ"

    Args:
        slug: Game slug like "atl-falcons-%40-ind-colts"

    Returns:
        tuple: (away_abbr, home_abbr) like ("ATL", "IND")
    """
    # Split by @
    parts = slug.split('%40')
    if len(parts) != 2:
        return (None, None)

    # Extract first non-empty word from each part (team abbreviation)
    away_parts = [p for p in parts[0].split('-') if p]
    home_parts = [p for p in parts[1].split('-') if p]

    # First part is usually the abbreviation
    away_abbr = away_parts[0].upper() if away_parts else None
    home_abbr = home_parts[0].upper() if home_parts else None

    # Special handling for LA teams (Chargers and Rams)
    # DraftKings slugs: "la-chargers" and "la-rams"
    # We need: "LAC" and "LAR"
    if away_abbr == "LA" and len(away_parts) > 1:
        if away_parts[1] == "chargers":
            away_abbr = "LAC"
        elif away_parts[1] == "rams":
            away_abbr = "LAR"

    if home_abbr == "LA" and len(home_parts) > 1:
        if home_parts[1] == "chargers":
            home_abbr = "LAC"
        elif home_parts[1] == "rams":
            home_abbr = "LAR"

    # Special handling for NY teams (Giants and Jets)
    # DraftKings slugs: "ny-giants" and "ny-jets"
    # We need: "NYG" and "NYJ"
    if away_abbr == "NY" and len(away_parts) > 1:
        if away_parts[1] == "jets":
            away_abbr = "NYJ"
        elif away_parts[1] == "giants":
            away_abbr = "NYG"

    if home_abbr == "NY" and len(home_parts) > 1:
        if home_parts[1] == "jets":
            home_abbr = "NYJ"
        elif home_parts[1] == "giants":
            home_abbr = "NYG"

    return (away_abbr, home_abbr)


def check_odds_exist(dk_away_abbr: str, dk_home_abbr: str, game_date_str: str = None) -> bool:
    """Check if odds already exist for a game.

    Args:
        dk_away_abbr: DraftKings away team abbreviation
        dk_home_abbr: DraftKings home team abbreviation
        game_date_str: Game date string (defaults to today)

    Returns:
        bool: True if odds exist, False otherwise
    """
    try:
        # Convert to PFR abbreviations
        pfr_away_abbr = DK_TO_PFR_ABBR.get(dk_away_abbr, dk_away_abbr.lower())
        pfr_home_abbr = DK_TO_PFR_ABBR.get(dk_home_abbr, dk_home_abbr.lower())

        # Get date folder (convert UTC to Eastern time)
        if game_date_str:
            try:
                date_folder = iso_to_eastern_date_folder(game_date_str)
            except (ValueError, AttributeError):
                date_folder = get_eastern_now().strftime("%Y-%m-%d")
        else:
            date_folder = get_eastern_now().strftime("%Y-%m-%d")

        # Check if file exists
        return odds_repo.odds_exist(date_folder, pfr_away_abbr, pfr_home_abbr)
    except Exception:
        return False


def fetch_single_game_odds(game_url: str, skip_if_exists: bool = True) -> dict:
    """Fetch odds for a single game from DraftKings URL.

    Args:
        game_url: DraftKings game URL
        skip_if_exists: If True, skip fetching if odds already exist

    Returns:
        dict with keys:
            - 'status': 'success', 'skipped', or 'failed'
            - 'message': Status message
            - 'odds_data': Extracted odds data (if success)
            - 'error': Error message (if failed)
    """
    try:
        # Fetch HTML from game URL
        scraper = WebScraper(headless=True, timeout=30000)
        with scraper.launch() as page:
            scraper.navigate_and_wait(page, game_url, wait_time=3000)
            game_html_content = page.content()

        # Save HTML to temp file for odds scraper
        temp_html_path = Path("nfl/data/odds") / "temp_dk_page.html"
        temp_html_path.parent.mkdir(parents=True, exist_ok=True)
        temp_html_path.write_text(game_html_content, encoding='utf-8')

        # Extract odds
        odds_scraper = NFLOddsScraper()
        odds_data = odds_scraper.extract_odds(str(temp_html_path))

        # Clean up temp file
        temp_html_path.unlink()

        # Check if we should skip (only after extraction to get team info)
        if skip_if_exists:
            dk_away_abbr = odds_data["teams"]["away"]["abbr"]
            dk_home_abbr = odds_data["teams"]["home"]["abbr"]
            game_date_str = odds_data.get("game_date")

            if check_odds_exist(dk_away_abbr, dk_home_abbr, game_date_str):
                return {
                    'status': 'skipped',
                    'message': 'Odds already exist',
                    'odds_data': odds_data
                }

        # Save odds
        save_odds_to_json(odds_data)

        return {
            'status': 'success',
            'message': 'Odds fetched and saved',
            'odds_data': odds_data
        }

    except Exception as e:
        return {
            'status': 'failed',
            'message': str(e),
            'error': str(e)
        }


def generate_schedule_file(games: list[dict], date_folder: str, fetched_tracking: dict) -> None:
    """Generate schedule.json for batch predictions using Eastern time.

    Creates a schedule file with game metadata to enable batch prediction workflows.
    Includes both DK and PFR abbreviations for compatibility, and tracks which games
    had odds successfully fetched.

    Args:
        games: List of game dicts from parse_todays_game_links()
        date_folder: Date string in Eastern time (YYYY-MM-DD)
        fetched_tracking: Dict mapping event_id -> bool (fetch success status)
    """
    schedule = {
        "date": date_folder,
        "fetched_at": get_eastern_now().isoformat(),
        "source": "draftkings",
        "games": []
    }

    for game in games:
        # Parse team abbreviations from slug
        dk_away_abbr, dk_home_abbr = parse_team_abbrs_from_slug(game['slug'])

        if not dk_away_abbr or not dk_home_abbr:
            console.print(f"[yellow]Warning: Could not parse team abbreviations from slug: {game['slug']}[/yellow]")
            continue

        # Convert to PFR abbreviations using existing mapping
        pfr_away_abbr = DK_TO_PFR_ABBR.get(dk_away_abbr, dk_away_abbr.lower())
        pfr_home_abbr = DK_TO_PFR_ABBR.get(dk_home_abbr, dk_home_abbr.lower())

        # Get team info from TEAMS array (for full names)
        away_team = DK_ABBR_TO_TEAM.get(dk_away_abbr, {})
        home_team = DK_ABBR_TO_TEAM.get(dk_home_abbr, {})

        # Build game entry
        game_entry = {
            "event_id": game['event_id'],
            "slug": game['slug'],
            "teams": {
                "away": {
                    "name": away_team.get("name", f"Unknown ({dk_away_abbr})"),
                    "dk_abbr": dk_away_abbr,
                    "pfr_abbr": pfr_away_abbr
                },
                "home": {
                    "name": home_team.get("name", f"Unknown ({dk_home_abbr})"),
                    "dk_abbr": dk_home_abbr,
                    "pfr_abbr": pfr_home_abbr
                }
            },
            "game_time_eastern": game['start_time'].isoformat() if game.get('start_time') else None,
            "game_time_display": game.get('start_time_str', 'TBD'),
            "has_started": game.get('has_started', False),
            "odds_file": f"{pfr_home_abbr}_{pfr_away_abbr}.json",
            "odds_fetched": fetched_tracking.get(game['event_id'], False)
        }

        schedule["games"].append(game_entry)

    # Add summary statistics
    schedule["summary"] = {
        "total_games": len(schedule["games"]),
        "upcoming_games": sum(1 for g in schedule["games"] if not g.get('has_started', False)),
        "started_games": sum(1 for g in schedule["games"] if g.get('has_started', False)),
        "odds_fetched": sum(1 for g in schedule["games"] if g.get('odds_fetched', False)),
        "odds_missing": sum(1 for g in schedule["games"] if not g.get('odds_fetched', False))
    }

    # Save to date folder
    schedule_path = Path(f"nfl/data/odds/{date_folder}/schedule.json")
    schedule_path.parent.mkdir(parents=True, exist_ok=True)

    with open(schedule_path, 'w', encoding='utf-8') as f:
        json.dump(schedule, f, indent=2, ensure_ascii=False)


def fetch_odds_command():
    """Fetch odds for all today's NFL games from DraftKings.

    Workflow:
    1. Scrape DraftKings NFL schedule page
    2. Parse all game URLs automatically
    3. For each game:
       - Check if odds already fetched (skip if yes)
       - Fetch and save odds if new
       - Add 3-5 second delay between fetches (rate limiting)
    4. Display summary of results
    """
    print_header("🎲 NFL ODDS FETCHER 🎲")
    console.print()
    console.print("[dim]Automatically fetches odds for all today's NFL games[/dim]")
    console.print()

    try:
        # Step 1: Scrape DraftKings schedule page
        print_info("🌐 Fetching today's NFL schedule from DraftKings...")
        html_content = scrape_draftkings_schedule()
        print_success("Schedule page fetched successfully")

        # Step 2: Parse game links
        console.print()
        print_info("🔍 Parsing game URLs...")
        games = parse_todays_game_links(html_content)

        if not games:
            console.print()
            console.print(Panel(
                "[yellow]No NFL games found on DraftKings schedule page.[/yellow]\n\n"
                "[dim]This could mean:[/dim]\n"
                "• No games scheduled for today\n"
                "• DraftKings changed their page structure\n"
                "• Network or parsing issue",
                title="[bold yellow]No Games Found[/bold yellow]",
                border_style="yellow",
                padding=(1, 2)
            ))
            return

        # Filter games into three categories
        started_games = [g for g in games if g.get('has_started', False)]
        upcoming_games = [
            g for g in games
            if not g.get('has_started', False)
            and (g.get('start_time_str', '').startswith('Today')
                 or g.get('start_time_str', '').startswith('Tomorrow'))
        ]
        future_games = [
            g for g in games
            if not g.get('has_started', False)
            and not g.get('start_time_str', '').startswith('Today')
            and not g.get('start_time_str', '').startswith('Tomorrow')
        ]

        print_success(f"Found {len(games)} game(s) total")
        if started_games or future_games:
            status_parts = []
            if upcoming_games:
                status_parts.append(f"{len(upcoming_games)} today/tomorrow")
            if started_games:
                status_parts.append(f"{len(started_games)} started (skipped)")
            if future_games:
                status_parts.append(f"{len(future_games)} future (skipped)")
            console.print(f"[dim]  • {', '.join(status_parts)}[/dim]")

        if not upcoming_games:
            console.print()
            reason = ""
            if started_games and not future_games:
                reason = "[yellow]All games have already started![/yellow]\n\n" \
                         "[dim]Cannot fetch odds for games in progress.[/dim]\n" \
                         "Try running this command before games start."
            elif future_games and not started_games:
                reason = "[yellow]No games scheduled for today or tomorrow![/yellow]\n\n" \
                         f"[dim]Found {len(future_games)} game(s) scheduled for future dates.[/dim]\n" \
                         "Run this command again closer to the game day."
            else:
                reason = "[yellow]No games available to fetch![/yellow]\n\n" \
                         f"[dim]• {len(started_games)} game(s) already started[/dim]\n" \
                         f"[dim]• {len(future_games)} game(s) scheduled for future dates[/dim]"

            console.print(Panel(
                reason,
                title="[bold yellow]No Upcoming Games (Today/Tomorrow)[/bold yellow]",
                border_style="yellow",
                padding=(1, 2)
            ))
            return

        # Step 3: Fetch odds for each upcoming game
        console.print()
        print_info(f"📊 Fetching odds for {len(upcoming_games)} upcoming game(s) (with 3-5s delay between fetches)...")
        console.print()

        fetched_count = 0
        skipped_count = 0
        failed_games = []
        fetched_tracking = {}  # Track fetch results for schedule.json generation

        for idx, game in enumerate(upcoming_games, 1):
            game_display = game['teams_display']
            time_display = f" ({game['start_time_str']})" if game.get('start_time_str') else ""
            console.print(f"[cyan][{idx}/{len(upcoming_games)}][/cyan] {game_display}{time_display}...", end=" ")

            try:
                # Parse team abbreviations from slug
                away_abbr, home_abbr = parse_team_abbrs_from_slug(game['slug'])

                # Check if odds already exist BEFORE fetching
                if away_abbr and home_abbr and check_odds_exist(away_abbr, home_abbr):
                    console.print("[yellow]⊘ Already have odds (skipped)[/yellow]")
                    skipped_count += 1
                    fetched_tracking[game['event_id']] = True  # Already have odds = success
                    continue

                # Use the reusable fetch function
                result = fetch_single_game_odds(game['url'], skip_if_exists=False)

                if result['status'] == 'success':
                    console.print("[green]✓ Saved[/green]")
                    fetched_count += 1
                    fetched_tracking[game['event_id']] = True
                elif result['status'] == 'skipped':
                    console.print("[yellow]⊘ Already have odds (skipped)[/yellow]")
                    skipped_count += 1
                    fetched_tracking[game['event_id']] = True
                else:
                    console.print(f"[red]✗ Failed: {result['message'][:50]}[/red]")
                    failed_games.append({
                        'game': game_display,
                        'error': result['message']
                    })
                    fetched_tracking[game['event_id']] = False

                # Rate limiting: Add delay between fetches (except for last game)
                if idx < len(upcoming_games):
                    delay = random.uniform(3, 5)
                    console.print(f"[dim]  Waiting {delay:.1f}s...[/dim]")
                    time.sleep(delay)

            except Exception as e:
                console.print(f"[red]✗ Failed: {str(e)[:50]}[/red]")
                failed_games.append({
                    'game': game_display,
                    'error': str(e)
                })
                fetched_tracking[game['event_id']] = False

        # Step 4: Display summary
        console.print()
        console.print("[bold]═" * 40 + "[/bold]")
        console.print()

        summary_text = f"[bold cyan]Summary:[/bold cyan]\n"
        summary_text += f"• Fetched: [green]{fetched_count}[/green] new game(s)\n"
        summary_text += f"• Skipped: [yellow]{skipped_count}[/yellow] existing game(s)\n"
        summary_text += f"• Failed: [red]{len(failed_games)}[/red] game(s)"

        if fetched_count > 0:
            today_str = get_eastern_now().strftime("%Y-%m-%d")
            summary_text += f"\n\n[dim]Odds saved to: nfl/data/odds/{today_str}/[/dim]"

        console.print(Panel(
            summary_text,
            title="[bold green]✅ Batch Fetch Complete[/bold green]" if len(failed_games) == 0 else "[bold yellow]⚠ Batch Fetch Complete (with errors)[/bold yellow]",
            border_style="green" if len(failed_games) == 0 else "yellow",
            padding=(1, 2)
        ))

        # Show failed games details if any
        if failed_games:
            console.print()
            console.print("[bold red]Failed Games:[/bold red]")
            for failed in failed_games:
                console.print(f"  • {failed['game']}: {failed['error'][:80]}")

        # Step 5: Generate schedule file for batch predictions
        if upcoming_games or started_games:
            try:
                console.print()
                print_info("📅 Generating schedule files for batch predictions...")

                all_games = upcoming_games + started_games

                # Group games by their actual game date
                games_by_date = defaultdict(list)
                for game in all_games:
                    if game.get('start_time'):
                        game_date = game['start_time'].strftime("%Y-%m-%d")
                        games_by_date[game_date].append(game)
                    else:
                        # Fallback to today if no start_time
                        today_str = get_eastern_now().strftime("%Y-%m-%d")
                        games_by_date[today_str].append(game)

                # Generate one schedule.json per date
                for game_date, date_games in games_by_date.items():
                    generate_schedule_file(date_games, game_date, fetched_tracking)
                    print_success(f"Schedule saved: nfl/data/odds/{game_date}/schedule.json")
                    console.print(f"[dim]  • {len(date_games)} game(s) on {game_date}[/dim]")
            except Exception as e:
                print_warning(f"Could not generate schedule: {str(e)}")

    except Exception as e:
        console.print()
        print_error(f"Error during batch fetch: {str(e)}")
        console.print()
        console.print(Panel(
            f"[red]Failed to fetch odds[/red]\n\n"
            f"[dim]Error details:[/dim]\n{str(e)}\n\n"
            f"[yellow]Please check:[/yellow]\n"
            f"• You have internet connection\n"
            f"• DraftKings website is accessible\n"
            f"• Playwright browser is installed (playwright install chromium)",
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
    filepath = f"nfl/data/odds/{date_folder}/{pfr_home_abbr}_{pfr_away_abbr}.json"
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
