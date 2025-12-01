"""Configuration for the PREDICTION service."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class EVConfig:
    """Configuration for EV (Expected Value) Calculator.

    Attributes:
        conservative_adjustment: Probability reduction factor (0.85 = 15% reduction)
        min_ev_threshold: Minimum EV percentage to include (0.0 = all positive EV)
        top_n_bets: Number of top bets to return
        deduplicate_players: If True, show only best bet per player
        max_receivers_per_team: Maximum receivers per team to avoid correlation
        min_games_required: Minimum games required for recent form calculation
    """
    conservative_adjustment: float = 0.85
    min_ev_threshold: float = 0.0
    top_n_bets: int = 5
    deduplicate_players: bool = True
    max_receivers_per_team: int = 1
    min_games_required: int = 3


@dataclass(frozen=True)
class AIConfig:
    """Configuration for AI Predictor (Claude API).

    Attributes:
        model: Claude model to use
        max_tokens: Maximum output tokens
        rate_limit_seconds: Seconds to wait between API calls
        input_cost_per_million: Cost per million input tokens
        output_cost_per_million: Cost per million output tokens
    """
    model: str = "claude-sonnet-4-5-20250929"
    max_tokens: int = 2048
    rate_limit_seconds: int = 60
    input_cost_per_million: float = 3.0
    output_cost_per_million: float = 15.0


@dataclass(frozen=True)
class OddsFilterConfig:
    """Configuration for filtering odds before prediction.

    Attributes:
        min_odds: Minimum American odds to include (e.g., -150)
        max_odds: Maximum American odds to include (e.g., 199)
    """
    min_odds: int = -150
    max_odds: int = 199


@dataclass(frozen=True)
class PredictionServiceConfig:
    """Configuration for the PREDICTION service.

    Attributes:
        ev_config: EV Calculator configuration
        ai_config: AI Predictor configuration
        odds_filter: Odds filtering configuration
        data_root: Root directory for prediction data
        use_dual_predictions: Run both EV and AI predictions
        skip_existing: Skip games that already have predictions
    """
    ev_config: EVConfig = field(default_factory=EVConfig)
    ai_config: AIConfig = field(default_factory=AIConfig)
    odds_filter: OddsFilterConfig = field(default_factory=OddsFilterConfig)
    data_root: str = "{sport}/data/predictions"
    use_dual_predictions: bool = True
    skip_existing: bool = True


def get_default_config() -> PredictionServiceConfig:
    """Get default prediction service configuration.

    Returns:
        PredictionServiceConfig with default settings
    """
    return PredictionServiceConfig()


def get_ev_only_config() -> PredictionServiceConfig:
    """Get configuration for EV-only predictions (no AI).

    Returns:
        PredictionServiceConfig with AI disabled
    """
    return PredictionServiceConfig(
        use_dual_predictions=False,
    )


def get_aggressive_config() -> PredictionServiceConfig:
    """Get configuration for aggressive EV predictions.

    Less conservative adjustment, lower EV threshold, more bets.

    Returns:
        PredictionServiceConfig with aggressive settings
    """
    return PredictionServiceConfig(
        ev_config=EVConfig(
            conservative_adjustment=0.90,  # Only 10% reduction
            min_ev_threshold=-2.0,  # Include slightly negative EV
            top_n_bets=10,
            max_receivers_per_team=2,
        ),
    )


def get_conservative_config() -> PredictionServiceConfig:
    """Get configuration for conservative EV predictions.

    More conservative adjustment, higher EV threshold, fewer bets.

    Returns:
        PredictionServiceConfig with conservative settings
    """
    return PredictionServiceConfig(
        ev_config=EVConfig(
            conservative_adjustment=0.80,  # 20% reduction
            min_ev_threshold=3.0,  # Minimum 3% EV
            top_n_bets=3,
            max_receivers_per_team=1,
        ),
    )
