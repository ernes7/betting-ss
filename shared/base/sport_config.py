"""Abstract base class for sport-specific configuration."""

from abc import ABC, abstractmethod
from typing import Any


class SportConfig(ABC):
    """Abstract base class defining the interface for sport configurations.

    Each sport must implement this interface to provide sport-specific:
    - Team metadata
    - Table mappings for scraping
    - URLs and rate limits
    - Data storage paths
    - Prompt components
    """

    @property
    @abstractmethod
    def sport_name(self) -> str:
        """Return the sport name (e.g., 'nfl', 'nba', 'nhl')."""
        pass

    @property
    @abstractmethod
    def teams(self) -> list[dict[str, Any]]:
        """Return list of team dictionaries with metadata."""
        pass

    @property
    @abstractmethod
    def ranking_tables(self) -> dict[str, str]:
        """Return mapping of table names to HTML table IDs for rankings."""
        pass

    @property
    @abstractmethod
    def profile_tables(self) -> dict[str, str]:
        """Return mapping of table names to HTML table IDs for team profiles."""
        pass

    @property
    @abstractmethod
    def stats_url(self) -> str:
        """Return the main stats/rankings URL for the sport."""
        pass

    @property
    @abstractmethod
    def rate_limit_calls(self) -> int:
        """Return number of calls allowed per rate limit period."""
        pass

    @property
    @abstractmethod
    def rate_limit_period(self) -> int:
        """Return rate limit period in seconds."""
        pass

    @property
    @abstractmethod
    def data_rankings_dir(self) -> str:
        """Return directory path for rankings data."""
        pass

    @property
    @abstractmethod
    def data_profiles_dir(self) -> str:
        """Return directory path for profile data."""
        pass

    @property
    @abstractmethod
    def prompt_components(self) -> Any:
        """Return sport-specific prompt components object."""
        pass

    @abstractmethod
    def build_team_url(self, team_abbr: str) -> str:
        """Build team-specific URL using sport's URL pattern.

        Args:
            team_abbr: Team abbreviation specific to the sport's reference site

        Returns:
            Complete URL for the team's page
        """
        pass

    def get_team_by_name(self, team_name: str) -> dict[str, Any] | None:
        """Get team metadata by full team name.

        Args:
            team_name: Full team name (e.g., "Miami Dolphins")

        Returns:
            Team dictionary or None if not found
        """
        for team in self.teams:
            if team["name"].lower() == team_name.lower():
                return team
        return None
