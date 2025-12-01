"""Pytest fixtures for ODDS service tests."""

import json
import pytest
from pathlib import Path
from datetime import datetime

from services.odds import (
    OddsService,
    OddsServiceConfig,
    OddsScraper,
    DraftKingsParser,
    NFL_INCLUDED_MARKETS,
    NFL_EXCLUDED_MARKETS,
)
from shared.scraping import ScraperConfig


@pytest.fixture
def test_scraper_config() -> ScraperConfig:
    """Fast scraper config for tests."""
    return ScraperConfig(
        interval_seconds=0.1,
        timeout_ms=5000,
        max_retries=1,
        retry_delay_seconds=0.1,
        headless=True,
        wait_time_ms=100,
    )


@pytest.fixture
def test_odds_config(test_scraper_config) -> OddsServiceConfig:
    """Test odds service configuration."""
    return OddsServiceConfig(
        scraper_config=test_scraper_config,
        included_markets=NFL_INCLUDED_MARKETS,
        excluded_markets=NFL_EXCLUDED_MARKETS,
    )


@pytest.fixture
def parser() -> DraftKingsParser:
    """DraftKings parser instance."""
    return DraftKingsParser()


@pytest.fixture
def temp_odds_dir(tmp_path) -> Path:
    """Create temporary odds data directory."""
    odds_dir = tmp_path / "nfl" / "data" / "odds"
    odds_dir.mkdir(parents=True)
    return odds_dir


@pytest.fixture
def odds_service(test_odds_config, tmp_path) -> OddsService:
    """OddsService with temp directory."""
    # Override data root to use temp directory
    config = OddsServiceConfig(
        scraper_config=test_odds_config.scraper_config,
        data_root=str(tmp_path / "{sport}" / "data" / "odds"),
        included_markets=test_odds_config.included_markets,
        excluded_markets=test_odds_config.excluded_markets,
    )
    return OddsService(sport="nfl", config=config)


@pytest.fixture
def sample_stadium_data() -> dict:
    """Sample DraftKings stadium event data."""
    return {
        "events": [{
            "id": "event_123",
            "startEventDate": "2024-12-01T18:00:00Z",
            "participants": [
                {
                    "type": "Team",
                    "name": "Dallas Cowboys",
                    "venueRole": "Home",
                    "metadata": {"shortName": "DAL"}
                },
                {
                    "type": "Team",
                    "name": "New York Giants",
                    "venueRole": "Away",
                    "metadata": {"shortName": "NYG"}
                }
            ]
        }],
        "markets": [
            {
                "id": "market_ml",
                "eventId": "event_123",
                "marketType": {"name": "Moneyline"},
                "name": "Moneyline"
            },
            {
                "id": "market_spread",
                "eventId": "event_123",
                "marketType": {"name": "Spread"},
                "name": "Spread"
            },
            {
                "id": "market_total",
                "eventId": "event_123",
                "marketType": {"name": "Total"},
                "name": "Total"
            },
            {
                "id": "market_passing",
                "eventId": "event_123",
                "marketType": {"name": "Passing Yards Milestones"},
                "name": "Dak Prescott Passing Yards"
            }
        ],
        "selections": [
            # Moneyline
            {
                "marketId": "market_ml",
                "displayOdds": {"american": "-150"},
                "participants": [{"venueRole": "Home"}]
            },
            {
                "marketId": "market_ml",
                "displayOdds": {"american": "+130"},
                "participants": [{"venueRole": "Away"}]
            },
            # Spread
            {
                "marketId": "market_spread",
                "points": -3.5,
                "displayOdds": {"american": "-110"},
                "participants": [{"venueRole": "Home"}]
            },
            {
                "marketId": "market_spread",
                "points": 3.5,
                "displayOdds": {"american": "-110"},
                "participants": [{"venueRole": "Away"}]
            },
            # Total
            {
                "marketId": "market_total",
                "label": "Over",
                "points": 47.5,
                "displayOdds": {"american": "-110"}
            },
            {
                "marketId": "market_total",
                "label": "Under",
                "points": -47.5,
                "displayOdds": {"american": "-110"}
            },
            # Passing yards milestones
            {
                "marketId": "market_passing",
                "milestoneValue": 250,
                "displayOdds": {"american": "-200"},
                "participants": [{"type": "Player", "name": "Dak Prescott", "venueRole": "HomePlayer"}]
            },
            {
                "marketId": "market_passing",
                "milestoneValue": 275,
                "displayOdds": {"american": "-110"},
                "participants": [{"type": "Player", "name": "Dak Prescott", "venueRole": "HomePlayer"}]
            },
            {
                "marketId": "market_passing",
                "milestoneValue": 300,
                "displayOdds": {"american": "+150"},
                "participants": [{"type": "Player", "name": "Dak Prescott", "venueRole": "HomePlayer"}]
            },
        ]
    }


@pytest.fixture
def sample_odds_data() -> dict:
    """Sample extracted odds data."""
    return {
        "sport": "nfl",
        "teams": {
            "home": {"name": "Dallas Cowboys", "abbr": "DAL"},
            "away": {"name": "New York Giants", "abbr": "NYG"}
        },
        "game_date": "2024-12-01T18:00:00Z",
        "fetched_at": "2024-12-01T12:00:00-05:00",
        "source": "draftkings",
        "game_lines": {
            "moneyline": {"home": -150, "away": 130},
            "spread": {"home": -3.5, "home_odds": -110, "away": 3.5, "away_odds": -110},
            "total": {"line": 47.5, "over": -110, "under": -110}
        },
        "player_props": [
            {
                "player": "Dak Prescott",
                "team": "HOME",
                "position": None,
                "props": [
                    {
                        "market": "passing_yards",
                        "milestones": [
                            {"line": 250, "odds": -200},
                            {"line": 275, "odds": -110},
                            {"line": 300, "odds": 150}
                        ]
                    }
                ]
            }
        ]
    }


@pytest.fixture
def saved_odds_file(temp_odds_dir, sample_odds_data) -> Path:
    """Create a saved odds file for testing."""
    date_dir = temp_odds_dir / "2024-12-01"
    date_dir.mkdir(parents=True, exist_ok=True)

    filepath = date_dir / "dal_nyg.json"
    filepath.write_text(json.dumps(sample_odds_data, indent=2))

    return filepath
