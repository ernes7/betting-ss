"""Unit tests for StatsFetcher."""

import pytest
from unittest.mock import MagicMock, patch
import pandas as pd

from services.stats import StatsFetcher, StatsServiceConfig, get_default_config
from shared.errors import StatsFetchError


class TestStatsFetcherInit:
    """Tests for StatsFetcher initialization."""

    def test_init_with_config(self, test_stats_config):
        """Test initialization with config."""
        fetcher = StatsFetcher(config=test_stats_config, sport="nfl")

        assert fetcher.config == test_stats_config
        assert fetcher.sport == "nfl"
        assert fetcher.scraper is not None

    def test_init_normalizes_sport(self, test_stats_config):
        """Test that sport is normalized to lowercase."""
        fetcher = StatsFetcher(config=test_stats_config, sport="NFL")
        assert fetcher.sport == "nfl"

    def test_init_with_default_config(self):
        """Test initialization with default config."""
        fetcher = StatsFetcher(sport="nfl")

        assert fetcher.sport == "nfl"
        assert fetcher.config is not None


class TestStatsFetcherDataframeConversion:
    """Tests for DataFrame conversion."""

    def test_dataframe_to_dict(self, stats_fetcher):
        """Test converting DataFrame to dict format."""
        df = pd.DataFrame({
            "col1": [1, 2, 3],
            "col2": ["a", "b", "c"]
        })

        result = stats_fetcher._dataframe_to_dict(df, "test_table")

        assert result["table_name"] == "test_table"
        assert result["columns"] == ["col1", "col2"]
        assert len(result["data"]) == 3
        assert result["data"][0] == {"col1": 1, "col2": "a"}

    def test_dataframe_to_dict_multiindex(self, stats_fetcher):
        """Test converting DataFrame with MultiIndex columns."""
        df = pd.DataFrame({
            ("Level1", "col1"): [1, 2],
            ("Level1", "col2"): [3, 4]
        })

        result = stats_fetcher._dataframe_to_dict(df, "test_table")

        # MultiIndex should be flattened
        assert all("_" in col or col.startswith("Level1") for col in result["columns"])


class TestStatsFetcherFetchMethods:
    """Tests for fetch methods."""

    def test_fetch_rankings_calls_scraper(self, stats_fetcher, mock_scraper):
        """Test that fetch_rankings calls the scraper."""
        stats_fetcher.scraper = mock_scraper

        result = stats_fetcher.fetch_rankings()

        assert mock_scraper.fetch_html.called
        assert mock_scraper.extract_tables.called
        assert result["sport"] == "nfl"
        assert result["data_type"] == "rankings"

    def test_fetch_defensive_stats_calls_scraper(self, stats_fetcher, mock_scraper):
        """Test that fetch_defensive_stats calls the scraper."""
        stats_fetcher.scraper = mock_scraper

        result = stats_fetcher.fetch_defensive_stats()

        assert mock_scraper.fetch_html.called
        assert result["data_type"] == "defensive"

    def test_fetch_team_profile_calls_scraper(self, stats_fetcher, mock_scraper):
        """Test that fetch_team_profile calls the scraper."""
        stats_fetcher.scraper = mock_scraper

        result = stats_fetcher.fetch_team_profile("dal")

        assert mock_scraper.fetch_html.called
        assert result["team"] == "DAL"
        assert result["data_type"] == "profile"

    def test_fetch_rankings_unknown_sport(self, test_stats_config):
        """Test fetch_rankings with unknown sport raises error."""
        fetcher = StatsFetcher(config=test_stats_config, sport="unknown")

        with pytest.raises(StatsFetchError):
            fetcher.fetch_rankings()


class TestStatsFetcherURLGeneration:
    """Tests for URL generation."""

    def test_team_profile_url_nfl(self):
        """Test NFL team profile URL generation."""
        from services.stats.fetcher import get_team_profile_url

        url = get_team_profile_url("nfl", "dal")

        assert "pro-football-reference.com" in url
        assert "dal" in url
        assert "2025" in url

    def test_team_profile_url_unknown_sport(self):
        """Test unknown sport raises error."""
        from services.stats.fetcher import get_team_profile_url

        with pytest.raises(ValueError):
            get_team_profile_url("unknown", "dal")
