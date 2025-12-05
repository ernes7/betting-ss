"""STATS Service - Fetches and manages team rankings and profiles.

This service is responsible for:
- Fetching league-wide rankings from PFR
- Fetching team-specific profiles from PFR
- Saving stats to the data directory as CSV
- Loading and querying existing stats

All dependencies are injected via constructor.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Optional, List

import pandas as pd

from shared.logging import get_logger
from shared.errors import (
    ErrorHandler,
    StatsFetchError,
    StatsParseError,
    DataNotFoundError,
    DataIOError,
)

from services.stats.config import StatsServiceConfig, get_default_config
from services.stats.fetcher import StatsFetcher

logger = get_logger("stats")


class StatsService:
    """Service for fetching and managing team statistics.

    Uses constructor injection for all dependencies.
    Fail-fast error handling with errors.json output.

    Example:
        # Create service with default config
        service = StatsService(sport="nfl")

        # Fetch rankings
        rankings = service.fetch_rankings()

        # Save rankings
        path = service.save_rankings(rankings)

        # Fetch team profile
        profile = service.fetch_team_profile("dal")
    """

    def __init__(
        self,
        sport: str,
        config: StatsServiceConfig | None = None,
        fetcher: StatsFetcher | None = None,
        error_handler: ErrorHandler | None = None,
    ):
        """Initialize the STATS service.

        Args:
            sport: Sport name (nfl, nba)
            config: Service configuration (uses defaults if not provided)
            fetcher: StatsFetcher instance (created if not provided)
            error_handler: ErrorHandler instance (created if not provided)
        """
        self.sport = sport.lower()
        self.config = config or get_default_config(self.sport)
        self.fetcher = fetcher or StatsFetcher(self.sport, self.config)
        self.error_handler = error_handler or ErrorHandler("stats")

        # Set up data directories
        self.data_root = Path(self.config.data_root.format(sport=self.sport))
        self.rankings_dir = self.data_root / "rankings"
        self.profiles_dir = self.data_root / "profiles"

        logger.info(f"StatsService initialized for {self.sport}")

    def fetch_rankings(self) -> dict[str, Any]:
        """Fetch league-wide team rankings.

        Returns:
            Dictionary with rankings tables

        Raises:
            StatsFetchError: If fetching fails
            StatsParseError: If parsing fails
        """
        try:
            return self.fetcher.fetch_rankings()
        except (StatsFetchError, StatsParseError) as e:
            self.error_handler.handle(e)

    def fetch_defensive_stats(self) -> dict[str, Any]:
        """Fetch defensive statistics.

        Returns:
            Dictionary with defensive tables

        Raises:
            StatsFetchError: If fetching fails
            StatsParseError: If parsing fails
        """
        try:
            return self.fetcher.fetch_defensive_stats()
        except (StatsFetchError, StatsParseError) as e:
            self.error_handler.handle(e)

    def fetch_team_profile(self, team_abbr: str) -> dict[str, Any]:
        """Fetch team profile data.

        Args:
            team_abbr: Team abbreviation (e.g., 'dal', 'buf')

        Returns:
            Dictionary with team profile tables

        Raises:
            StatsFetchError: If fetching fails
            StatsParseError: If parsing fails
        """
        try:
            return self.fetcher.fetch_team_profile(team_abbr)
        except (StatsFetchError, StatsParseError) as e:
            self.error_handler.handle(e, context={"team": team_abbr})

    def save_rankings(
        self,
        rankings_data: dict[str, Any],
        date: str | None = None,
    ) -> Path:
        """Save rankings to the data directory as CSV files.

        Each table in rankings_data is saved as a separate CSV file.

        Args:
            rankings_data: Rankings data dictionary with 'tables' key
            date: Date string (YYYY-MM-DD), defaults to today

        Returns:
            Path to the directory containing CSV files

        Raises:
            DataIOError: If saving fails
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        # Build directory path
        date_dir = self.rankings_dir / date
        date_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Save each table as separate CSV
            tables = rankings_data.get("tables", {})
            for table_name, table_data in tables.items():
                if isinstance(table_data, pd.DataFrame):
                    df = table_data
                elif isinstance(table_data, list):
                    df = pd.DataFrame(table_data)
                else:
                    continue

                csv_path = date_dir / f"{table_name}.csv"
                df.to_csv(csv_path, index=False)

            logger.info(f"Saved {len(tables)} ranking tables to {date_dir}")
            return date_dir
        except Exception as e:
            error = DataIOError(
                f"Failed to save rankings: {e}",
                context={"directory": str(date_dir), "error": str(e)}
            )
            self.error_handler.handle(error)

    def save_defensive_stats(
        self,
        defensive_data: dict[str, Any],
        date: str | None = None,
    ) -> Path:
        """Save defensive stats to the data directory as CSV files.

        Each table is saved as a separate CSV with 'defense_' prefix.

        Args:
            defensive_data: Defensive stats dictionary with 'tables' key
            date: Date string (YYYY-MM-DD), defaults to today

        Returns:
            Path to the directory containing CSV files

        Raises:
            DataIOError: If saving fails
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        # Build directory path
        date_dir = self.rankings_dir / date
        date_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Save each table as separate CSV with defense_ prefix
            tables = defensive_data.get("tables", {})
            for table_name, table_data in tables.items():
                if isinstance(table_data, pd.DataFrame):
                    df = table_data
                elif isinstance(table_data, list):
                    df = pd.DataFrame(table_data)
                else:
                    continue

                csv_path = date_dir / f"defense_{table_name}.csv"
                df.to_csv(csv_path, index=False)

            logger.info(f"Saved {len(tables)} defensive tables to {date_dir}")
            return date_dir
        except Exception as e:
            error = DataIOError(
                f"Failed to save defensive stats: {e}",
                context={"directory": str(date_dir), "error": str(e)}
            )
            self.error_handler.handle(error)

    def save_team_profile(
        self,
        profile_data: dict[str, Any],
        team_abbr: str,
        date: str | None = None,
    ) -> Path:
        """Save team profile to the data directory as CSV files.

        Each table is saved as a separate CSV in team subdirectory.

        Args:
            profile_data: Profile data dictionary with 'tables' key
            team_abbr: Team abbreviation
            date: Date string (YYYY-MM-DD), defaults to today

        Returns:
            Path to the team directory containing CSV files

        Raises:
            DataIOError: If saving fails
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        team_abbr = team_abbr.lower()

        # Build directory path: profiles/{date}/{team}/
        team_dir = self.profiles_dir / date / team_abbr
        team_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Save each table as separate CSV
            tables = profile_data.get("tables", {})
            for table_name, table_data in tables.items():
                if isinstance(table_data, pd.DataFrame):
                    df = table_data
                elif isinstance(table_data, list):
                    df = pd.DataFrame(table_data)
                else:
                    continue

                csv_path = team_dir / f"{table_name}.csv"
                df.to_csv(csv_path, index=False)

            logger.info(f"Saved {len(tables)} profile tables for {team_abbr.upper()} to {team_dir}")
            return team_dir
        except Exception as e:
            error = DataIOError(
                f"Failed to save profile: {e}",
                context={"directory": str(team_dir), "team": team_abbr, "error": str(e)}
            )
            self.error_handler.handle(error)

    def load_rankings(self, date: str) -> dict[str, Any]:
        """Load rankings for a specific date from CSV files.

        Args:
            date: Date string (YYYY-MM-DD)

        Returns:
            Rankings data dictionary with 'tables' key

        Raises:
            DataNotFoundError: If rankings directory not found
            DataIOError: If loading fails
        """
        date_dir = self.rankings_dir / date

        if not date_dir.exists():
            raise DataNotFoundError(
                f"Rankings not found for {date}",
                context={"directory": str(date_dir), "date": date}
            )

        try:
            tables = {}
            # Load all CSV files (excluding defense_ prefixed ones)
            for csv_file in date_dir.glob("*.csv"):
                if not csv_file.name.startswith("defense_"):
                    tables[csv_file.stem] = pd.read_csv(csv_file).to_dict("records")

            if not tables:
                raise DataNotFoundError(
                    f"No ranking CSV files found for {date}",
                    context={"directory": str(date_dir), "date": date}
                )

            return {"tables": tables, "date": date}
        except DataNotFoundError:
            raise
        except Exception as e:
            error = DataIOError(
                f"Failed to load rankings: {e}",
                context={"directory": str(date_dir), "error": str(e)}
            )
            self.error_handler.handle(error)

    def load_defensive_stats(self, date: str) -> dict[str, Any]:
        """Load defensive stats for a specific date from CSV files.

        Args:
            date: Date string (YYYY-MM-DD)

        Returns:
            Defensive stats dictionary with 'tables' key

        Raises:
            DataNotFoundError: If files not found
            DataIOError: If loading fails
        """
        date_dir = self.rankings_dir / date

        if not date_dir.exists():
            raise DataNotFoundError(
                f"Defensive stats not found for {date}",
                context={"directory": str(date_dir), "date": date}
            )

        try:
            tables = {}
            # Load all defense_ prefixed CSV files
            for csv_file in date_dir.glob("defense_*.csv"):
                # Remove defense_ prefix from table name
                table_name = csv_file.stem.replace("defense_", "")
                tables[table_name] = pd.read_csv(csv_file).to_dict("records")

            if not tables:
                raise DataNotFoundError(
                    f"No defensive CSV files found for {date}",
                    context={"directory": str(date_dir), "date": date}
                )

            return {"tables": tables, "date": date}
        except DataNotFoundError:
            raise
        except Exception as e:
            error = DataIOError(
                f"Failed to load defensive stats: {e}",
                context={"directory": str(date_dir), "error": str(e)}
            )
            self.error_handler.handle(error)

    def load_team_profile(self, team_abbr: str, date: str) -> dict[str, Any]:
        """Load team profile for a specific date from CSV files.

        Args:
            team_abbr: Team abbreviation
            date: Date string (YYYY-MM-DD)

        Returns:
            Profile data dictionary with 'tables' key

        Raises:
            DataNotFoundError: If profile directory not found
            DataIOError: If loading fails
        """
        team_abbr = team_abbr.lower()
        team_dir = self.profiles_dir / date / team_abbr

        if not team_dir.exists():
            raise DataNotFoundError(
                f"Profile not found for {team_abbr.upper()} on {date}",
                context={"directory": str(team_dir), "team": team_abbr, "date": date}
            )

        try:
            tables = {}
            for csv_file in team_dir.glob("*.csv"):
                tables[csv_file.stem] = pd.read_csv(csv_file).to_dict("records")

            if not tables:
                raise DataNotFoundError(
                    f"No profile CSV files found for {team_abbr.upper()} on {date}",
                    context={"directory": str(team_dir), "team": team_abbr, "date": date}
                )

            return {"tables": tables, "team": team_abbr, "date": date}
        except DataNotFoundError:
            raise
        except Exception as e:
            error = DataIOError(
                f"Failed to load profile: {e}",
                context={"directory": str(team_dir), "error": str(e)}
            )
            self.error_handler.handle(error)

    def load_rankings_safe(self, date: str) -> Optional[dict[str, Any]]:
        """Load rankings, returning None if not found.

        Args:
            date: Date string (YYYY-MM-DD)

        Returns:
            Rankings data dictionary or None
        """
        try:
            return self.load_rankings(date)
        except DataNotFoundError:
            return None

    def load_team_profile_safe(self, team_abbr: str, date: str) -> Optional[dict[str, Any]]:
        """Load team profile, returning None if not found.

        Args:
            team_abbr: Team abbreviation
            date: Date string (YYYY-MM-DD)

        Returns:
            Profile data dictionary or None
        """
        try:
            return self.load_team_profile(team_abbr, date)
        except DataNotFoundError:
            return None

    def get_available_dates(self) -> List[str]:
        """Get list of dates that have rankings data available.

        Returns:
            Sorted list of dates in YYYY-MM-DD format (most recent first)
        """
        if not self.rankings_dir.exists():
            return []

        dates = [
            d.name for d in self.rankings_dir.iterdir()
            if d.is_dir() and len(d.name.split("-")) == 3
        ]

        return sorted(dates, reverse=True)

    def get_available_profiles(self, date: str) -> List[str]:
        """Get list of team profiles available for a specific date.

        Args:
            date: Date string (YYYY-MM-DD)

        Returns:
            List of team abbreviations with available profiles
        """
        date_dir = self.profiles_dir / date

        if not date_dir.exists():
            return []

        # Return directories (team abbreviations)
        return sorted([
            d.name for d in date_dir.iterdir() if d.is_dir()
        ])

    def rankings_exist(self, date: str) -> bool:
        """Check if rankings exist for a specific date.

        Args:
            date: Date string (YYYY-MM-DD)

        Returns:
            True if rankings CSV files exist
        """
        date_dir = self.rankings_dir / date
        if not date_dir.exists():
            return False
        # Check for any non-defense CSV files
        return any(
            f.suffix == ".csv" and not f.name.startswith("defense_")
            for f in date_dir.iterdir()
        )

    def profile_exists(self, team_abbr: str, date: str) -> bool:
        """Check if a team profile exists for a specific date.

        Args:
            team_abbr: Team abbreviation
            date: Date string (YYYY-MM-DD)

        Returns:
            True if profile directory with CSV files exists
        """
        team_abbr = team_abbr.lower()
        team_dir = self.profiles_dir / date / team_abbr
        if not team_dir.exists():
            return False
        # Check for any CSV files
        return any(f.suffix == ".csv" for f in team_dir.iterdir())
