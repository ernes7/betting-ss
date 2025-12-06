"""Abstract base class for sport-specific configuration."""

from abc import ABC, abstractmethod
from typing import Any, Callable


class SportConfig(ABC):
    """Abstract base class defining the interface for sport configurations.

    Each sport must implement this interface to provide sport-specific:
    - Table mappings for scraping
    - Rate limits
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
    def profile_tables(self) -> dict[str, str]:
        """Return mapping of table names to HTML table IDs for team profiles."""
        pass

    @property
    @abstractmethod
    def result_tables(self) -> dict[str, str]:
        """Return mapping of table names to HTML table IDs for game results/boxscores."""
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
    def predictions_dir(self) -> str:
        """Return directory path for predictions."""
        pass

    @property
    @abstractmethod
    def results_dir(self) -> str:
        """Return directory path for results."""
        pass

    @property
    @abstractmethod
    def analysis_dir(self) -> str:
        """Return directory path for analysis (future use)."""
        pass

    @property
    @abstractmethod
    def prompt_components(self) -> Any:
        """Return sport-specific prompt components object."""
        pass

    @abstractmethod
    def build_boxscore_url(self, game_date: str, home_team_abbr: str) -> str:
        """Build URL for game boxscore/results page.

        Args:
            game_date: Game date in YYYY-MM-DD format
            home_team_abbr: Home team abbreviation

        Returns:
            Complete URL for the game's boxscore page
        """
        pass

    @property
    def prompt_builder(self) -> Callable | None:
        """Optional sport-specific prompt builder function.

        Override this to provide a custom prompt builder for the sport.
        If None, the default shared PromptBuilder will be used.

        Returns:
            Callable that builds a prompt string, or None for default behavior.
        """
        return None
