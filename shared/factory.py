"""Factory for creating sport instances."""

from typing import Any


class Sport:
    """Facade class for sport configuration and predictor."""

    def __init__(self, config: Any):
        """Initialize sport with configuration.

        Args:
            config: Sport configuration object
        """
        from shared.base import Predictor

        self.config = config
        self.predictor = Predictor(config)


class SportFactory:
    """Factory for creating sport instances."""

    _registry = {}

    @classmethod
    def register(cls, sport_name: str, config_class: type):
        """Register a sport configuration class.

        Args:
            sport_name: Name of the sport (e.g., 'nfl', 'nba')
            config_class: Configuration class for the sport
        """
        cls._registry[sport_name.lower()] = config_class

    @classmethod
    def create(cls, sport_name: str) -> Sport:
        """Create a sport instance by name.

        Args:
            sport_name: Name of the sport (e.g., 'nfl', 'nba', 'nhl', 'mlb')

        Returns:
            Sport instance with scraper and predictor

        Raises:
            ValueError: If sport_name is not registered
        """
        sport_name = sport_name.lower()

        if sport_name not in cls._registry:
            available = ", ".join(cls._registry.keys())
            raise ValueError(
                f"Unknown sport: '{sport_name}'. Available sports: {available}"
            )

        config_class = cls._registry[sport_name]
        config = config_class()
        return Sport(config)

    @classmethod
    def available_sports(cls) -> list[str]:
        """Get list of available sport names.

        Returns:
            List of registered sport names
        """
        return sorted(cls._registry.keys())
