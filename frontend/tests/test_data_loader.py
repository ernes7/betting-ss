"""Unit tests for DataLoader."""

import pytest
import json
from pathlib import Path

from frontend.utils import (
    DataLoader,
    format_date,
    load_all_predictions,
    load_all_analyses,
    merge_predictions_with_analyses,
)
from frontend import StreamlitServiceConfig


class TestFormatDate:
    """Tests for format_date function."""

    def test_format_date_valid(self):
        """Test formatting valid date string."""
        result = format_date("2024-11-24")
        assert result == "Nov-24"

    def test_format_date_invalid(self):
        """Test formatting invalid date string."""
        result = format_date("invalid")
        assert result == "invalid"

    def test_format_date_different_month(self):
        """Test formatting dates in different months."""
        assert format_date("2024-01-15") == "Jan-15"
        assert format_date("2024-06-01") == "Jun-01"
        assert format_date("2024-12-31") == "Dec-31"


class TestDataLoaderInit:
    """Tests for DataLoader initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default configuration."""
        loader = DataLoader()

        assert loader.config is not None
        assert loader.base_dir is not None

    def test_init_with_custom_config(self, test_config):
        """Test initialization with custom configuration."""
        loader = DataLoader(config=test_config)

        assert loader.config == test_config

    def test_init_with_custom_base_dir(self, tmp_path):
        """Test initialization with custom base directory."""
        loader = DataLoader(base_dir=tmp_path)

        assert loader.base_dir == tmp_path


class TestDataLoaderLoadPredictions:
    """Tests for loading predictions."""

    def test_load_predictions_empty_dir(self, temp_data_dir):
        """Test loading predictions from empty directory."""
        loader = DataLoader(base_dir=temp_data_dir)

        predictions = loader.load_predictions("nfl")

        # Empty directory returns empty list
        assert isinstance(predictions, list)

    def test_load_predictions_with_files(self, populated_data_dir):
        """Test loading predictions from populated directory."""
        loader = DataLoader(base_dir=populated_data_dir)

        predictions = loader.load_predictions("nfl")

        assert len(predictions) == 1
        assert predictions[0]['game_key'] == 'nyg_dal'
        assert predictions[0]['game_date'] == '2024-11-24'
        assert predictions[0]['ai_prediction'] is not None
        assert predictions[0]['ev_prediction'] is not None
        assert predictions[0]['has_both'] is True

    def test_load_predictions_groups_ai_ev(self, temp_data_dir, sample_ai_prediction, sample_ev_prediction):
        """Test that AI and EV predictions are grouped together."""
        pred_dir = temp_data_dir / "sports" / "nfl" / "data" / "predictions" / "2024-11-24"

        with open(pred_dir / "game1_ai.json", "w") as f:
            json.dump(sample_ai_prediction, f)
        with open(pred_dir / "game1_ev.json", "w") as f:
            json.dump(sample_ev_prediction, f)

        loader = DataLoader(base_dir=temp_data_dir)
        predictions = loader.load_predictions("nfl")

        assert len(predictions) == 1
        assert predictions[0]['has_both'] is True

    def test_load_predictions_separate_games(self, temp_data_dir, sample_ai_prediction):
        """Test loading predictions for separate games."""
        pred_dir = temp_data_dir / "sports" / "nfl" / "data" / "predictions" / "2024-11-24"

        with open(pred_dir / "game1_ai.json", "w") as f:
            json.dump(sample_ai_prediction, f)
        with open(pred_dir / "game2_ai.json", "w") as f:
            json.dump(sample_ai_prediction, f)

        loader = DataLoader(base_dir=temp_data_dir)
        predictions = loader.load_predictions("nfl")

        assert len(predictions) == 2


class TestDataLoaderLoadAnalyses:
    """Tests for loading analyses."""

    def test_load_analyses_empty(self, temp_data_dir):
        """Test loading analyses from empty directory."""
        loader = DataLoader(base_dir=temp_data_dir)

        analyses = loader.load_analyses("nfl")

        assert isinstance(analyses, dict)
        assert len(analyses) == 0

    def test_load_analyses_with_files(self, populated_data_dir):
        """Test loading analyses from populated directory."""
        loader = DataLoader(base_dir=populated_data_dir)

        analyses = loader.load_analyses("nfl")

        assert len(analyses) == 1
        assert "nyg_dal" in analyses


class TestDataLoaderMerge:
    """Tests for merging predictions with analyses."""

    def test_merge_with_matching_analysis(self, populated_data_dir):
        """Test merging predictions with matching analysis."""
        loader = DataLoader(base_dir=populated_data_dir)

        predictions = loader.load_predictions("nfl")
        analyses = loader.load_analyses("nfl")
        merged = loader.merge_predictions_analyses(predictions, analyses)

        assert len(merged) == 1
        assert merged[0]['analysis'] is not None
        assert 'ai_system' in merged[0]['analysis']

    def test_merge_without_analysis(self, temp_data_dir, sample_ai_prediction):
        """Test merging predictions without analysis."""
        pred_dir = temp_data_dir / "sports" / "nfl" / "data" / "predictions" / "2024-11-24"
        with open(pred_dir / "nyg_dal_ai.json", "w") as f:
            json.dump(sample_ai_prediction, f)

        loader = DataLoader(base_dir=temp_data_dir)

        predictions = loader.load_predictions("nfl")
        analyses = loader.load_analyses("nfl")
        merged = loader.merge_predictions_analyses(predictions, analyses)

        assert merged[0]['analysis'] is None

    def test_merge_extracts_teams(self, populated_data_dir):
        """Test that merging extracts team info."""
        loader = DataLoader(base_dir=populated_data_dir)

        data = loader.load_all_data("nfl")

        assert data[0].get('teams') is not None

    def test_merge_sets_generated_at(self, populated_data_dir):
        """Test that merging sets generated_at timestamp."""
        loader = DataLoader(base_dir=populated_data_dir)

        data = loader.load_all_data("nfl")

        assert 'generated_at' in data[0]


class TestDataLoaderLoadAllData:
    """Tests for load_all_data convenience method."""

    def test_load_all_data(self, populated_data_dir):
        """Test loading and merging all data."""
        loader = DataLoader(base_dir=populated_data_dir)

        data = loader.load_all_data("nfl")

        assert len(data) == 1
        assert data[0]['analysis'] is not None
        assert data[0]['has_both'] is True
