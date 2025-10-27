"""NBA-specific analyzer (placeholder implementation)."""

from shared.base.analyzer import BaseAnalyzer


class NBAAnalyzer(BaseAnalyzer):
    """NBA analyzer - placeholder for future implementation."""

    def _build_analysis_prompt(self, prediction_data: dict, result_data: dict) -> str:
        """Build NBA-specific analysis prompt for Claude.

        Args:
            prediction_data: Prediction data from JSON file
            result_data: Game results data

        Returns:
            Formatted analysis prompt string

        Note:
            This is a placeholder. Full implementation will be added when NBA
            analysis is needed.
        """
        raise NotImplementedError(
            "NBA analysis not yet implemented. "
            "This feature will be added in a future phase."
        )
