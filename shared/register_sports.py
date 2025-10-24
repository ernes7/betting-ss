"""Register all available sports with the factory."""

from shared.factory import SportFactory


def register_all_sports():
    """Register all sport configurations with the factory."""
    # Import sport configs here to avoid circular imports
    from nfl.nfl_config import NFLConfig
    from nba.nba_config import NBAConfig

    # Register each sport
    SportFactory.register("nfl", NFLConfig)
    SportFactory.register("nba", NBAConfig)


# Auto-register on module import
register_all_sports()
