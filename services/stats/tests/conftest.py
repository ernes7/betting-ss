"""Pytest fixtures for STATS service tests."""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from services.stats import (
    StatsService,
    StatsServiceConfig,
    StatsFetcher,
)
from shared.scraping import ScraperConfig


@pytest.fixture
def test_scraper_config() -> ScraperConfig:
    """Fast scraper config for tests."""
    return ScraperConfig(
        delay_seconds=0.1,
        timeout=5,
        max_retries=1,
    )


@pytest.fixture
def test_stats_config(test_scraper_config) -> StatsServiceConfig:
    """Test stats service configuration."""
    return StatsServiceConfig(
        scraper_config=test_scraper_config,
        rankings_tables={"team_offense": "team_stats"},
        defensive_tables={"team_defense": "team_stats"},
        profile_tables={"passing": "passing"},
    )


@pytest.fixture
def temp_stats_dir(tmp_path) -> Path:
    """Create temporary stats data directory."""
    rankings_dir = tmp_path / "nfl" / "data" / "rankings"
    rankings_dir.mkdir(parents=True)
    profiles_dir = tmp_path / "nfl" / "data" / "profiles"
    profiles_dir.mkdir(parents=True)
    return tmp_path / "nfl" / "data"


@pytest.fixture
def mock_scraper():
    """Create a mock scraper."""
    scraper = MagicMock()

    # Mock fetch_html
    scraper.fetch_html.return_value = """
    <html>
    <table id="team_stats">
        <tr><th>Rk</th><th>Tm</th><th>G</th></tr>
        <tr><td>1</td><td>Cowboys</td><td>10</td></tr>
        <tr><td>2</td><td>Giants</td><td>10</td></tr>
    </table>
    </html>
    """

    import pandas as pd
    # Mock extract_tables
    scraper.extract_tables.return_value = [
        pd.DataFrame({
            "Rk": [1, 2],
            "Tm": ["Cowboys", "Giants"],
            "G": [10, 10]
        })
    ]

    return scraper


@pytest.fixture
def stats_fetcher(test_stats_config, mock_scraper) -> StatsFetcher:
    """Create a StatsFetcher with mock scraper."""
    return StatsFetcher(
        sport="nfl",
        config=test_stats_config,
        scraper=mock_scraper,
    )


@pytest.fixture
def stats_service(test_stats_config, tmp_path) -> StatsService:
    """StatsService with temp directory."""
    config = StatsServiceConfig(
        scraper_config=test_stats_config.scraper_config,
        data_root=str(tmp_path / "{sport}" / "data"),
        rankings_tables=test_stats_config.rankings_tables,
        defensive_tables=test_stats_config.defensive_tables,
        profile_tables=test_stats_config.profile_tables,
    )
    return StatsService(sport="nfl", config=config)


@pytest.fixture
def sample_rankings_data() -> dict:
    """Sample rankings data with tables as list of records (CSV-compatible)."""
    return {
        "tables": {
            "team_offense": [
                {"Rk": 1, "Tm": "Cowboys", "G": 10, "PF": 300, "PA": 200},
                {"Rk": 2, "Tm": "Giants", "G": 10, "PF": 250, "PA": 230},
            ]
        }
    }


@pytest.fixture
def sample_profile_data() -> dict:
    """Sample team profile data with tables as list of records (CSV-compatible)."""
    return {
        "tables": {
            "passing": [
                {"Player": "Dak Prescott", "Cmp": 200, "Att": 300, "Yds": 2500, "TD": 20},
            ],
            "rushing_receiving": [
                {"Player": "Tony Pollard", "Pos": "RB", "Att": 150, "Yds": 800, "TD": 5},
                {"Player": "CeeDee Lamb", "Pos": "WR", "Att": 0, "Yds": 0, "TD": 0},
            ]
        }
    }


@pytest.fixture
def saved_rankings_dir(temp_stats_dir, sample_rankings_data) -> Path:
    """Create saved rankings CSV files for testing."""
    import pandas as pd

    rankings_dir = temp_stats_dir / "rankings" / "2024-12-01"
    rankings_dir.mkdir(parents=True, exist_ok=True)

    # Save each table as CSV
    for table_name, table_data in sample_rankings_data["tables"].items():
        df = pd.DataFrame(table_data)
        df.to_csv(rankings_dir / f"{table_name}.csv", index=False)

    return rankings_dir


@pytest.fixture
def saved_profile_dir(temp_stats_dir, sample_profile_data) -> Path:
    """Create saved profile CSV files for testing."""
    import pandas as pd

    profile_dir = temp_stats_dir / "profiles" / "2024-12-01" / "dal"
    profile_dir.mkdir(parents=True, exist_ok=True)

    # Save each table as CSV
    for table_name, table_data in sample_profile_data["tables"].items():
        df = pd.DataFrame(table_data)
        df.to_csv(profile_dir / f"{table_name}.csv", index=False)

    return profile_dir
