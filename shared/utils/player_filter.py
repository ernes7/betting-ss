"""Filter players for EV calculation based on role and usage."""

from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from shared.models.stat_aggregator import StatAggregator


class PlayerFilter:
    """Filter players for EV calculation based on position and statistical performance.

    Only includes top players by position:
    - Top 2 QBs by passing yards
    - Top 2 RBs by rushing yards
    - Top 3 WRs by receptions
    - Top 2 TEs by receptions
    """

    def __init__(
        self,
        home_profile: Optional[Dict[str, Any]],
        away_profile: Optional[Dict[str, Any]],
        stat_aggregator: Optional["StatAggregator"] = None
    ):
        """Initialize player filter with team profiles.

        Args:
            home_profile: Home team profile data with passing and rushing_receiving tables
            away_profile: Away team profile data with passing and rushing_receiving tables
            stat_aggregator: StatAggregator instance for name normalization (optional)
        """
        self.home_profile = home_profile
        self.away_profile = away_profile
        self.stat_aggregator = stat_aggregator
        self.eligible_players = self._identify_eligible_players()
        # Store both original and normalized names for matching
        self.eligible_players_normalized = self._normalize_eligible_players()

    def _identify_eligible_players(self) -> Dict[str, Dict[str, list]]:
        """Identify top players by position from team profiles.

        Returns:
            Dictionary mapping team ('HOME', 'AWAY') to eligible player names by position
        """
        eligible = {}

        for team_side, profile in [("HOME", self.home_profile), ("AWAY", self.away_profile)]:
            if not profile:
                eligible[team_side] = {"qbs": [], "rbs": [], "wrs": [], "tes": []}
                continue

            # Top 2 QBs by passing yards
            passing_data = profile.get("passing", {}).get("data", [])
            qbs = sorted(
                passing_data,
                key=lambda x: float(x.get("pass_yds", 0) or 0),
                reverse=True
            )[:2]

            # Get rushing_receiving data
            rush_rec_data = profile.get("rushing_receiving", {}).get("data", [])

            # Top 2 RBs by rushing yards
            rbs = [p for p in rush_rec_data if p.get("pos") == "RB"]
            rbs_sorted = sorted(
                rbs,
                key=lambda x: float(x.get("rush_yds", 0) or 0),
                reverse=True
            )[:2]

            # Top 3 WRs by receptions
            wrs = [p for p in rush_rec_data if p.get("pos") == "WR"]
            wrs_sorted = sorted(
                wrs,
                key=lambda x: float(x.get("rec", 0) or 0),
                reverse=True
            )[:3]

            # Top 2 TEs by receptions
            tes = [p for p in rush_rec_data if p.get("pos") == "TE"]
            tes_sorted = sorted(
                tes,
                key=lambda x: float(x.get("rec", 0) or 0),
                reverse=True
            )[:2]

            eligible[team_side] = {
                "qbs": [p.get("name_display") for p in qbs if p.get("name_display")],
                "rbs": [p.get("name_display") for p in rbs_sorted if p.get("name_display")],
                "wrs": [p.get("name_display") for p in wrs_sorted if p.get("name_display")],
                "tes": [p.get("name_display") for p in tes_sorted if p.get("name_display")]
            }

        return eligible

    def _normalize_eligible_players(self) -> Dict[str, Dict[str, list]]:
        """Create normalized versions of eligible player names for fuzzy matching.

        Returns:
            Dictionary mapping team to normalized player names by position
        """
        if not self.stat_aggregator:
            # No normalization available - return empty structure
            return {"HOME": {"qbs": [], "rbs": [], "wrs": [], "tes": []},
                    "AWAY": {"qbs": [], "rbs": [], "wrs": [], "tes": []}}

        normalized = {}
        for team, positions in self.eligible_players.items():
            normalized[team] = {}
            for position, players in positions.items():
                normalized[team][position] = [
                    self.stat_aggregator.normalize_player_name(name)
                    for name in players
                ]
        return normalized

    def is_player_eligible(self, player_name: str, team: str) -> bool:
        """Check if player should be included in EV calculation.

        Uses normalized name matching to handle nickname variations (Josh/Joshua),
        suffix differences (Jr./Sr./III), and case sensitivity.

        Args:
            player_name: Player's display name from odds
            team: Team identifier ('HOME' or 'AWAY')

        Returns:
            True if player is in top N for their position, False otherwise
        """
        team = team.upper()
        if team not in self.eligible_players:
            return False

        # Try exact match first (fast path)
        team_eligible = self.eligible_players[team]
        if (player_name in team_eligible["qbs"] or
            player_name in team_eligible["rbs"] or
            player_name in team_eligible["wrs"] or
            player_name in team_eligible["tes"]):
            return True

        # Fallback to normalized matching if StatAggregator available
        if self.stat_aggregator:
            normalized_name = self.stat_aggregator.normalize_player_name(player_name)
            team_eligible_normalized = self.eligible_players_normalized[team]
            return (
                normalized_name in team_eligible_normalized["qbs"] or
                normalized_name in team_eligible_normalized["rbs"] or
                normalized_name in team_eligible_normalized["wrs"] or
                normalized_name in team_eligible_normalized["tes"]
            )

        return False

    def get_eligible_player_count(self) -> Dict[str, int]:
        """Get count of eligible players by team.

        Returns:
            Dictionary with player counts for HOME and AWAY teams
        """
        counts = {}
        for team, players in self.eligible_players.items():
            counts[team] = sum(len(pos_list) for pos_list in players.values())
        return counts

    def get_eligible_players_summary(self) -> str:
        """Get human-readable summary of eligible players.

        Returns:
            Formatted string showing eligible players by team and position
        """
        lines = []
        for team, players in self.eligible_players.items():
            lines.append(f"{team}:")
            lines.append(f"  QBs: {', '.join(players['qbs']) or 'None'}")
            lines.append(f"  RBs: {', '.join(players['rbs']) or 'None'}")
            lines.append(f"  WRs: {', '.join(players['wrs']) or 'None'}")
            lines.append(f"  TEs: {', '.join(players['tes']) or 'None'}")
        return "\n".join(lines)
