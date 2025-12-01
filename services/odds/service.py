"""ODDS Service - Fetches and manages betting odds.

This service is responsible for:
- Fetching odds from DraftKings (via URL or saved HTML)
- Saving odds to the data directory
- Loading and querying existing odds
- Providing odds data to other services

All dependencies are injected via constructor.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, List, Tuple

from shared.logging import get_logger
from shared.errors import (
    ErrorHandler,
    OddsFetchError,
    OddsParseError,
    DataNotFoundError,
    DataIOError,
)
from shared.models import Odds

from services.odds.config import OddsServiceConfig, get_default_config
from services.odds.scraper import OddsScraper


logger = get_logger("odds")


class OddsService:
    """Service for fetching and managing betting odds.

    Uses constructor injection for all dependencies.
    Fail-fast error handling with errors.json output.

    Example:
        # Create service with default config
        service = OddsService(sport="nfl")

        # Fetch odds from URL
        odds = service.fetch_from_url(url)

        # Save odds
        path = service.save_odds(odds, game_date="2024-12-01")

        # Load existing odds
        odds = service.load_odds("2024-12-01", "dal", "nyg")
    """

    def __init__(
        self,
        sport: str,
        config: OddsServiceConfig | None = None,
        scraper: OddsScraper | None = None,
        error_handler: ErrorHandler | None = None,
    ):
        """Initialize the ODDS service.

        Args:
            sport: Sport name (nfl, nba)
            config: Service configuration (uses defaults if not provided)
            scraper: OddsScraper instance (created if not provided)
            error_handler: ErrorHandler instance (created if not provided)
        """
        self.sport = sport.lower()
        self.config = config or get_default_config(self.sport)
        self.scraper = scraper or OddsScraper(self.config, self.sport)
        self.error_handler = error_handler or ErrorHandler("odds")

        # Set up data directory
        self.data_root = Path(self.config.data_root.format(sport=self.sport))

        logger.info(f"OddsService initialized for {self.sport}")

    def fetch_from_url(self, url: str) -> dict[str, Any]:
        """Fetch odds from a DraftKings URL.

        Args:
            url: DraftKings event URL

        Returns:
            Dictionary with game info and odds

        Raises:
            OddsFetchError: If fetching fails
            OddsParseError: If parsing fails
        """
        try:
            return self.scraper.fetch_odds_from_url(url)
        except (OddsFetchError, OddsParseError) as e:
            self.error_handler.handle(e, context={"url": url})

    def fetch_from_file(self, html_path: str | Path) -> dict[str, Any]:
        """Extract odds from a saved HTML file.

        Args:
            html_path: Path to the HTML file

        Returns:
            Dictionary with game info and odds

        Raises:
            OddsFetchError: If file not found
            OddsParseError: If parsing fails
        """
        try:
            return self.scraper.extract_odds_from_file(html_path)
        except (OddsFetchError, OddsParseError) as e:
            self.error_handler.handle(e, context={"path": str(html_path)})

    def fetch_from_data(self, stadium_data: dict) -> dict[str, Any]:
        """Extract odds from stadium data dictionary.

        Use when you have the data from page.evaluate().

        Args:
            stadium_data: The stadiumEventData dictionary

        Returns:
            Dictionary with game info and odds
        """
        try:
            return self.scraper.extract_odds_from_data(stadium_data)
        except OddsParseError as e:
            self.error_handler.handle(e)

    def save_odds(
        self,
        odds_data: dict[str, Any],
        game_date: str | None = None,
        home_team: str | None = None,
        away_team: str | None = None,
    ) -> Path:
        """Save odds to the data directory.

        Args:
            odds_data: Odds data dictionary
            game_date: Game date (YYYY-MM-DD), extracted from data if not provided
            home_team: Home team abbreviation, extracted from data if not provided
            away_team: Away team abbreviation, extracted from data if not provided

        Returns:
            Path to the saved file

        Raises:
            DataIOError: If saving fails
        """
        # Extract values from data if not provided
        if game_date is None:
            game_date_str = odds_data.get("game_date", "")
            if game_date_str:
                # Parse ISO format and extract date
                try:
                    dt = datetime.fromisoformat(game_date_str.replace("Z", "+00:00"))
                    game_date = dt.strftime("%Y-%m-%d")
                except ValueError:
                    game_date = game_date_str[:10]  # Take first 10 chars
            else:
                game_date = datetime.now().strftime("%Y-%m-%d")

        if home_team is None:
            teams = odds_data.get("teams", {})
            home_team = teams.get("home", {}).get("abbr", "home")
            if home_team:
                home_team = home_team.lower()

        if away_team is None:
            teams = odds_data.get("teams", {})
            away_team = teams.get("away", {}).get("abbr", "away")
            if away_team:
                away_team = away_team.lower()

        # Build file path
        date_dir = self.data_root / game_date
        date_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{home_team}_{away_team}.json"
        filepath = date_dir / filename

        # Save file
        try:
            filepath.write_text(
                json.dumps(odds_data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            logger.info(f"Saved odds to {filepath}")
            return filepath
        except Exception as e:
            error = DataIOError(
                f"Failed to save odds: {e}",
                context={"filepath": str(filepath), "error": str(e)}
            )
            self.error_handler.handle(error)

    def load_odds(
        self,
        game_date: str,
        home_team: str,
        away_team: str,
    ) -> dict[str, Any]:
        """Load odds for a specific game.

        Args:
            game_date: Game date (YYYY-MM-DD)
            home_team: Home team abbreviation
            away_team: Away team abbreviation

        Returns:
            Odds data dictionary

        Raises:
            DataNotFoundError: If odds file not found
            DataIOError: If loading fails
        """
        home_team = home_team.lower()
        away_team = away_team.lower()

        filepath = self.data_root / game_date / f"{home_team}_{away_team}.json"

        if not filepath.exists():
            raise DataNotFoundError(
                f"Odds not found for {away_team} @ {home_team} on {game_date}",
                context={
                    "filepath": str(filepath),
                    "game_date": game_date,
                    "home_team": home_team,
                    "away_team": away_team,
                }
            )

        try:
            return json.loads(filepath.read_text(encoding="utf-8"))
        except Exception as e:
            error = DataIOError(
                f"Failed to load odds: {e}",
                context={"filepath": str(filepath), "error": str(e)}
            )
            self.error_handler.handle(error)

    def load_odds_safe(
        self,
        game_date: str,
        home_team: str,
        away_team: str,
    ) -> Optional[dict[str, Any]]:
        """Load odds for a specific game, returning None if not found.

        Args:
            game_date: Game date (YYYY-MM-DD)
            home_team: Home team abbreviation
            away_team: Away team abbreviation

        Returns:
            Odds data dictionary or None if not found
        """
        try:
            return self.load_odds(game_date, home_team, away_team)
        except DataNotFoundError:
            return None

    def odds_exist(
        self,
        game_date: str,
        home_team: str,
        away_team: str,
    ) -> bool:
        """Check if odds exist for a specific game.

        Args:
            game_date: Game date (YYYY-MM-DD)
            home_team: Home team abbreviation
            away_team: Away team abbreviation

        Returns:
            True if odds file exists
        """
        home_team = home_team.lower()
        away_team = away_team.lower()
        filepath = self.data_root / game_date / f"{home_team}_{away_team}.json"
        return filepath.exists()

    def get_available_dates(self) -> List[str]:
        """Get list of dates that have odds data available.

        Returns:
            Sorted list of dates in YYYY-MM-DD format (most recent first)
        """
        if not self.data_root.exists():
            return []

        dates = [
            d.name for d in self.data_root.iterdir()
            if d.is_dir() and len(d.name.split("-")) == 3
        ]

        return sorted(dates, reverse=True)

    def get_odds_files_for_date(self, game_date: str) -> List[Tuple[Path, str]]:
        """Get list of odds files available for a specific date.

        Args:
            game_date: Date in YYYY-MM-DD format

        Returns:
            List of tuples (filepath, display_name)
        """
        date_dir = self.data_root / game_date

        if not date_dir.exists():
            return []

        odds_files = []
        for filepath in date_dir.glob("*.json"):
            teams = filepath.stem.split("_")
            if len(teams) == 2:
                display_name = f"{teams[0].upper()} vs {teams[1].upper()}"
            else:
                display_name = filepath.name
            odds_files.append((filepath, display_name))

        return sorted(odds_files, key=lambda x: x[1])

    def get_all_odds_for_date(self, game_date: str) -> List[dict[str, Any]]:
        """Get all odds for a specific date.

        Args:
            game_date: Date in YYYY-MM-DD format

        Returns:
            List of odds dictionaries
        """
        odds_files = self.get_odds_files_for_date(game_date)
        all_odds = []

        for filepath, _ in odds_files:
            try:
                odds_data = json.loads(filepath.read_text(encoding="utf-8"))
                all_odds.append(odds_data)
            except Exception as e:
                logger.warning(f"Failed to load {filepath}: {e}")

        return all_odds

    def get_game_lines(self, odds_data: dict) -> Optional[dict]:
        """Extract game lines from odds data.

        Args:
            odds_data: Odds data dictionary

        Returns:
            Game lines dictionary or None
        """
        return odds_data.get("game_lines")

    def get_player_props(self, odds_data: dict) -> Optional[List[dict]]:
        """Extract player props from odds data.

        Args:
            odds_data: Odds data dictionary

        Returns:
            List of player prop dictionaries or None
        """
        return odds_data.get("player_props")

    def to_model(self, odds_data: dict) -> Odds:
        """Convert odds dictionary to Odds dataclass.

        Args:
            odds_data: Raw odds data dictionary

        Returns:
            Odds dataclass instance
        """
        return Odds.from_dict(odds_data)
