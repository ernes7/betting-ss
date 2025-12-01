"""Analysis service for comparing predictions to results.

This module provides the AnalysisService class and supporting components
for validating bet predictions against actual game outcomes.

Example usage:
    from services.analysis import AnalysisService, get_default_config

    config = get_default_config()
    service = AnalysisService(sport="nfl", config=config)

    # Analyze a single game
    analysis = service.analyze_game(
        game_date="2024-11-24",
        away_team="nyg",
        home_team="dal",
        prediction_data=prediction_json,
        result_data=result_json,
    )

    # Get analysis summary
    print(f"Won: {analysis['summary']['bets_won']}/{analysis['summary']['total_bets']}")
    print(f"Profit: ${analysis['summary']['total_profit']:.2f}")
"""

from services.analysis.config import (
    AnalysisServiceConfig,
    MatchingConfig,
    ProfitConfig,
    get_default_config,
    get_strict_matching_config,
    get_lenient_matching_config,
    get_ev_analysis_config,
)
from services.analysis.bet_checker import BetChecker
from services.analysis.service import AnalysisService


__all__ = [
    # Service
    "AnalysisService",
    # Components
    "BetChecker",
    # Configuration
    "AnalysisServiceConfig",
    "MatchingConfig",
    "ProfitConfig",
    # Factory functions
    "get_default_config",
    "get_strict_matching_config",
    "get_lenient_matching_config",
    "get_ev_analysis_config",
]
