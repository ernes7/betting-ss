"""STATS Service - Sport-agnostic stats fetching and storage.

This service is a black box that:
- Takes sport configuration as input (URLs, table mappings)
- Fetches HTML tables from sports reference sites
- Outputs CSV files

All sport-specific details come from the config parameter.
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

from services.stats.config import StatsServiceConfig
from services.stats.fetcher import StatsFetcher

logger = get_logger("stats")


class StatsService:
    """Sport-agnostic service for fetching and managing team statistics.

    This is a black box - all sport-specific details come from the config.
    Uses constructor injection for all dependencies.

    Example:
        from sports.nfl.nfl_config import get_nfl_stats_config

        config = get_nfl_stats_config()
        service = StatsService(sport="nfl", config=config)

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
        config: StatsServiceConfig,
        fetcher: StatsFetcher | None = None,
        error_handler: ErrorHandler | None = None,
    ):
        """Initialize the STATS service.

        Args:
            sport: Sport identifier (e.g., 'nfl', 'bundesliga')
            config: Service configuration with URLs and table mappings (required)
            fetcher: StatsFetcher instance (created if not provided)
            error_handler: ErrorHandler instance (created if not provided)
        """
        self.sport = sport.lower()
        self.config = config
        self.fetcher = fetcher or StatsFetcher(self.sport, self.config)
        self.error_handler = error_handler or ErrorHandler("stats")

        # Set up data directories
        self.data_root = Path(self.config.data_root.format(sport=self.sport))
        self.rankings_dir = self.data_root / "rankings"
        self.profiles_dir = self.data_root / "profiles"

        logger.info(f"StatsService initialized for {self.sport}")

    def fetch_rankings(self, skip_if_exists: bool = True) -> dict[str, Any]:
        """Fetch league-wide team rankings.

        Args:
            skip_if_exists: If True, load from cache if rankings exist

        Returns:
            Dictionary with rankings tables

        Raises:
            StatsFetchError: If fetching fails
            StatsParseError: If parsing fails
        """
        if skip_if_exists and self.rankings_exist():
            logger.info("Rankings already exist, loading from cache")
            return self.load_rankings()

        try:
            return self.fetcher.fetch_rankings()
        except (StatsFetchError, StatsParseError) as e:
            self.error_handler.handle(e)

    def fetch_defensive_stats(self, skip_if_exists: bool = True) -> dict[str, Any]:
        """Fetch defensive statistics.

        Args:
            skip_if_exists: If True, load from cache if defensive stats exist

        Returns:
            Dictionary with defensive tables

        Raises:
            StatsFetchError: If fetching fails
            StatsParseError: If parsing fails
        """
        # Check if defensive stats exist (they're saved with defense_ prefix)
        if skip_if_exists and self.defensive_stats_exist():
            logger.info("Defensive stats already exist, loading from cache")
            return self.load_defensive_stats()

        try:
            return self.fetcher.fetch_defensive_stats()
        except (StatsFetchError, StatsParseError) as e:
            self.error_handler.handle(e)

    def fetch_team_profile(
        self, team_abbr: str, skip_if_exists: bool = True
    ) -> dict[str, Any]:
        """Fetch team profile data.

        Args:
            team_abbr: Team abbreviation (e.g., 'dal', 'buf')
            skip_if_exists: If True, load from cache if profile exists

        Returns:
            Dictionary with team profile tables

        Raises:
            StatsFetchError: If fetching fails
            StatsParseError: If parsing fails
        """
        if skip_if_exists and self.profile_exists(team_abbr):
            logger.info(f"Profile for {team_abbr.upper()} already exists, loading from cache")
            return self.load_team_profile(team_abbr)

        try:
            return self.fetcher.fetch_team_profile(team_abbr)
        except (StatsFetchError, StatsParseError) as e:
            self.error_handler.handle(e, context={"team": team_abbr})

    def save_rankings(self, rankings_data: dict[str, Any]) -> Path:
        """Save rankings to flat directory as CSV files (no date subfolders).

        Each table in rankings_data is saved as a separate CSV file.

        Args:
            rankings_data: Rankings data dictionary with 'tables' key

        Returns:
            Path to the directory containing CSV files

        Raises:
            DataIOError: If saving fails
        """
        self.rankings_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Save each table as separate CSV
            tables = rankings_data.get("tables", {})
            for table_name, table_data in tables.items():
                if isinstance(table_data, pd.DataFrame):
                    df = table_data
                elif isinstance(table_data, list):
                    df = pd.DataFrame(table_data)
                elif isinstance(table_data, dict) and "data" in table_data:
                    # Handle fetcher format: {"table_name": ..., "columns": ..., "data": [...]}
                    df = pd.DataFrame(table_data["data"])
                else:
                    continue

                csv_path = self.rankings_dir / f"{table_name}.csv"
                df.to_csv(csv_path, index=False)

            logger.info(f"Saved {len(tables)} ranking tables to {self.rankings_dir}")
            return self.rankings_dir
        except Exception as e:
            error = DataIOError(
                f"Failed to save rankings: {e}",
                context={"directory": str(self.rankings_dir), "error": str(e)}
            )
            self.error_handler.handle(error)

    def save_defensive_stats(self, defensive_data: dict[str, Any]) -> Path:
        """Save defensive stats to flat directory as CSV files (no date subfolders).

        Each table is saved as a separate CSV with 'defense_' prefix.

        Args:
            defensive_data: Defensive stats dictionary with 'tables' key

        Returns:
            Path to the directory containing CSV files

        Raises:
            DataIOError: If saving fails
        """
        self.rankings_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Save each table as separate CSV with defense_ prefix
            tables = defensive_data.get("tables", {})
            for table_name, table_data in tables.items():
                if isinstance(table_data, pd.DataFrame):
                    df = table_data
                elif isinstance(table_data, list):
                    df = pd.DataFrame(table_data)
                elif isinstance(table_data, dict) and "data" in table_data:
                    # Handle fetcher format: {"table_name": ..., "columns": ..., "data": [...]}
                    df = pd.DataFrame(table_data["data"])
                else:
                    continue

                csv_path = self.rankings_dir / f"defense_{table_name}.csv"
                df.to_csv(csv_path, index=False)

            logger.info(f"Saved {len(tables)} defensive tables to {self.rankings_dir}")
            return self.rankings_dir
        except Exception as e:
            error = DataIOError(
                f"Failed to save defensive stats: {e}",
                context={"directory": str(self.rankings_dir), "error": str(e)}
            )
            self.error_handler.handle(error)

    def save_team_profile(
        self,
        profile_data: dict[str, Any],
        team_abbr: str,
    ) -> Path:
        """Save team profile to flat directory as CSV files (no date subfolders).

        Each table is saved as a separate CSV in team subdirectory.

        Args:
            profile_data: Profile data dictionary with 'tables' key
            team_abbr: Team abbreviation

        Returns:
            Path to the team directory containing CSV files

        Raises:
            DataIOError: If saving fails
        """
        team_abbr = team_abbr.lower()

        # Build directory path: profiles/{team}/
        team_dir = self.profiles_dir / team_abbr
        team_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Save each table as separate CSV
            tables = profile_data.get("tables", {})
            for table_name, table_data in tables.items():
                if isinstance(table_data, pd.DataFrame):
                    df = table_data
                elif isinstance(table_data, list):
                    df = pd.DataFrame(table_data)
                elif isinstance(table_data, dict) and "data" in table_data:
                    # Handle fetcher format: {"table_name": ..., "columns": ..., "data": [...]}
                    df = pd.DataFrame(table_data["data"])
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

    def load_rankings(self) -> dict[str, Any]:
        """Load rankings from flat directory structure.

        Returns:
            Rankings data dictionary with 'tables' key

        Raises:
            DataNotFoundError: If rankings directory not found
            DataIOError: If loading fails
        """
        if not self.rankings_dir.exists():
            raise DataNotFoundError(
                "Rankings directory not found",
                context={"directory": str(self.rankings_dir)}
            )

        try:
            tables = {}
            # Load all CSV files (excluding defense_ prefixed ones)
            for csv_file in self.rankings_dir.glob("*.csv"):
                if not csv_file.name.startswith("defense_"):
                    tables[csv_file.stem] = pd.read_csv(csv_file).to_dict("records")

            if not tables:
                raise DataNotFoundError(
                    "No ranking CSV files found",
                    context={"directory": str(self.rankings_dir)}
                )

            return {"tables": tables}
        except DataNotFoundError:
            raise
        except Exception as e:
            error = DataIOError(
                f"Failed to load rankings: {e}",
                context={"directory": str(self.rankings_dir), "error": str(e)}
            )
            self.error_handler.handle(error)

    def load_defensive_stats(self) -> dict[str, Any]:
        """Load defensive stats from flat directory structure.

        Returns:
            Defensive stats dictionary with 'tables' key

        Raises:
            DataNotFoundError: If files not found
            DataIOError: If loading fails
        """
        if not self.rankings_dir.exists():
            raise DataNotFoundError(
                "Defensive stats not found",
                context={"directory": str(self.rankings_dir)}
            )

        try:
            tables = {}
            # Load all defense_ prefixed CSV files
            for csv_file in self.rankings_dir.glob("defense_*.csv"):
                # Remove defense_ prefix from table name
                table_name = csv_file.stem.replace("defense_", "")
                tables[table_name] = pd.read_csv(csv_file).to_dict("records")

            if not tables:
                raise DataNotFoundError(
                    "No defensive CSV files found",
                    context={"directory": str(self.rankings_dir)}
                )

            return {"tables": tables}
        except DataNotFoundError:
            raise
        except Exception as e:
            error = DataIOError(
                f"Failed to load defensive stats: {e}",
                context={"directory": str(self.rankings_dir), "error": str(e)}
            )
            self.error_handler.handle(error)

    def load_team_profile(self, team_abbr: str) -> dict[str, Any]:
        """Load team profile from flat directory structure.

        Args:
            team_abbr: Team abbreviation

        Returns:
            Profile data dictionary with 'tables' key

        Raises:
            DataNotFoundError: If profile directory not found
            DataIOError: If loading fails
        """
        team_abbr = team_abbr.lower()
        team_dir = self.profiles_dir / team_abbr

        if not team_dir.exists():
            raise DataNotFoundError(
                f"Profile not found for {team_abbr.upper()}",
                context={"directory": str(team_dir), "team": team_abbr}
            )

        try:
            tables = {}
            for csv_file in team_dir.glob("*.csv"):
                tables[csv_file.stem] = pd.read_csv(csv_file).to_dict("records")

            if not tables:
                raise DataNotFoundError(
                    f"No profile CSV files found for {team_abbr.upper()}",
                    context={"directory": str(team_dir), "team": team_abbr}
                )

            return {"tables": tables, "team": team_abbr}
        except DataNotFoundError:
            raise
        except Exception as e:
            error = DataIOError(
                f"Failed to load profile: {e}",
                context={"directory": str(team_dir), "error": str(e)}
            )
            self.error_handler.handle(error)

    def load_rankings_safe(self) -> Optional[dict[str, Any]]:
        """Load rankings, returning None if not found.

        Returns:
            Rankings data dictionary or None
        """
        try:
            return self.load_rankings()
        except DataNotFoundError:
            return None

    def load_team_profile_safe(self, team_abbr: str) -> Optional[dict[str, Any]]:
        """Load team profile, returning None if not found.

        Args:
            team_abbr: Team abbreviation

        Returns:
            Profile data dictionary or None
        """
        try:
            return self.load_team_profile(team_abbr)
        except DataNotFoundError:
            return None

    def get_available_profiles(self) -> List[str]:
        """Get list of team profiles available.

        Returns:
            List of team abbreviations with available profiles
        """
        if not self.profiles_dir.exists():
            return []

        # Return directories (team abbreviations), excluding date folders
        return sorted([
            d.name for d in self.profiles_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".") and len(d.name) > 10
        ])

    def rankings_exist(self) -> bool:
        """Check if rankings exist in flat structure.

        Returns:
            True if rankings CSV files exist
        """
        if not self.rankings_dir.exists():
            return False
        # Check for any non-defense CSV files
        return any(
            f.suffix == ".csv" and not f.name.startswith("defense_")
            for f in self.rankings_dir.iterdir() if f.is_file()
        )

    def defensive_stats_exist(self) -> bool:
        """Check if defensive stats exist in flat structure.

        Returns:
            True if defensive CSV files exist
        """
        if not self.rankings_dir.exists():
            return False
        # Check for any defense_ prefixed CSV files
        return any(
            f.name.startswith("defense_") and f.suffix == ".csv"
            for f in self.rankings_dir.iterdir() if f.is_file()
        )

    def profile_exists(self, team_abbr: str) -> bool:
        """Check if a team profile exists.

        Args:
            team_abbr: Team abbreviation

        Returns:
            True if profile directory with CSV files exists
        """
        team_abbr = team_abbr.lower()
        team_dir = self.profiles_dir / team_abbr
        if not team_dir.exists():
            return False
        # Check for any CSV files
        return any(f.suffix == ".csv" for f in team_dir.iterdir() if f.is_file())
