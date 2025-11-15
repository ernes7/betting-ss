"""Centralized data loading with caching, normalization, and type safety."""

import json
from typing import Dict, Any, Optional
from pathlib import Path
from nfl.teams import TEAMS, DK_ABBR_TO_NAME


class DataLoader:
    """Cached data loader with team name normalization and type safety."""

    # Team name variations to canonical full name mapping
    TEAM_NAME_VARIATIONS = {
        # Full names (canonical)
        **{team["name"]: team["name"] for team in TEAMS},

        # DraftKings abbreviations
        **DK_ABBR_TO_NAME,

        # Common short names
        "NY Jets": "New York Jets",
        "NY Giants": "New York Giants",
        "NE Patriots": "New England Patriots",
        "LA Rams": "Los Angeles Rams",
        "LA Chargers": "Los Angeles Chargers",
        "SF 49ers": "San Francisco 49ers",
        "TB Buccaneers": "Tampa Bay Buccaneers",
        "KC Chiefs": "Kansas City Chiefs",
        "LV Raiders": "Las Vegas Raiders",
        "NO Saints": "New Orleans Saints",
    }

    # Full name to profile directory name
    TEAM_DIR_MAP = {
        team["name"]: team["name"].lower().replace(" ", "_")
        for team in TEAMS
    }

    def __init__(self, sport_config, base_dir: Optional[str] = None):
        """Initialize data loader with cached rankings.

        Args:
            sport_config: Sport configuration object
            base_dir: Base directory (defaults to project root)
        """
        self.sport_config = sport_config
        if base_dir is None:
            base_dir = Path(__file__).parent.parent.parent
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / sport_config.sport_name / "data"

        # Cached rankings (loaded once)
        self.offense_rankings: Dict[str, Dict[str, Any]] = {}
        self.defense_rankings: Dict[str, Dict[str, Any]] = {}

        # Load all rankings at initialization
        self._load_all_rankings()

    def normalize_team_name(self, team_name: str) -> str:
        """Normalize any team name variation to canonical full name.

        Args:
            team_name: Any team name format (full, abbr, short)

        Returns:
            Canonical full name (e.g., "New York Jets")
        """
        return self.TEAM_NAME_VARIATIONS.get(team_name, team_name)

    def get_profile_dir_name(self, team_name: str) -> str:
        """Get profile directory name for a team.

        Args:
            team_name: Any team name format

        Returns:
            Directory name (e.g., "new_york_jets")
        """
        canonical_name = self.normalize_team_name(team_name)
        return self.TEAM_DIR_MAP.get(canonical_name, canonical_name.lower().replace(" ", "_"))

    def _load_all_rankings(self):
        """Load all ranking tables once and cache them."""
        rankings_dir = self.data_dir / "rankings"

        if not rankings_dir.exists():
            print(f"Warning: Rankings directory not found: {rankings_dir}")
            return

        # Offensive rankings
        offense_tables = [
            "passing_offense",
            "rushing_offense",
            "scoring_offense",
            "team_offense",
            "afc_standings",
            "nfc_standings"
        ]

        # Defensive rankings
        defense_tables = [
            "passing_defense",
            "rushing_defense",
            "team_defense",
            "advanced_defense"
        ]

        # Load offensive rankings
        for table_name in offense_tables:
            file_path = rankings_dir / f"{table_name}.json"
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    # Convert to dict keyed by team name for O(1) lookup
                    self.offense_rankings[table_name] = self._index_by_team(data)
                except Exception as e:
                    print(f"Error loading {table_name}: {e}")

        # Load defensive rankings
        for table_name in defense_tables:
            file_path = rankings_dir / f"{table_name}.json"
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    self.defense_rankings[table_name] = self._index_by_team(data)
                except Exception as e:
                    print(f"Error loading {table_name}: {e}")

    def _index_by_team(self, table_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Convert table data to dict keyed by normalized team name.

        Args:
            table_data: Raw table JSON with "data" array

        Returns:
            Dict mapping team name → team stats
        """
        indexed = {}
        data_rows = table_data.get("data", [])

        for row in data_rows:
            team_name = row.get("team")
            if team_name:
                # Normalize team name
                canonical_name = self.normalize_team_name(team_name)
                indexed[canonical_name] = row

        return indexed

    def get_team_stat(
        self,
        team_name: str,
        table_name: str,
        field: str,
        default: Optional[float] = None,
        is_defense: bool = False
    ) -> Optional[float]:
        """Get a team stat with type safety (string → float).

        Args:
            team_name: Team name (any format)
            table_name: Table name (e.g., "scoring_offense")
            field: Field name (e.g., "points_per_g")
            default: Default value if not found
            is_defense: Whether this is a defensive stat

        Returns:
            Float value or default
        """
        canonical_name = self.normalize_team_name(team_name)

        # Select correct rankings dict
        rankings = self.defense_rankings if is_defense else self.offense_rankings

        # Get table
        table = rankings.get(table_name, {})

        # Get team data
        team_data = table.get(canonical_name)
        if not team_data:
            return default

        # Get field value
        value = team_data.get(field)

        # Convert to float
        return self._safe_float(value, default)

    def get_team_data(
        self,
        team_name: str,
        table_name: str,
        is_defense: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Get all data for a team from a table.

        Args:
            team_name: Team name (any format)
            table_name: Table name
            is_defense: Whether this is a defensive stat

        Returns:
            Dict with team stats or None
        """
        canonical_name = self.normalize_team_name(team_name)
        rankings = self.defense_rankings if is_defense else self.offense_rankings
        table = rankings.get(table_name, {})
        return table.get(canonical_name)

    def get_defense_rank(
        self,
        team_name: str,
        category: str = "passing"
    ) -> Optional[int]:
        """Get team's defensive ranking in a category.

        Args:
            team_name: Team name (any format)
            category: "passing", "rushing", or "overall"

        Returns:
            Rank (1-32) or None
        """
        table_map = {
            "passing": "passing_defense",
            "rushing": "rushing_defense",
            "overall": "team_defense"
        }

        table_name = table_map.get(category, "team_defense")
        canonical_name = self.normalize_team_name(team_name)

        team_data = self.defense_rankings.get(table_name, {}).get(canonical_name)
        if not team_data:
            return None

        rank_str = team_data.get("ranker", "16")
        try:
            return int(rank_str)
        except (ValueError, TypeError):
            return None

    def get_offense_rank(
        self,
        team_name: str,
        category: str = "passing"
    ) -> Optional[int]:
        """Get team's offensive ranking in a category.

        Args:
            team_name: Team name (any format)
            category: "passing", "rushing", or "overall"

        Returns:
            Rank (1-32) or None
        """
        table_map = {
            "passing": "passing_offense",
            "rushing": "rushing_offense",
            "overall": "team_offense"
        }

        table_name = table_map.get(category, "team_offense")
        canonical_name = self.normalize_team_name(team_name)

        team_data = self.offense_rankings.get(table_name, {}).get(canonical_name)
        if not team_data:
            return None

        rank_str = team_data.get("ranker", "16")
        try:
            return int(rank_str)
        except (ValueError, TypeError):
            return None

    def get_team_points_allowed_per_game(self, team_name: str) -> float:
        """Get team's defensive points allowed per game.

        Calculates from team_defense table: points / g

        Args:
            team_name: Team name (any format)

        Returns:
            Points allowed per game or 22.0 default
        """
        canonical_name = self.normalize_team_name(team_name)
        team_data = self.defense_rankings.get("team_defense", {}).get(canonical_name)

        if not team_data:
            return 22.0

        points = self._safe_float(team_data.get("points"))
        games = self._safe_float(team_data.get("g"))

        if points is not None and games is not None and games > 0:
            return points / games

        return 22.0

    def get_defense_pressure_rate(self, team_name: str) -> float:
        """Get team's defensive pressure rate (QB pressures %).

        Args:
            team_name: Team name (any format)

        Returns:
            Pressure percentage (0-100) or 22.5 default
        """
        canonical_name = self.normalize_team_name(team_name)
        team_data = self.defense_rankings.get("advanced_defense", {}).get(canonical_name)

        if not team_data:
            return 22.5  # League average

        pressure_pct_str = team_data.get("pressures_pct", "22.5%")
        # Remove % sign and convert to float
        try:
            return float(pressure_pct_str.replace("%", ""))
        except (ValueError, AttributeError):
            return 22.5

    def get_defense_sack_total(self, team_name: str) -> int:
        """Get team's total sacks this season.

        Args:
            team_name: Team name (any format)

        Returns:
            Total sacks or 0
        """
        canonical_name = self.normalize_team_name(team_name)
        team_data = self.defense_rankings.get("advanced_defense", {}).get(canonical_name)

        if not team_data:
            return 0

        sacks_str = team_data.get("sacks", "0")
        try:
            return int(sacks_str)
        except (ValueError, TypeError):
            return 0

    def get_defense_blitz_rate(self, team_name: str) -> float:
        """Get team's blitz rate percentage.

        Args:
            team_name: Team name (any format)

        Returns:
            Blitz percentage (0-100) or 25.0 default
        """
        canonical_name = self.normalize_team_name(team_name)
        team_data = self.defense_rankings.get("advanced_defense", {}).get(canonical_name)

        if not team_data:
            return 25.0  # Default blitz rate

        blitz_pct_str = team_data.get("blitz_pct", "25.0%")
        try:
            return float(blitz_pct_str.replace("%", ""))
        except (ValueError, AttributeError):
            return 25.0

    def _safe_float(self, value: Any, default: Optional[float] = None) -> Optional[float]:
        """Convert value to float, handling None, empty strings, etc.

        Args:
            value: Value to convert
            default: Default if conversion fails

        Returns:
            Float or default
        """
        if value is None or value == "":
            return default

        try:
            return float(value)
        except (ValueError, TypeError):
            return default
