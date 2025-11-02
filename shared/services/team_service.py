"""Team service for centralized team-related operations.

This module provides a unified interface for team selection, validation,
and abbreviation conversion across all sports.
"""

from typing import List, Dict, Optional
import inquirer


class TeamService:
    """Service for team-related operations."""

    def __init__(self, teams: List[Dict[str, str]], team_names: List[str]):
        """Initialize the team service.

        Args:
            teams: List of team dictionaries with metadata
            team_names: Sorted list of team names for display
        """
        self.teams = teams
        self.team_names = team_names

        # Build lookup maps for efficient access
        self._name_to_team = {team["name"]: team for team in teams}
        self._abbr_to_team = {team["abbreviation"]: team for team in teams}

    def select_team_interactive(self, prompt: str = "Select a team") -> Optional[str]:
        """Display team list with arrow key navigation.

        Args:
            prompt: Custom prompt message to display

        Returns:
            Selected team name, or None if cancelled
        """
        questions = [
            inquirer.List(
                "team",
                message=prompt,
                choices=self.team_names,
            ),
        ]
        answers = inquirer.prompt(questions)
        return answers["team"] if answers else None

    def get_team_abbreviation(self, team_name: str, lowercase: bool = True) -> str:
        """Get team abbreviation from team name.

        Args:
            team_name: Full team name (e.g., "Miami Dolphins")
            lowercase: If True, return lowercase abbreviation

        Returns:
            Team abbreviation (e.g., "mia" or "MIA")

        Raises:
            ValueError: If team name is not found
        """
        team = self._name_to_team.get(team_name)
        if not team:
            # Fallback to normalized full name if not found
            abbr = team_name.replace(" ", "_")
        else:
            abbr = team["abbreviation"]

        return abbr.lower() if lowercase else abbr

    def get_team_full_name(self, abbreviation: str) -> str:
        """Get full team name from abbreviation.

        Args:
            abbreviation: Team abbreviation (case-insensitive)

        Returns:
            Full team name

        Raises:
            ValueError: If abbreviation is not found
        """
        # Try uppercase first (standard format)
        team = self._abbr_to_team.get(abbreviation.upper())
        if not team:
            raise ValueError(f"Unknown team abbreviation: {abbreviation}")
        return team["name"]

    def get_team_pfr_abbreviation(self, team_name: str) -> str:
        """Get Pro Football Reference abbreviation for a team.

        Args:
            team_name: Full team name

        Returns:
            PFR-specific abbreviation (e.g., "mia", "gnb")

        Raises:
            ValueError: If team name is not found
        """
        team = self._name_to_team.get(team_name)
        if not team:
            raise ValueError(f"Unknown team name: {team_name}")
        return team.get("pfr_abbr", team["abbreviation"].lower())

    def validate_team(self, team_name: str) -> bool:
        """Check if a team name is valid.

        Args:
            team_name: Full team name to validate

        Returns:
            True if team exists, False otherwise
        """
        return team_name in self._name_to_team

    def get_team_info(self, team_name: str) -> Optional[Dict[str, str]]:
        """Get complete team information.

        Args:
            team_name: Full team name

        Returns:
            Team dictionary with all metadata, or None if not found
        """
        return self._name_to_team.get(team_name)

    def get_all_teams(self) -> List[Dict[str, str]]:
        """Get list of all teams.

        Returns:
            List of team dictionaries
        """
        return self.teams

    def get_all_team_names(self) -> List[str]:
        """Get sorted list of all team names.

        Returns:
            Sorted list of team names
        """
        return self.team_names


def create_team_service_for_sport(sport_code: str) -> TeamService:
    """Factory function to create a TeamService for a specific sport.

    Args:
        sport_code: Sport code ('nfl', 'nba', etc.)

    Returns:
        Configured TeamService instance

    Raises:
        ValueError: If sport code is not recognized
    """
    if sport_code == "nfl":
        from nfl.teams import TEAMS, TEAM_NAMES
        return TeamService(TEAMS, TEAM_NAMES)
    elif sport_code == "nba":
        from nba.teams import TEAMS, TEAM_NAMES
        return TeamService(TEAMS, TEAM_NAMES)
    else:
        raise ValueError(f"Unsupported sport: {sport_code}")
