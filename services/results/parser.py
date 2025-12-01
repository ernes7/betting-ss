"""Results parsing utilities for boxscore data.

Parses game results from sports reference sites (Pro-Football-Reference,
Basketball-Reference, etc.).
"""

from typing import Any, Optional, List, Dict

from shared.logging import get_logger
from shared.errors import ResultsParseError


logger = get_logger("results")


class ResultsParser:
    """Parser for game results data.

    Extracts structured data from boxscore tables including:
    - Final scores
    - Team names
    - Player statistics
    - Game information

    Example:
        parser = ResultsParser()
        score = parser.parse_final_score(scoring_table)
        teams = parser.parse_team_names(scoring_table)
    """

    def parse_final_score(self, scoring_data: dict) -> dict[str, int]:
        """Parse final score from scoring table.

        For NFL, the scoring table has vis_team_score and home_team_score columns.
        The final row contains the final scores.

        Args:
            scoring_data: Extracted scoring table data

        Returns:
            Dictionary with away and home scores

        Raises:
            ResultsParseError: If scores cannot be parsed
        """
        if not scoring_data or not scoring_data.get("data"):
            raise ResultsParseError(
                "Scoring table has no data",
                context={"scoring_data": scoring_data}
            )

        rows = scoring_data["data"]

        if len(rows) < 1:
            raise ResultsParseError("Scoring table must have at least 1 row")

        # Get the last row which has the final scores
        last_row = rows[-1]

        away_score = None
        home_score = None

        # NFL format: vis_team_score and home_team_score
        if "vis_team_score" in last_row:
            try:
                away_score = int(last_row["vis_team_score"])
            except (ValueError, TypeError):
                pass

        if "home_team_score" in last_row:
            try:
                home_score = int(last_row["home_team_score"])
            except (ValueError, TypeError):
                pass

        if away_score is None or home_score is None:
            raise ResultsParseError(
                "Could not parse final scores from scoring table",
                context={"last_row": last_row}
            )

        return {"away": away_score, "home": home_score}

    def parse_team_names(self, scoring_data: dict) -> dict[str, Optional[str]]:
        """Parse team names from scoring table.

        Determines home/away by tracking which team's scoring plays
        increase which score column.

        Args:
            scoring_data: Extracted scoring table data

        Returns:
            Dictionary with away and home team names
        """
        teams = {"away": None, "home": None}

        if not scoring_data or not scoring_data.get("data"):
            return teams

        rows = scoring_data["data"]

        for i, row in enumerate(rows):
            if "team" not in row or not row["team"]:
                continue

            team = row["team"]

            if i > 0:
                prev_row = rows[i - 1]
                curr_vis = self._safe_int(row.get("vis_team_score", 0))
                prev_vis = self._safe_int(prev_row.get("vis_team_score", 0))
                curr_home = self._safe_int(row.get("home_team_score", 0))
                prev_home = self._safe_int(prev_row.get("home_team_score", 0))

                if curr_vis > prev_vis:
                    teams["away"] = team
                elif curr_home > prev_home:
                    teams["home"] = team
            else:
                # First scoring play
                vis_score = self._safe_int(row.get("vis_team_score", 0))
                home_score = self._safe_int(row.get("home_team_score", 0))

                if vis_score > 0 and home_score == 0:
                    teams["away"] = team
                elif home_score > 0 and vis_score == 0:
                    teams["home"] = team

            if teams["home"] and teams["away"]:
                break

        return teams

    def determine_winner(
        self,
        final_score: dict[str, int],
        teams: dict[str, str]
    ) -> str:
        """Determine the winner from final score.

        Args:
            final_score: Dictionary with away and home scores
            teams: Dictionary with away and home team names

        Returns:
            Winner team name or "TIE"
        """
        if final_score["away"] > final_score["home"]:
            return teams.get("away") or "AWAY"
        elif final_score["home"] > final_score["away"]:
            return teams.get("home") or "HOME"
        else:
            return "TIE"

    def split_player_offense(self, player_offense: dict) -> dict[str, Optional[dict]]:
        """Split player_offense table into passing, rushing, receiving.

        NFL boxscores combine all offensive stats into one table.
        This splits them into separate tables based on stat presence.

        Args:
            player_offense: Combined player offense table

        Returns:
            Dictionary with passing, rushing, receiving tables
        """
        result = {
            "passing": None,
            "rushing": None,
            "receiving": None,
        }

        if not player_offense or not player_offense.get("data"):
            return result

        rows = player_offense["data"]
        headers = player_offense.get("headers", [])

        passing_rows = []
        rushing_rows = []
        receiving_rows = []

        for row in rows:
            # Passing: has pass_cmp or pass_att
            if self._has_passing_stats(row):
                passing_rows.append(row)

            # Rushing: has rush_att
            if self._has_rushing_stats(row):
                rushing_rows.append(row)

            # Receiving: has targets or rec
            if self._has_receiving_stats(row):
                receiving_rows.append(row)

        if passing_rows:
            result["passing"] = {
                "table_name": "Passing",
                "headers": headers,
                "data": passing_rows,
            }

        if rushing_rows:
            result["rushing"] = {
                "table_name": "Rushing",
                "headers": headers,
                "data": rushing_rows,
            }

        if receiving_rows:
            result["receiving"] = {
                "table_name": "Receiving",
                "headers": headers,
                "data": receiving_rows,
            }

        return result

    def extract_player_stats(
        self,
        tables: dict[str, dict],
        stat_type: str
    ) -> list[dict]:
        """Extract player statistics from result tables.

        Args:
            tables: Dictionary of extracted tables
            stat_type: Type of stats to extract (passing, rushing, receiving, defense)

        Returns:
            List of player stat dictionaries
        """
        table = tables.get(stat_type)
        if not table or not table.get("data"):
            return []

        return table["data"]

    def get_player_stat(
        self,
        tables: dict[str, dict],
        player_name: str,
        stat_name: str,
        default: Any = 0
    ) -> Any:
        """Get a specific stat for a player.

        Searches through all player tables to find the stat.

        Args:
            tables: Dictionary of extracted tables
            player_name: Player name to search for
            stat_name: Stat column name
            default: Default value if not found

        Returns:
            Stat value or default
        """
        player_tables = ["passing", "rushing", "receiving", "defense"]

        for table_name in player_tables:
            table = tables.get(table_name)
            if not table or not table.get("data"):
                continue

            for row in table["data"]:
                player = row.get("player", row.get("name", ""))
                if player_name.lower() in player.lower():
                    if stat_name in row:
                        return row[stat_name]

        return default

    def _safe_int(self, value: Any) -> int:
        """Safely convert value to int."""
        try:
            return int(value or 0)
        except (ValueError, TypeError):
            return 0

    def _has_passing_stats(self, row: dict) -> bool:
        """Check if row has passing stats."""
        return (
            self._safe_int(row.get("pass_cmp")) > 0 or
            self._safe_int(row.get("pass_att")) > 0
        )

    def _has_rushing_stats(self, row: dict) -> bool:
        """Check if row has rushing stats."""
        return self._safe_int(row.get("rush_att")) > 0

    def _has_receiving_stats(self, row: dict) -> bool:
        """Check if row has receiving stats."""
        return (
            self._safe_int(row.get("targets")) > 0 or
            self._safe_int(row.get("rec")) > 0
        )
