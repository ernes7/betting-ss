"""Unit tests for OddsScraper."""

import pytest
from pathlib import Path

from services.odds import OddsScraper, OddsServiceConfig, get_default_config
from shared.errors import OddsFetchError, OddsParseError


class TestOddsScraperInit:
    """Tests for OddsScraper initialization."""

    def test_init_with_config(self, test_odds_config):
        """Test initialization with config."""
        scraper = OddsScraper(config=test_odds_config, sport="nfl")

        assert scraper.config == test_odds_config
        assert scraper.sport == "nfl"
        assert scraper.parser is not None

    def test_init_normalizes_sport(self, test_odds_config):
        """Test that sport is normalized to lowercase."""
        scraper = OddsScraper(config=test_odds_config, sport="NFL")
        assert scraper.sport == "nfl"


class TestOddsScraperExtract:
    """Tests for OddsScraper extraction methods."""

    def test_extract_odds_from_data(self, test_odds_config, sample_stadium_data):
        """Test extracting odds from stadium data."""
        scraper = OddsScraper(config=test_odds_config, sport="nfl")
        odds = scraper.extract_odds_from_data(sample_stadium_data)

        assert odds["sport"] == "nfl"
        assert odds["source"] == "draftkings"
        assert odds["teams"]["home"]["name"] == "Dallas Cowboys"
        assert odds["teams"]["away"]["name"] == "New York Giants"

    def test_extract_game_lines(self, test_odds_config, sample_stadium_data):
        """Test extracting game lines."""
        scraper = OddsScraper(config=test_odds_config, sport="nfl")
        odds = scraper.extract_odds_from_data(sample_stadium_data)

        game_lines = odds["game_lines"]
        assert "moneyline" in game_lines
        assert "spread" in game_lines
        assert "total" in game_lines

    def test_extract_player_props(self, test_odds_config, sample_stadium_data):
        """Test extracting player props."""
        scraper = OddsScraper(config=test_odds_config, sport="nfl")
        odds = scraper.extract_odds_from_data(sample_stadium_data)

        player_props = odds["player_props"]
        assert len(player_props) > 0

    def test_extract_from_empty_events(self, test_odds_config):
        """Test extracting from data with no events raises error."""
        scraper = OddsScraper(config=test_odds_config, sport="nfl")

        with pytest.raises(OddsParseError) as exc_info:
            scraper.extract_odds_from_data({"events": [], "markets": [], "selections": []})

        assert "No event data found" in str(exc_info.value)


class TestOddsScraperFile:
    """Tests for OddsScraper file operations."""

    def test_extract_from_file_not_found(self, test_odds_config):
        """Test extracting from non-existent file."""
        scraper = OddsScraper(config=test_odds_config, sport="nfl")

        with pytest.raises(OddsFetchError) as exc_info:
            scraper.extract_odds_from_file("/nonexistent/path.html")

        assert "not found" in str(exc_info.value).lower()


class TestOddsScraperMarketFiltering:
    """Tests for market filtering based on config."""

    def test_excludes_excluded_markets(self, test_odds_config, sample_stadium_data):
        """Test that excluded markets are not included."""
        # Add an excluded market
        sample_stadium_data["markets"].append({
            "id": "market_1q",
            "eventId": "event_123",
            "marketType": {"name": "1st Quarter Moneyline"},
            "name": "1st Quarter Moneyline"
        })

        scraper = OddsScraper(config=test_odds_config, sport="nfl")
        odds = scraper.extract_odds_from_data(sample_stadium_data)

        # Should not include 1st Quarter in player props
        for prop in odds["player_props"]:
            for p in prop.get("props", []):
                assert "1st_quarter" not in p.get("market", "")

    def test_only_includes_included_markets(self, sample_stadium_data):
        """Test that only included markets are processed."""
        # Create config with only moneyline included
        config = OddsServiceConfig(
            included_markets={"Moneyline"},
            excluded_markets=set(),
        )

        scraper = OddsScraper(config=config, sport="nfl")
        odds = scraper.extract_odds_from_data(sample_stadium_data)

        # Should still have game lines (moneyline, spread, total are handled separately)
        assert "moneyline" in odds["game_lines"]


class TestOddsScraperNBA:
    """Tests for NBA-specific scraping."""

    def test_nba_config(self):
        """Test that NBA config is loaded correctly."""
        config = get_default_config("nba")
        scraper = OddsScraper(config=config, sport="nba")

        assert scraper.sport == "nba"
        assert "Points Milestones" in scraper.config.included_markets
        assert "Rebounds Milestones" in scraper.config.included_markets
