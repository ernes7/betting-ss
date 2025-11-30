"""Player game log utility for extracting recent game stats from boxscores."""

from typing import Dict, List, Any, Optional
from pathlib import Path
import os

from shared.repositories.results_repository import ResultsRepository


class PlayerGameLog:
    """Load and calculate player stats from boxscore game logs."""

    # Common nickname mappings for player name matching (same as StatAggregator)
    NICKNAME_MAP = {
        'joshua': 'josh',
        'christopher': 'chris',
        'benjamin': 'ben',
        'william': 'will',
        'willie': 'will',
        'michael': 'mike',
        'matthew': 'matt',
        'nicholas': 'nick',
        'nicolas': 'nick',
        'anthony': 'tony',
        'joseph': 'joe',
        'robert': 'rob',
        'daniel': 'dan',
        'andrew': 'drew',
        'thomas': 'tom',
        'james': 'jim',
        'richard': 'rick',
        'timothy': 'tim',
        'kenneth': 'ken',
        'jonathan': 'jon',
        'alexander': 'alex',
        'zachary': 'zach',
        'patrick': 'pat',
    }

    def __init__(self, sport_code: str, base_dir: str = None):
        """Initialize the player game log utility.

        Args:
            sport_code: Sport identifier (e.g., 'nfl')
            base_dir: Base directory for data files
        """
        self.sport_code = sport_code
        self.results_repo = ResultsRepository(sport_code)
        if base_dir is None:
            base_dir = Path(__file__).parent.parent.parent
        self.base_dir = Path(base_dir)

    def normalize_player_name(self, name: str, strip_suffixes: bool = False) -> str:
        """Normalize player name for matching.

        Args:
            name: Player name
            strip_suffixes: If True, remove Jr/Sr/II/III suffixes

        Returns:
            Normalized lowercase name
        """
        if not name:
            return ""

        if strip_suffixes:
            name = self._strip_suffix(name)

        name_lower = name.lower().strip()
        parts = name_lower.split()
        if not parts:
            return ""

        # Check first name for nickname mapping
        first_name = parts[0]
        if first_name in self.NICKNAME_MAP:
            parts[0] = self.NICKNAME_MAP[first_name]

        return " ".join(parts)

    def _strip_suffix(self, name: str) -> str:
        """Strip common suffixes from player names."""
        if not name:
            return ""

        suffixes = [' jr.', ' jr', ' sr.', ' sr', ' ii', ' iii', ' iv', ' v']
        name_lower = name.lower().strip()

        for suffix in suffixes:
            if name_lower.endswith(suffix):
                return name[:len(name) - len(suffix)].strip()

        return name

    def get_player_recent_games(
        self,
        player_name: str,
        team_abbr: str,
        num_games: int = 5
    ) -> List[Dict[str, Any]]:
        """Find player's last N games from boxscore data.

        Args:
            player_name: Player name to search for
            team_abbr: Team abbreviation (e.g., "DET", "PHI")
            num_games: Maximum number of games to retrieve

        Returns:
            List of game stat dicts, most recent first
        """
        game_logs = []
        team_abbr_upper = team_abbr.upper()

        # Get all result dates (sorted descending - most recent first)
        all_dates = self.results_repo.get_all_result_dates()

        for game_date in all_dates:
            if len(game_logs) >= num_games:
                break

            # Get all results for this date
            results = self.results_repo.list_results_for_date(game_date)

            for result in results:
                if len(game_logs) >= num_games:
                    break

                # Find player in this game's boxscore
                player_stats = self._find_player_in_boxscore(
                    result,
                    player_name,
                    team_abbr_upper
                )

                if player_stats:
                    player_stats["game_date"] = game_date
                    game_logs.append(player_stats)

        return game_logs

    def _find_player_in_boxscore(
        self,
        boxscore: Dict[str, Any],
        player_name: str,
        team_abbr: str
    ) -> Optional[Dict[str, Any]]:
        """Find player stats in boxscore using fuzzy matching.

        Args:
            boxscore: Boxscore data dictionary
            player_name: Player name to search for
            team_abbr: Team abbreviation (uppercase)

        Returns:
            Player stats dict or None if not found
        """
        # Normalize search name
        search_name = self.normalize_player_name(player_name, strip_suffixes=False)
        search_no_suffix = self.normalize_player_name(player_name, strip_suffixes=True)

        tables = boxscore.get("tables", {})

        # Search in passing, rushing, receiving tables
        for table_name in ["passing", "rushing", "receiving"]:
            table = tables.get(table_name, {})
            data = table.get("data", [])

            for player in data:
                player_team = player.get("team", "").upper()

                # Must match team
                if player_team != team_abbr:
                    continue

                boxscore_name = player.get("player", "")
                norm_name = self.normalize_player_name(boxscore_name, strip_suffixes=False)
                norm_no_suffix = self.normalize_player_name(boxscore_name, strip_suffixes=True)

                # Level 1: Exact match after normalization
                if norm_name == search_name:
                    return self._extract_player_stats(player, table_name)

                # Level 2: Match without suffixes
                if norm_no_suffix == search_no_suffix:
                    return self._extract_player_stats(player, table_name)

        return None

    def _extract_player_stats(
        self,
        player_data: Dict[str, Any],
        source_table: str
    ) -> Dict[str, Any]:
        """Extract relevant stats from player boxscore data.

        Args:
            player_data: Raw player data from boxscore
            source_table: Which table the data came from

        Returns:
            Cleaned stats dictionary
        """
        stats = {
            "player": player_data.get("player", ""),
            "team": player_data.get("team", ""),
            "source_table": source_table,
        }

        # Passing stats
        stats["pass_yds"] = self._safe_int(player_data.get("pass_yds", 0))
        stats["pass_att"] = self._safe_int(player_data.get("pass_att", 0))
        stats["pass_cmp"] = self._safe_int(player_data.get("pass_cmp", 0))
        stats["pass_td"] = self._safe_int(player_data.get("pass_td", 0))

        # Rushing stats
        stats["rush_yds"] = self._safe_int(player_data.get("rush_yds", 0))
        stats["rush_att"] = self._safe_int(player_data.get("rush_att", 0))
        stats["rush_td"] = self._safe_int(player_data.get("rush_td", 0))

        # Receiving stats
        stats["rec"] = self._safe_int(player_data.get("rec", 0))
        stats["rec_yds"] = self._safe_int(player_data.get("rec_yds", 0))
        stats["rec_td"] = self._safe_int(player_data.get("rec_td", 0))
        stats["targets"] = self._safe_int(player_data.get("targets", 0))

        return stats

    def _safe_int(self, value: Any) -> int:
        """Safely convert value to int."""
        if value is None or value == "" or value == "-":
            return 0
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return 0

    def calculate_recent_averages(
        self,
        game_logs: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate per-game averages from game logs.

        Args:
            game_logs: List of game stat dictionaries

        Returns:
            Dictionary with per-game averages
        """
        if not game_logs:
            return {}

        num_games = len(game_logs)

        # Sum up all stats
        totals = {
            "pass_yds": 0,
            "pass_att": 0,
            "pass_cmp": 0,
            "pass_td": 0,
            "rush_yds": 0,
            "rush_att": 0,
            "rush_td": 0,
            "rec": 0,
            "rec_yds": 0,
            "rec_td": 0,
            "targets": 0,
        }

        for game in game_logs:
            for key in totals:
                totals[key] += game.get(key, 0)

        # Calculate averages (matching StatAggregator field names)
        averages = {
            "pass_yds_per_g": totals["pass_yds"] / num_games,
            "pass_att_per_g": totals["pass_att"] / num_games,
            "pass_cmp_per_g": totals["pass_cmp"] / num_games,
            "pass_td_per_g": totals["pass_td"] / num_games,
            "rush_yds_per_g": totals["rush_yds"] / num_games,
            "rush_att_per_g": totals["rush_att"] / num_games,
            "rush_td_per_g": totals["rush_td"] / num_games,
            "rec_per_g": totals["rec"] / num_games,
            "rec_yds_per_g": totals["rec_yds"] / num_games,
            "rec_td_per_g": totals["rec_td"] / num_games,
            "targets_per_g": totals["targets"] / num_games,
        }

        return averages

    def get_data_freshness_days(self) -> int:
        """Get how many days since the last result was fetched.

        Returns:
            Number of days since last result, or -1 if no results
        """
        from datetime import datetime

        all_dates = self.results_repo.get_all_result_dates()
        if not all_dates:
            return -1

        latest_date = datetime.strptime(all_dates[0], "%Y-%m-%d")
        days_old = (datetime.now() - latest_date).days

        return days_old
