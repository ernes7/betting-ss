"""Unit tests for streamlit utility functions."""

import pytest

from frontend.utils import (
    get_profit_color,
    get_win_rate_color,
    get_ev_color,
    get_roi_color,
    get_system_summary,
    detect_analysis_format,
    get_bet_results,
    calculate_combined_metrics,
)


class TestColorFunctions:
    """Tests for color utility functions."""

    def test_get_profit_color_positive(self):
        """Test profit color for positive value."""
        color = get_profit_color(100.0)
        assert color == "#22C55E"  # Green

    def test_get_profit_color_negative(self):
        """Test profit color for negative value."""
        color = get_profit_color(-50.0)
        assert color == "#EF4444"  # Red

    def test_get_profit_color_zero(self):
        """Test profit color for zero value."""
        color = get_profit_color(0.0)
        assert color == "#6B7280"  # Gray

    def test_get_win_rate_color_good(self):
        """Test win rate color for good rate."""
        color = get_win_rate_color(60.0)
        assert color == "#22C55E"  # Green

    def test_get_win_rate_color_breakeven(self):
        """Test win rate color for breakeven rate."""
        color = get_win_rate_color(52.0)
        assert color == "#EAB308"  # Yellow

    def test_get_win_rate_color_losing(self):
        """Test win rate color for losing rate."""
        color = get_win_rate_color(45.0)
        assert color == "#EF4444"  # Red

    def test_get_ev_color_strong_positive(self):
        """Test EV color for strong positive."""
        color = get_ev_color(7.0)
        assert color == "#22C55E"  # Green

    def test_get_ev_color_slight_positive(self):
        """Test EV color for slight positive."""
        color = get_ev_color(2.0)
        assert color == "#EAB308"  # Yellow

    def test_get_ev_color_negative(self):
        """Test EV color for negative."""
        color = get_ev_color(-3.0)
        assert color == "#EF4444"  # Red

    def test_get_roi_color_strong_positive(self):
        """Test ROI color for strong positive."""
        color = get_roi_color(15.0)
        assert color == "#22C55E"  # Green

    def test_get_roi_color_positive(self):
        """Test ROI color for positive."""
        color = get_roi_color(5.0)
        assert color == "#84CC16"  # Light green

    def test_get_roi_color_zero(self):
        """Test ROI color for zero."""
        color = get_roi_color(0.0)
        assert color == "#6B7280"  # Gray

    def test_get_roi_color_negative(self):
        """Test ROI color for negative."""
        color = get_roi_color(-10.0)
        assert color == "#EF4444"  # Red


class TestAnalysisHelpers:
    """Tests for analysis helper functions."""

    def test_get_system_summary_dual_format_ai(self, sample_analysis_dual):
        """Test getting AI summary from dual format."""
        summary = get_system_summary(sample_analysis_dual, 'ai_system')

        assert summary['total_profit'] == 90.91
        assert summary['bets_won'] == 1

    def test_get_system_summary_dual_format_ev(self, sample_analysis_dual):
        """Test getting EV summary from dual format."""
        summary = get_system_summary(sample_analysis_dual, 'ev_system')

        assert summary['total_profit'] == 90.91
        assert summary['bets_won'] == 1

    def test_get_system_summary_legacy_format(self, sample_analysis_legacy):
        """Test getting AI summary from legacy format."""
        summary = get_system_summary(sample_analysis_legacy, 'ai_system')

        assert summary['total_profit'] == 90.91

    def test_get_system_summary_legacy_format_ev(self, sample_analysis_legacy):
        """Test getting EV summary from legacy format (should be empty)."""
        summary = get_system_summary(sample_analysis_legacy, 'ev_system')

        assert summary == {}

    def test_get_system_summary_none(self):
        """Test getting summary from None."""
        summary = get_system_summary(None, 'ai_system')

        assert summary == {}

    def test_detect_analysis_format_dual(self, sample_analysis_dual):
        """Test detecting dual format."""
        result = detect_analysis_format(sample_analysis_dual)

        assert result['format'] == 'dual'
        assert result['ai_analysis'] is not None
        assert result['ev_analysis'] is not None

    def test_detect_analysis_format_legacy(self, sample_analysis_legacy):
        """Test detecting legacy format."""
        result = detect_analysis_format(sample_analysis_legacy)

        assert result['format'] == 'legacy'
        assert result['ai_analysis'] is not None
        assert result['ev_analysis'] is None

    def test_detect_analysis_format_none(self):
        """Test detecting None input."""
        result = detect_analysis_format(None)

        assert result['format'] is None
        assert result['ai_analysis'] is None

    def test_get_bet_results_dual(self, sample_analysis_dual):
        """Test getting bet results from dual format."""
        ai_results = get_bet_results(sample_analysis_dual, 'ai_system')
        ev_results = get_bet_results(sample_analysis_dual, 'ev_system')

        assert len(ai_results) == 1
        assert len(ev_results) == 1

    def test_get_bet_results_legacy(self, sample_analysis_legacy):
        """Test getting bet results from legacy format."""
        ai_results = get_bet_results(sample_analysis_legacy, 'ai_system')
        ev_results = get_bet_results(sample_analysis_legacy, 'ev_system')

        assert len(ai_results) == 1
        assert len(ev_results) == 0

    def test_get_bet_results_none(self):
        """Test getting bet results from None."""
        results = get_bet_results(None, 'ai_system')

        assert results == []

    def test_calculate_combined_metrics(self, sample_analysis_dual):
        """Test calculating combined metrics."""
        metrics = calculate_combined_metrics(sample_analysis_dual)

        assert metrics['total_profit'] == 181.82  # 90.91 + 90.91
        assert metrics['total_bets'] == 2
        assert metrics['total_won'] == 2
        assert metrics['win_rate'] == 100.0
        assert metrics['ai_profit'] == 90.91
        assert metrics['ev_profit'] == 90.91

    def test_calculate_combined_metrics_none(self):
        """Test calculating combined metrics from None."""
        metrics = calculate_combined_metrics(None)

        assert metrics['total_profit'] == 0
        assert metrics['total_bets'] == 0
        assert metrics['win_rate'] == 0
