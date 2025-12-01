"""Unit tests for ResultsFetcher."""

import pytest
from unittest.mock import MagicMock, patch

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


class TestResultsFetcherResponseHandling:
    """Tests for response status handling."""

    def test_check_response_404(self, mock_fetcher, mock_scraper):
        """Test 404 response raises appropriate error."""
        scraper, page, response = mock_scraper
        response.status = 404

        with pytest.raises(ResultsFetchError) as exc_info:
            mock_fetcher._check_response_status(response, "http://example.com")

        assert "404" in str(exc_info.value)

    def test_check_response_429(self, mock_fetcher, mock_scraper):
        """Test 429 rate limit response raises appropriate error."""
        scraper, page, response = mock_scraper
        response.status = 429

        with pytest.raises(ResultsFetchError) as exc_info:
            mock_fetcher._check_response_status(response, "http://example.com")

        assert "429" in str(exc_info.value)
        assert "Rate limited" in str(exc_info.value)

    def test_check_response_500(self, mock_fetcher, mock_scraper):
        """Test 500 error response raises appropriate error."""
        scraper, page, response = mock_scraper
        response.status = 500

        with pytest.raises(ResultsFetchError) as exc_info:
            mock_fetcher._check_response_status(response, "http://example.com")

        assert "500" in str(exc_info.value)

    def test_check_response_200_success(self, mock_fetcher, mock_scraper):
        """Test 200 response does not raise error."""
        scraper, page, response = mock_scraper
        response.status = 200

        # Should not raise
        mock_fetcher._check_response_status(response, "http://example.com")

    def test_check_response_none(self, mock_fetcher):
        """Test None response does not raise error."""
        # Should not raise
        mock_fetcher._check_response_status(None, "http://example.com")


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

    def test_extract_tables_all_found(self, mock_fetcher, mock_scraper):
        """Test extracting tables when all are found."""
        scraper, page, response = mock_scraper
        result_data = {"tables": {}}

        # Mock TableExtractor to return data for all tables
        with patch("shared.scraping.TableExtractor") as MockExtractor:
            MockExtractor.extract.return_value = {
                "table_name": "test",
                "data": [{"col": "value"}]
            }

            extracted, missing = mock_fetcher._extract_tables(page, result_data)

        assert extracted == len(mock_fetcher.config.result_tables)
        assert len(missing) == 0

    def test_extract_tables_some_missing(self, mock_fetcher, mock_scraper):
        """Test extracting tables when some are missing."""
        scraper, page, response = mock_scraper
        result_data = {"tables": {}}

        # Mock TableExtractor to return None for some tables
        call_count = [0]

        def mock_extract(page, table_id):
            call_count[0] += 1
            if call_count[0] % 2 == 0:
                return None
            return {"table_name": table_id, "data": []}

        with patch("shared.scraping.TableExtractor") as MockExtractor:
            MockExtractor.extract.side_effect = mock_extract

            extracted, missing = mock_fetcher._extract_tables(page, result_data)

        assert len(missing) > 0


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
