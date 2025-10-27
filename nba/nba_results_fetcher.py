"""NBA-specific results fetcher (placeholder implementation)."""

from shared.base.results_fetcher import ResultsFetcher


class NBAResultsFetcher(ResultsFetcher):
    """NBA results fetcher - placeholder for future implementation."""

    def extract_game_result(self, boxscore_url: str) -> dict:
        """Extract final score and player stats from Basketball-Reference boxscore page.

        Args:
            boxscore_url: URL to the game's boxscore page

        Returns:
            Dictionary with game results

        Note:
            This is a placeholder. Full implementation will be added when NBA
            results fetching is needed.
        """
        raise NotImplementedError(
            "NBA results fetching not yet implemented. "
            "This feature will be added in a future phase."
        )
