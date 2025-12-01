"""Configuration for the Streamlit dashboard service."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class DisplayConfig:
    """Configuration for display settings.

    Attributes:
        page_title: Browser tab title
        page_icon: Favicon emoji
        layout: Streamlit layout mode ('wide' or 'centered')
        cards_per_row: Number of prediction cards per row
        fixed_bet_amount: Fixed amount per bet for calculations
    """
    page_title: str = "Sports Betting Analytics"
    page_icon: str = "🎯"
    layout: str = "wide"
    cards_per_row: int = 3
    fixed_bet_amount: float = 100.0


@dataclass(frozen=True)
class DataPathConfig:
    """Configuration for data paths.

    Attributes:
        predictions_path: Path template for predictions directory
        analysis_path: Path template for analysis directory
        results_path: Path template for results directory
    """
    predictions_path: str = "sports/{sport}/data/predictions"
    analysis_path: str = "sports/{sport}/data/analysis"
    results_path: str = "sports/{sport}/data/results"

    def get_predictions_dir(self, sport: str, base_dir: Optional[Path] = None) -> Path:
        """Get predictions directory path for a sport."""
        base = base_dir or Path(__file__).parent.parent.parent
        return base / self.predictions_path.format(sport=sport)

    def get_analysis_dir(self, sport: str, base_dir: Optional[Path] = None) -> Path:
        """Get analysis directory path for a sport."""
        base = base_dir or Path(__file__).parent.parent.parent
        return base / self.analysis_path.format(sport=sport)

    def get_results_dir(self, sport: str, base_dir: Optional[Path] = None) -> Path:
        """Get results directory path for a sport."""
        base = base_dir or Path(__file__).parent.parent.parent
        return base / self.results_path.format(sport=sport)


@dataclass(frozen=True)
class ThemeConfig:
    """Configuration for theme colors.

    Attributes:
        ai_gradient_bg: Background gradient for AI system
        ai_border_color: Border color for AI system
        ev_gradient_bg: Background gradient for EV system
        ev_border_color: Border color for EV system
        profit_positive: Color for positive profit
        profit_negative: Color for negative profit
        profit_neutral: Color for neutral/zero profit
    """
    ai_gradient_bg: str = "linear-gradient(135deg, rgba(139,92,246,0.1), rgba(167,139,250,0.05))"
    ai_border_color: str = "#8B5CF6"
    ev_gradient_bg: str = "linear-gradient(135deg, rgba(34,197,94,0.1), rgba(74,222,128,0.05))"
    ev_border_color: str = "#22C55E"
    profit_positive: str = "#22C55E"
    profit_negative: str = "#EF4444"
    profit_neutral: str = "#6B7280"


@dataclass(frozen=True)
class StreamlitServiceConfig:
    """Main configuration for the Streamlit dashboard service.

    Attributes:
        display: Display settings
        paths: Data path settings
        theme: Theme color settings
        default_sport: Default sport to display
        enable_nba: Whether to enable NBA data
        enable_nfl: Whether to enable NFL data
    """
    display: DisplayConfig = field(default_factory=DisplayConfig)
    paths: DataPathConfig = field(default_factory=DataPathConfig)
    theme: ThemeConfig = field(default_factory=ThemeConfig)
    default_sport: str = "nfl"
    enable_nba: bool = True
    enable_nfl: bool = True


def get_default_config() -> StreamlitServiceConfig:
    """Get default streamlit service configuration.

    Returns:
        StreamlitServiceConfig with default settings
    """
    return StreamlitServiceConfig()


def get_nfl_only_config() -> StreamlitServiceConfig:
    """Get configuration for NFL only.

    Returns:
        StreamlitServiceConfig with NBA disabled
    """
    return StreamlitServiceConfig(
        default_sport="nfl",
        enable_nba=False,
        enable_nfl=True,
    )


def get_nba_only_config() -> StreamlitServiceConfig:
    """Get configuration for NBA only.

    Returns:
        StreamlitServiceConfig with NFL disabled
    """
    return StreamlitServiceConfig(
        default_sport="nba",
        enable_nba=True,
        enable_nfl=False,
    )
