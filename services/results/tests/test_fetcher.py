"""Unit tests for ResultsFetcher."""

import pytest
from unittest.mock import MagicMock, patch
import pandas as pd

from services.results import ResultsFetcher, ResultsServiceConfig, get_default_config
from shared.errors import ResultsFetchError, ResultsParseError


class TestResultsFetcherInit:
    """Tests for ResultsFetcher initialization."""

    def test_init_with_config(self, test_results_config):
        """Test initialization with config."""
        fetcher = ResultsFetcher(config=test_results_config, sport="nfl")

        assert fetcher.config == test_results_config
        assert fetcher.sport == "nfl"
        assert fetcher.parser is not None

    def test_init_normalizes_sport(self, test_results_config):
        """Test that sport is normalized to lowercase."""
        fetcher = ResultsFetcher(config=test_results_config, sport="NFL")
        assert fetcher.sport == "nfl"

    def test_init_with_default_config(self):
        """Test initialization with default config."""
        fetcher = ResultsFetcher(sport="nfl")

        assert fetcher.sport == "nfl"
        assert fetcher.config is not None
        assert "scoring" in fetcher.config.result_tables


class TestResultsFetcherFileHandling:
    """Tests for file-based result extraction."""

    def test_fetch_from_nonexistent_file(self, test_results_config):
        """Test fetching from non-existent file raises error."""
        fetcher = ResultsFetcher(config=test_results_config, sport="nfl")

        with pytest.raises(ResultsFetchError) as exc_info:
            fetcher.fetch_boxscore_from_file("/nonexistent/path.html")

        assert "not found" in str(exc_info.value).lower()


class TestResultsFetcherTableExtraction:
    """Tests for table extraction."""

    def test_dataframe_to_dict(self, mock_fetcher):
        """Test converting DataFrame to dict format."""
        df = pd.DataFrame({
            "col1": [1, 2, 3],
            "col2": ["a", "b", "c"]
        })

        result = mock_fetcher._dataframe_to_dict(df, "test_table")

        assert result["table_name"] == "test_table"
        assert result["columns"] == ["col1", "col2"]
        assert len(result["data"]) == 3
        assert result["data"][0] == {"col1": 1, "col2": "a"}

    def test_dataframe_to_dict_multiindex(self, mock_fetcher):
        """Test converting DataFrame with MultiIndex columns."""
        df = pd.DataFrame({
            ("Level1", "col1"): [1, 2],
            ("Level1", "col2"): [3, 4]
        })

        result = mock_fetcher._dataframe_to_dict(df, "test_table")

        # MultiIndex should be flattened
        assert all("_" in col or col.startswith("Level1") for col in result["columns"])

    def test_find_table_by_columns_scoring(self, mock_fetcher):
        """Test finding scoring table by column pattern."""
        tables = [
            pd.DataFrame({"A": [1], "B": [2]}),
            pd.DataFrame({"1": [0], "2": [7], "3": [3], "4": [10], "Final": [20]}),
        ]

        result = mock_fetcher._find_table_by_columns(tables, "scoring")

        assert result is not None
        assert result["table_name"] == "scoring"

    def test_find_table_by_columns_not_found(self, mock_fetcher):
        """Test finding table when pattern doesn't match."""
        tables = [
            pd.DataFrame({"A": [1], "B": [2]}),
            pd.DataFrame({"C": [3], "D": [4]}),
        ]

        result = mock_fetcher._find_table_by_columns(tables, "scoring")

        assert result is None


class TestResultsFetcherSplitOffense:
    """Tests for player offense splitting."""

    def test_split_player_offense_nfl(self, mock_fetcher, sample_player_offense_data):
        """Test splitting player offense for NFL."""
        result_data = {
            "tables": {
                "player_offense": sample_player_offense_data
            }
        }

        mock_fetcher._split_player_offense(result_data)

        # player_offense should be removed
        assert "player_offense" not in result_data["tables"]

        # Split tables should be added
        assert "passing" in result_data["tables"]
        assert "rushing" in result_data["tables"]
        assert "receiving" in result_data["tables"]


class TestResultsFetcherNBA:
    """Tests for NBA-specific fetching."""

    def test_nba_config(self):
        """Test that NBA config is loaded correctly."""
        config = get_default_config("nba")
        fetcher = ResultsFetcher(config=config, sport="nba")

        assert fetcher.sport == "nba"
        assert "line_score" in fetcher.config.result_tables
        assert "four_factors" in fetcher.config.result_tables


class TestResultsFetcherIntegration:
    """Integration tests for ResultsFetcher."""

    def test_initialize_result_data(self, mock_fetcher):
        """Test result data initialization."""
        result = mock_fetcher._initialize_result_data("http://test.com")

        assert result["sport"] == "nfl"
        assert result["boxscore_url"] == "http://test.com"
        assert result["teams"] == {"away": None, "home": None}
        assert result["final_score"] == {"away": None, "home": None}
        assert result["tables"] == {}
        assert "fetched_at" in result
