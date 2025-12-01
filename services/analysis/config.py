"""Configuration classes for the Analysis service."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class MatchingConfig:
    """Configuration for player name matching.

    Attributes:
        name_similarity_threshold: Minimum similarity ratio for name matching (0.0-1.0)
        check_all_tables: Whether to search all tables if player not found in primary
        normalize_names: Whether to normalize names (remove Jr., III, etc.)
        use_nickname_mapping: Whether to use nickname variants for matching
    """
    name_similarity_threshold: float = 0.85
    check_all_tables: bool = True
    normalize_names: bool = True
    use_nickname_mapping: bool = True


@dataclass(frozen=True)
class ProfitConfig:
    """Configuration for profit calculations.

    Attributes:
        default_stake: Default stake amount per bet
        default_odds: Default American odds when not specified
    """
    default_stake: float = 100.0
    default_odds: int = -110


@dataclass(frozen=True)
class AnalysisServiceConfig:
    """Main configuration for the Analysis service.

    Attributes:
        matching_config: Player name matching configuration
        profit_config: Profit calculation configuration
        data_root: Root path for analysis data (with {sport} placeholder)
        analysis_type: Type of analysis ('analysis' or 'analysis_ev')
        skip_existing: Whether to skip analysis if already exists
        include_pending: Whether to include pending bets in analysis
    """
    matching_config: MatchingConfig = field(default_factory=MatchingConfig)
    profit_config: ProfitConfig = field(default_factory=ProfitConfig)
    data_root: str = "{sport}/data/analysis"
    analysis_type: str = "analysis"
    skip_existing: bool = True
    include_pending: bool = False


def get_default_config() -> AnalysisServiceConfig:
    """Get default analysis service configuration.

    Returns:
        AnalysisServiceConfig with default settings
    """
    return AnalysisServiceConfig()


def get_strict_matching_config() -> AnalysisServiceConfig:
    """Get configuration with strict name matching.

    Returns:
        AnalysisServiceConfig with higher matching threshold
    """
    return AnalysisServiceConfig(
        matching_config=MatchingConfig(
            name_similarity_threshold=0.90,
            check_all_tables=False,
        )
    )


def get_lenient_matching_config() -> AnalysisServiceConfig:
    """Get configuration with lenient name matching.

    Returns:
        AnalysisServiceConfig with lower matching threshold
    """
    return AnalysisServiceConfig(
        matching_config=MatchingConfig(
            name_similarity_threshold=0.75,
            check_all_tables=True,
        )
    )


def get_ev_analysis_config() -> AnalysisServiceConfig:
    """Get configuration for EV-specific analysis.

    Returns:
        AnalysisServiceConfig for EV predictions analysis
    """
    return AnalysisServiceConfig(
        analysis_type="analysis_ev"
    )
