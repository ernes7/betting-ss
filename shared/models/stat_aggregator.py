"""Aggregate statistical data from rankings and profiles for EV calculation."""

from typing import Dict, Any, Optional, List
import json
from pathlib import Path
from shared.models.data_loader import DataLoader


class StatAggregator:
    """Loads and aggregates stats from rankings and team profiles."""

    # Common nickname mappings for player name matching
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

    def __init__(self, sport_config, base_dir: str = None):
        """Initialize stat aggregator.

        Args:
            sport_config: Sport-specific configuration object
            base_dir: Base directory for data files (defaults to project root)
        """
        self.sport_config = sport_config
        if base_dir is None:
            base_dir = Path(__file__).parent.parent.parent
        self.base_dir = Path(base_dir)
        self.sport_dir = self.base_dir / sport_config.sport_name
        self.data_dir = self.sport_dir / "data"

        # Initialize DataLoader for cached rankings
        self.data_loader = DataLoader(sport_config, str(base_dir))

    def normalize_player_name(self, name: str) -> str:
        """Normalize player name for matching.

        Handles nicknames, case, and common variations.

        Args:
            name: Player name (e.g., "Joshua Palmer", "Josh Palmer")

        Returns:
            Normalized lowercase name with nickname substitutions
        """
        if not name:
            return ""

        # Convert to lowercase for comparison
        name_lower = name.lower().strip()

        # Split into parts
        parts = name_lower.split()
        if not parts:
            return ""

        # Check first name for nickname mapping
        first_name = parts[0]
        if first_name in self.NICKNAME_MAP:
            parts[0] = self.NICKNAME_MAP[first_name]

        return " ".join(parts)

    def load_team_rankings(self, team_name: str) -> Dict[str, Any]:
        """Load team rankings from all ranking tables.

        Args:
            team_name: Full team name (e.g., "Chicago Bears")

        Returns:
            Dictionary with rankings data for the team
        """
        rankings = {}
        rankings_dir = self.data_dir / "rankings"

        if not rankings_dir.exists():
            return rankings

        # Load all ranking files
        for ranking_file in rankings_dir.glob("*.json"):
            if ranking_file.stem == ".metadata":
                continue

            try:
                with open(ranking_file, 'r') as f:
                    data = json.load(f)

                table_name = data.get("table_name", ranking_file.stem)
                team_data = self._find_team_in_table(data, team_name)

                if team_data:
                    rankings[ranking_file.stem] = team_data

            except Exception as e:
                print(f"Error loading {ranking_file}: {e}")
                continue

        return rankings

    def load_player_stats(self, player_name: str, team_profiles: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Load player statistics from team profiles with fuzzy name matching.

        Checks BOTH passing and rushing_receiving tables and merges stats if player appears in both.
        Uses nickname normalization to match variations like "Joshua" → "Josh".

        Args:
            player_name: Player name to search for (e.g., "Joshua Palmer")
            team_profiles: Loaded team profile data

        Returns:
            Dictionary with player stats or None if not found
        """
        # Normalize the search name for fuzzy matching
        search_name = self.normalize_player_name(player_name)

        # Load both tables
        passing_data = team_profiles.get("passing", {}).get("data", [])
        rush_rec_data = team_profiles.get("rushing_receiving", {}).get("data", [])

        passing_stats = None
        rush_rec_stats = None
        position = None

        # Search in both tables with fuzzy matching
        for player in passing_data:
            profile_name = self.normalize_player_name(player.get("name_display", ""))
            if profile_name == search_name:
                passing_stats = player
                position = player.get("pos", "QB")
                break

        for player in rush_rec_data:
            profile_name = self.normalize_player_name(player.get("name_display", ""))
            if profile_name == search_name:
                rush_rec_stats = player
                position = player.get("pos")
                break

        # If not found in either table, print debug info and return None
        if not passing_stats and not rush_rec_stats:
            print(f"⚠️  Player not found: '{player_name}' (normalized: '{search_name}')")
            available_players = self._list_available_players(team_profiles)
            if available_players:
                print(f"    Available players in profile: {', '.join(available_players[:5])}{'...' if len(available_players) > 5 else ''}")
            return None

        # Merge stats from both tables
        merged_stats = {}
        if passing_stats:
            merged_stats.update(passing_stats)
        if rush_rec_stats:
            merged_stats.update(rush_rec_stats)  # This overwrites with rushing/receiving stats

        # Determine source based on what we found
        if passing_stats and rush_rec_stats:
            source = "both"
        elif passing_stats:
            source = "passing"
        else:
            source = "rushing_receiving"

        return {
            "source": source,
            "stats": merged_stats,
            "position": position
        }

    def _list_available_players(self, team_profile: Dict[str, Any]) -> List[str]:
        """List all player names in profile for debugging.

        Args:
            team_profile: Team profile dictionary

        Returns:
            List of player names found in the profile
        """
        players = []

        # Check passing table
        passing_data = team_profile.get("passing", {}).get("data", [])
        for player in passing_data:
            name = player.get("name_display", "")
            if name:
                players.append(name)

        # Check rushing/receiving table
        rush_rec_data = team_profile.get("rushing_receiving", {}).get("data", [])
        for player in rush_rec_data:
            name = player.get("name_display", "")
            if name and name not in players:  # Avoid duplicates
                players.append(name)

        # Check defense table (for defensive TDs, etc.)
        defense_data = team_profile.get("defense_fumbles", {}).get("data", [])
        for player in defense_data:
            name = player.get("name_display", player.get("player", ""))
            if name and name not in players:
                players.append(name)

        return players

    def load_team_profile(self, team_name: str) -> Dict[str, Any]:
        """Load complete team profile.

        Args:
            team_name: Team name (any format - will be normalized)

        Returns:
            Dictionary with all team profile tables
        """
        profile = {}
        # Normalize team name and get directory name
        team_dir_name = self.data_loader.get_profile_dir_name(team_name)
        profile_dir = self.data_dir / "profiles" / team_dir_name

        if not profile_dir.exists():
            print(f"Warning: Profile directory not found: {profile_dir}")
            return profile

        # Load all profile tables
        profile_files = [
            "passing.json",
            "rushing_receiving.json",
            "injury_report.json",
            "team_stats.json",
            "schedule_results.json",
            "scoring_summary.json",
            "touchdown_log.json",
            "defense_fumbles.json"
        ]

        for filename in profile_files:
            file_path = profile_dir / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    profile[filename.replace(".json", "")] = data
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")

        return profile

    def get_player_averages(self, player_stats: Dict[str, Any]) -> Dict[str, float]:
        """Calculate player averages from stats.

        Args:
            player_stats: Player statistics dictionary

        Returns:
            Dictionary with calculated averages
        """
        stats = player_stats.get("stats", {})
        position = player_stats.get("position", "")
        averages = {}

        try:
            # Parse games played
            games = float(stats.get("games", 1) or 1)
            if games == 0:
                games = 1

            # Always populate ALL stat fields (even if 0) to ensure validator can find them
            # Passing stats
            averages["pass_yds_per_g"] = float(stats.get("pass_yds_per_g", 0) or 0)
            averages["pass_cmp_per_g"] = float(stats.get("pass_cmp", 0) or 0) / games
            averages["pass_att_per_g"] = float(stats.get("pass_att", 0) or 0) / games
            averages["pass_td_per_g"] = float(stats.get("pass_td", 0) or 0) / games

            # Rushing stats
            averages["rush_yds_per_g"] = float(stats.get("rush_yds_per_g", 0) or 0)
            averages["rush_att_per_g"] = float(stats.get("rush_att_per_g", 0) or 0)
            averages["rush_td_per_g"] = float(stats.get("rush_td", 0) or 0) / games

            # Receiving stats
            averages["rec_yds_per_g"] = float(stats.get("rec_yds_per_g", 0) or 0)
            averages["rec_per_g"] = float(stats.get("rec_per_g", 0) or 0)
            averages["rec_td_per_g"] = float(stats.get("rec_td", 0) or 0) / games
            averages["targets_per_g"] = float(stats.get("targets", 0) or 0) / games

        except (ValueError, TypeError) as e:
            print(f"Error calculating averages: {e}")

        return averages

    def check_injury_status(self, player_name: str, injury_report: Dict[str, Any]) -> str:
        """Check if player is injured.

        Args:
            player_name: Player name to check
            injury_report: Injury report data from team profile

        Returns:
            Injury status: "healthy", "out", "questionable", "injured_reserve"
        """
        injury_data = injury_report.get("data", [])

        for injury in injury_data:
            if injury.get("player", "").lower() == player_name.lower():
                status = injury.get("status", "").lower()

                if "out" in status:
                    return "out"
                elif "injured reserve" in status or "ir" in status:
                    return "injured_reserve"
                elif "questionable" in status or "doubtful" in status:
                    return "questionable"

        return "healthy"

    def get_opponent_defense_rank(self, opponent_team: str, rankings: Dict[str, Any], category: str = "passing") -> Optional[int]:
        """Get opponent's defensive ranking.

        Args:
            opponent_team: Opponent team name (any format)
            rankings: All rankings data (DEPRECATED - now using cached data)
            category: Defense category ("passing", "rushing", "scoring")

        Returns:
            Defensive rank (1-32) or None if not found
        """
        # Use DataLoader's cached defense rankings
        return self.data_loader.get_defense_rank(opponent_team, category)

    def get_team_offense_rank(self, team_name: str, rankings: Dict[str, Any], category: str = "passing") -> Optional[int]:
        """Get team's offensive ranking.

        Args:
            team_name: Team name (any format)
            rankings: All rankings data (DEPRECATED - now using cached data)
            category: Offense category ("passing", "rushing", "overall")

        Returns:
            Offensive rank (1-32) or None if not found
        """
        # Use DataLoader's cached offense rankings
        return self.data_loader.get_offense_rank(team_name, category)

    def apply_conservative_adjustment(self, probability: float, adjustment_factor: float = 0.85) -> float:
        """Apply conservative adjustment to probability (reduce by 10-15%).

        Args:
            probability: Original probability (0-100)
            adjustment_factor: Multiplication factor (0.85 = 15% reduction, 0.90 = 10% reduction)

        Returns:
            Adjusted probability
        """
        return probability * adjustment_factor

    def _find_team_in_table(self, table_data: Dict[str, Any], team_name: str) -> Optional[Dict[str, Any]]:
        """Find team data in a ranking table.

        Args:
            table_data: Table JSON data
            team_name: Team name to search for

        Returns:
            Team's data row or None if not found
        """
        data_rows = table_data.get("data", [])

        for row in data_rows:
            if row.get("team", "").lower() == team_name.lower():
                return row

        return None

    def get_team_scoring_average(self, team_name: str) -> float:
        """Get team's scoring average from rankings.

        Args:
            team_name: Team name (any format)

        Returns:
            Points per game average
        """
        # Use DataLoader's cached scoring data
        ppg = self.data_loader.get_team_stat(
            team_name,
            "scoring_offense",
            "points_per_g",
            default=20.0
        )
        return ppg if ppg is not None else 20.0

    def get_team_points_allowed_per_game(self, team_name: str) -> float:
        """Get team's defensive points allowed per game.

        Args:
            team_name: Team name (any format)

        Returns:
            Points allowed per game
        """
        return self.data_loader.get_team_points_allowed_per_game(team_name)

    def get_injured_players(self, team_profile: Dict[str, Any]) -> List[str]:
        """Get list of injured players from team profile.

        Args:
            team_profile: Team profile dictionary

        Returns:
            List of injured player names
        """
        injured = []
        injury_report = team_profile.get("injury_report", {})
        injury_data = injury_report.get("data", [])

        for injury in injury_data:
            status = injury.get("status", "").lower()
            if "out" in status or "injured reserve" in status or "ir" in status:
                injured.append(injury.get("player", ""))

        return injured

    def get_injured_receivers(self, team_profile: Dict[str, Any]) -> List[str]:
        """Get list of injured WRs/TEs from team profile.

        Args:
            team_profile: Team profile dictionary

        Returns:
            List of injured receiver names
        """
        injured = []
        injury_report = team_profile.get("injury_report", {})
        injury_data = injury_report.get("data", [])

        for injury in injury_data:
            status = (injury.get("status") or "").lower()
            pos = (injury.get("pos") or "").upper()

            if ("out" in status or "injured reserve" in status or "ir" in status):
                if pos in ["WR", "TE"]:
                    injured.append(injury.get("player", ""))

        return injured

    def get_injured_ol(self, team_profile: Dict[str, Any]) -> List[str]:
        """Get list of injured offensive linemen from team profile.

        Args:
            team_profile: Team profile dictionary

        Returns:
            List of injured OL names
        """
        injured = []
        injury_report = team_profile.get("injury_report", {})
        injury_data = injury_report.get("data", [])

        for injury in injury_data:
            status = (injury.get("status") or "").lower()
            pos = (injury.get("pos") or "").upper()

            if ("out" in status or "injured reserve" in status or "ir" in status):
                if pos in ["OL", "T", "G", "C", "OT", "OG"]:
                    injured.append(injury.get("player", ""))

        return injured

    def get_defense_pressure_rate(self, team_name: str) -> float:
        """Get defensive pressure rate percentage.

        Args:
            team_name: Team name (any format)

        Returns:
            Pressure percentage (0-100)
        """
        return self.data_loader.get_defense_pressure_rate(team_name)

    def get_defense_sack_total(self, team_name: str) -> int:
        """Get total sacks for a defense.

        Args:
            team_name: Team name (any format)

        Returns:
            Total sacks
        """
        return self.data_loader.get_defense_sack_total(team_name)

    def get_defense_blitz_rate(self, team_name: str) -> float:
        """Get defensive blitz rate percentage.

        Args:
            team_name: Team name (any format)

        Returns:
            Blitz percentage (0-100)
        """
        return self.data_loader.get_defense_blitz_rate(team_name)

    def get_team_drive_efficiency(self, team_name: str) -> Dict[str, float]:
        """Get team drive efficiency stats from team profile.

        Args:
            team_name: Team name (any format)

        Returns:
            Dict with score_pct, turnover_pct, yards_per_drive, points_avg
        """
        profile = self.load_team_profile(team_name)
        team_stats = profile.get("team_stats", {})
        data = team_stats.get("data", [])

        if not data:
            return {
                "score_pct": 35.0,  # League average
                "turnover_pct": 12.0,
                "yards_per_drive": 30.0,
                "points_avg": 2.0
            }

        team_data = data[0]  # First row is team stats
        return {
            "score_pct": self._safe_percent(team_data.get("score_pct"), 35.0),
            "turnover_pct": self._safe_percent(team_data.get("turnover_pct"), 12.0),
            "yards_per_drive": self._safe_float_stat(team_data.get("yds_per_drive"), 30.0),
            "points_avg": self._safe_float_stat(team_data.get("points_avg"), 2.0)
        }

    def _safe_percent(self, value: Any, default: float) -> float:
        """Convert percentage string to float.

        Args:
            value: Value like "35.2%" or 35.2
            default: Default value

        Returns:
            Float percentage
        """
        if value is None or value == "":
            return default

        try:
            if isinstance(value, str) and "%" in value:
                return float(value.replace("%", ""))
            return float(value)
        except (ValueError, TypeError):
            return default

    def _safe_float_stat(self, value: Any, default: float) -> float:
        """Convert stat to float.

        Args:
            value: Stat value
            default: Default value

        Returns:
            Float value
        """
        if value is None or value == "":
            return default

        try:
            return float(value)
        except (ValueError, TypeError):
            return default
