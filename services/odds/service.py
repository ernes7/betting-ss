"""ODDS Service - Fetches and manages betting odds.

This service is responsible for:
- Fetching odds from DraftKings (via URL or saved HTML)
- Saving odds to the data directory as CSV files
- Loading and querying existing odds
- Providing odds data to other services

All dependencies are injected via constructor.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Optional, List, Tuple

import pandas as pd

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
        """Save odds to the data directory as CSV files.

        Creates a game directory with:
        - game_lines.csv: Moneyline, spread, total (1 row)
        - player_props.csv: All player props (1 row per prop milestone)

        Args:
            odds_data: Odds data dictionary
            game_date: Game date (YYYY-MM-DD), extracted from data if not provided
            home_team: Home team abbreviation, extracted from data if not provided
            away_team: Away team abbreviation, extracted from data if not provided

        Returns:
            Path to the game directory

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

        # Build game directory path
        game_dir = self.data_root / game_date / f"{home_team}_{away_team}"
        game_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Save game_lines.csv
            game_lines = odds_data.get("game_lines", {})
            moneyline = game_lines.get("moneyline", {})
            spread = game_lines.get("spread", {})
            total = game_lines.get("total", {})

            game_lines_row = {
                "away_team": away_team,
                "home_team": home_team,
                "game_date": odds_data.get("game_date", ""),
                "ml_away": moneyline.get("away"),
                "ml_home": moneyline.get("home"),
                "spread_away": spread.get("away"),
                "spread_away_odds": spread.get("away_odds"),
                "spread_home": spread.get("home"),
                "spread_home_odds": spread.get("home_odds"),
                "total_line": total.get("line"),
                "total_over": total.get("over"),
                "total_under": total.get("under"),
            }
            pd.DataFrame([game_lines_row]).to_csv(game_dir / "game_lines.csv", index=False)

            # Save player_props.csv
            props_rows = []
            for player_prop in odds_data.get("player_props", []):
                player = player_prop.get("player", "")
                team = player_prop.get("team", "")
                for prop in player_prop.get("props", []):
                    market = prop.get("market", "")
                    for milestone in prop.get("milestones", []):
                        props_rows.append({
                            "player": player,
                            "team": team,
                            "market": market,
                            "line": milestone.get("line"),
                            "odds": milestone.get("odds"),
                        })

            if props_rows:
                pd.DataFrame(props_rows).to_csv(game_dir / "player_props.csv", index=False)
            else:
                # Create empty player_props.csv with headers
                pd.DataFrame(columns=["player", "team", "market", "line", "odds"]).to_csv(
                    game_dir / "player_props.csv", index=False
                )

            logger.info(f"Saved odds to {game_dir}")
            return game_dir
        except Exception as e:
            error = DataIOError(
                f"Failed to save odds: {e}",
                context={"directory": str(game_dir), "error": str(e)}
            )
            self.error_handler.handle(error)

    def load_odds(
        self,
        game_date: str,
        home_team: str,
        away_team: str,
    ) -> dict[str, Any]:
        """Load odds for a specific game from CSV files.

        Args:
            game_date: Game date (YYYY-MM-DD)
            home_team: Home team abbreviation
            away_team: Away team abbreviation

        Returns:
            Odds data dictionary (reconstructed from CSVs)

        Raises:
            DataNotFoundError: If odds directory not found
            DataIOError: If loading fails
        """
        home_team = home_team.lower()
        away_team = away_team.lower()

        game_dir = self.data_root / game_date / f"{home_team}_{away_team}"
        game_lines_path = game_dir / "game_lines.csv"

        if not game_dir.exists() or not game_lines_path.exists():
            raise DataNotFoundError(
                f"Odds not found for {away_team} @ {home_team} on {game_date}",
                context={
                    "directory": str(game_dir),
                    "game_date": game_date,
                    "home_team": home_team,
                    "away_team": away_team,
                }
            )

        try:
            # Load game_lines.csv
            game_lines_df = pd.read_csv(game_lines_path)
            row = game_lines_df.iloc[0].to_dict()

            # Reconstruct odds_data structure
            odds_data = {
                "sport": self.sport,
                "teams": {
                    "away": {"abbr": row.get("away_team", "").upper()},
                    "home": {"abbr": row.get("home_team", "").upper()},
                },
                "game_date": row.get("game_date", ""),
                "game_lines": {
                    "moneyline": {
                        "away": self._safe_int(row.get("ml_away")),
                        "home": self._safe_int(row.get("ml_home")),
                    },
                    "spread": {
                        "away": self._safe_float(row.get("spread_away")),
                        "away_odds": self._safe_int(row.get("spread_away_odds")),
                        "home": self._safe_float(row.get("spread_home")),
                        "home_odds": self._safe_int(row.get("spread_home_odds")),
                    },
                    "total": {
                        "line": self._safe_float(row.get("total_line")),
                        "over": self._safe_int(row.get("total_over")),
                        "under": self._safe_int(row.get("total_under")),
                    },
                },
                "player_props": [],
            }

            # Load player_props.csv if exists
            player_props_path = game_dir / "player_props.csv"
            if player_props_path.exists():
                props_df = pd.read_csv(player_props_path)
                odds_data["player_props"] = self._reconstruct_player_props(props_df)

            return odds_data
        except DataNotFoundError:
            raise
        except Exception as e:
            error = DataIOError(
                f"Failed to load odds: {e}",
                context={"directory": str(game_dir), "error": str(e)}
            )
            self.error_handler.handle(error)

    def _safe_int(self, value: Any) -> Optional[int]:
        """Safely convert value to int, returning None for NaN/None."""
        if pd.isna(value):
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float, returning None for NaN/None."""
        if pd.isna(value):
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _reconstruct_player_props(self, props_df: pd.DataFrame) -> List[dict]:
        """Reconstruct nested player_props structure from flat CSV."""
        if props_df.empty:
            return []

        # Group by player and team
        player_props = []
        for (player, team), group in props_df.groupby(["player", "team"]):
            player_data = {
                "player": player,
                "team": team,
                "props": [],
            }

            # Group by market within player
            for market, market_group in group.groupby("market"):
                prop_data = {
                    "market": market,
                    "milestones": [
                        {"line": row["line"], "odds": int(row["odds"])}
                        for _, row in market_group.iterrows()
                        if pd.notna(row["line"]) and pd.notna(row["odds"])
                    ],
                }
                if prop_data["milestones"]:
                    player_data["props"].append(prop_data)

            if player_data["props"]:
                player_props.append(player_data)

        return player_props

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
            True if odds directory with game_lines.csv exists
        """
        home_team = home_team.lower()
        away_team = away_team.lower()
        game_dir = self.data_root / game_date / f"{home_team}_{away_team}"
        return game_dir.exists() and (game_dir / "game_lines.csv").exists()

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
        """Get list of odds directories available for a specific date.

        Args:
            game_date: Date in YYYY-MM-DD format

        Returns:
            List of tuples (directory_path, display_name)
        """
        date_dir = self.data_root / game_date

        if not date_dir.exists():
            return []

        odds_dirs = []
        for game_dir in date_dir.iterdir():
            if game_dir.is_dir() and (game_dir / "game_lines.csv").exists():
                teams = game_dir.name.split("_")
                if len(teams) == 2:
                    display_name = f"{teams[0].upper()} vs {teams[1].upper()}"
                else:
                    display_name = game_dir.name
                odds_dirs.append((game_dir, display_name))

        return sorted(odds_dirs, key=lambda x: x[1])

    def get_all_odds_for_date(self, game_date: str) -> List[dict[str, Any]]:
        """Get all odds for a specific date.

        Args:
            game_date: Date in YYYY-MM-DD format

        Returns:
            List of odds dictionaries
        """
        odds_dirs = self.get_odds_files_for_date(game_date)
        all_odds = []

        for game_dir, _ in odds_dirs:
            try:
                # Extract home and away from directory name
                teams = game_dir.name.split("_")
                if len(teams) == 2:
                    home_team, away_team = teams[0], teams[1]
                    odds_data = self.load_odds(game_date, home_team, away_team)
                    all_odds.append(odds_data)
            except Exception as e:
                logger.warning(f"Failed to load {game_dir}: {e}")

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
