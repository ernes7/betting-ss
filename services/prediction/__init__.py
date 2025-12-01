"""PREDICTION service for generating betting predictions.

This service generates betting predictions using two methods:
1. EV Calculator - Statistical model (free, fast)
2. AI Predictor - Claude API analysis (costs money, more nuanced)

Example:
    from services.prediction import PredictionService

    service = PredictionService(sport="nfl", sport_config=config)
    result = service.predict_game(
        game_date="2024-11-24",
        away_team="Giants",
        home_team="Cowboys",
        odds=odds_data,
    )
"""

from services.prediction.config import (
    PredictionServiceConfig,
    EVConfig,
    AIConfig,
    OddsFilterConfig,
    get_default_config,
    get_ev_only_config,
    get_aggressive_config,
    get_conservative_config,
)
from services.prediction.ev_predictor import EVPredictor
from services.prediction.ai_predictor import AIPredictor
from services.prediction.service import PredictionService


__all__ = [
    # Main service
    "PredictionService",
    # Predictors
    "EVPredictor",
    "AIPredictor",
    # Configuration
    "PredictionServiceConfig",
    "EVConfig",
    "AIConfig",
    "OddsFilterConfig",
    "get_default_config",
    "get_ev_only_config",
    "get_aggressive_config",
    "get_conservative_config",
]
