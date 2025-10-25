"""Base class for fetching and storing game results."""

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from shared.base.sport_config import SportConfig


class ResultsFetcher(ABC):
    """Base class for fetching game results across all sports.

    Handles the common workflow:
    1. Load predictions metadata
    2. Filter games by date where results not yet fetched
    3. Fetch results from sports reference sites
    4. Save results to JSON files
    5. Update metadata to mark results as fetched
    """

    def __init__(self, config: SportConfig):
        """Initialize results fetcher with sport-specific configuration.

        Args:
            config: Sport configuration object implementing SportConfig interface
        """
        self.config = config

    @abstractmethod
    def extract_game_result(self, boxscore_url: str) -> dict[str, Any]:
        """Extract final score and player stats from boxscore page.

        Args:
            boxscore_url: URL to the game's boxscore page

        Returns:
            Dictionary with game results following the schema:
            {
                "game_date": str,
                "teams": {"away": str, "home": str},
                "final_score": {"away": int, "home": int},
                "winner": str,
                "boxscore_url": str,
                "fetched_at": str,
                "player_stats": {...}
            }

        Note:
            This is sport-specific and must be implemented by each sport.
            Implementation should use web scraping to extract data from boxscore page.
        """
        pass

    def fetch_results_for_date(self, target_date: str) -> dict[str, Any]:
        """Fetch results for all games on a specific date.

        Algorithm:
        1. Load predictions metadata
        2. Filter games matching target_date where results_fetched = false
        3. For each game:
           a. Build boxscore URL using config.build_boxscore_url()
           b. Call extract_game_result()
           c. Save result to {results_dir}/{date}/{game}.json
           d. Update predictions metadata: results_fetched = true
        4. Return summary statistics

        Args:
            target_date: Date in YYYY-MM-DD format

        Returns:
            Dictionary with summary:
            {
                "fetched_count": int,
                "failed_count": int,
                "skipped_count": int,
                "errors": [...]
            }

        Note:
            This is a stub implementation. Will be implemented in future phase.
        """
        # TODO: Implement in next phase
        return {
            "fetched_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "errors": []
        }

    def _save_result_to_json(self, game_date: str, game_key: str, result_data: dict[str, Any]):
        """Save game result to JSON file.

        Args:
            game_date: Game date in YYYY-MM-DD format
            game_key: Unique game identifier (e.g., "2025-10-24_tor_mil")
            result_data: Game result dictionary from extract_game_result()
        """
        # Create results directory structure
        date_dir = os.path.join(self.config.results_dir, game_date)
        os.makedirs(date_dir, exist_ok=True)

        # Extract filename from game_key (e.g., "2025-10-24_tor_mil" -> "tor_mil.json")
        filename = "_".join(game_key.split("_")[1:]) + ".json"
        filepath = os.path.join(date_dir, filename)

        # Save to JSON file
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)

    def _load_predictions_metadata(self) -> dict[str, Any]:
        """Load predictions metadata file.

        Returns:
            Predictions metadata dictionary
        """
        metadata_file = os.path.join(self.config.predictions_dir, ".metadata.json")

        if os.path.exists(metadata_file):
            try:
                with open(metadata_file) as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load predictions metadata: {str(e)}")
                return {}
        return {}

    def _save_predictions_metadata(self, metadata: dict[str, Any]):
        """Save predictions metadata file.

        Args:
            metadata: Updated metadata dictionary
        """
        metadata_file = os.path.join(self.config.predictions_dir, ".metadata.json")
        os.makedirs(os.path.dirname(metadata_file), exist_ok=True)

        try:
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save predictions metadata: {str(e)}")
