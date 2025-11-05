"""Metadata service for unified metadata management.

This module provides centralized metadata tracking for scraped data,
predictions, and analyses to prevent duplicate work and track processing status.
"""

import json
import os
from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional
from shared.config import ensure_parent_directory


class MetadataService:
    """Service for managing metadata files."""

    def __init__(self, metadata_file_path: str):
        """Initialize the metadata service.

        Args:
            metadata_file_path: Path to the metadata JSON file
        """
        self.metadata_file_path = metadata_file_path

    def load_metadata(self) -> Dict[str, Any]:
        """Load metadata file.

        Returns:
            Dictionary containing metadata, or empty dict if file doesn't exist
        """
        if os.path.exists(self.metadata_file_path):
            try:
                with open(self.metadata_file_path) as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load metadata file: {str(e)}")
                return {}
        return {}

    def save_metadata(self, metadata: Dict[str, Any]) -> None:
        """Save metadata file.

        Args:
            metadata: Dictionary to save as metadata
        """
        ensure_parent_directory(self.metadata_file_path)
        try:
            with open(self.metadata_file_path, "w") as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save metadata file: {str(e)}")

    def update_metadata(self, key: str, value: Any) -> None:
        """Update a specific metadata entry.

        Args:
            key: Metadata key to update
            value: New value for the key
        """
        metadata = self.load_metadata()
        metadata[key] = value
        self.save_metadata(metadata)

    def get_metadata_value(self, key: str, default: Any = None) -> Any:
        """Get a specific metadata value.

        Args:
            key: Metadata key to retrieve
            default: Default value if key doesn't exist

        Returns:
            Metadata value or default
        """
        metadata = self.load_metadata()
        return metadata.get(key, default)

    def check_if_processed_today(self, key: str) -> bool:
        """Check if an item was processed today.

        Args:
            key: Metadata key to check

        Returns:
            True if item was processed today, False otherwise
        """
        today = date.today().isoformat()
        return self.get_metadata_value(key) == today

    def mark_processed_today(self, key: str) -> None:
        """Mark an item as processed today.

        Args:
            key: Metadata key to mark
        """
        today = date.today().isoformat()
        self.update_metadata(key, today)

    def delete_metadata_key(self, key: str) -> None:
        """Delete a specific metadata key.

        Args:
            key: Metadata key to delete
        """
        metadata = self.load_metadata()
        if key in metadata:
            del metadata[key]
            self.save_metadata(metadata)

    def clear_metadata(self) -> None:
        """Clear all metadata (deletes the file)."""
        if os.path.exists(self.metadata_file_path):
            os.remove(self.metadata_file_path)

    def get_all_keys(self) -> list:
        """Get list of all metadata keys.

        Returns:
            List of metadata keys
        """
        metadata = self.load_metadata()
        return list(metadata.keys())


class PredictionsMetadataService(MetadataService):
    """Specialized service for predictions metadata with enhanced tracking."""

    def load_predictions_metadata(self) -> Dict[str, Any]:
        """Load predictions metadata with automatic migration and archival.

        Returns:
            Dictionary containing predictions metadata
        """
        metadata = self.load_metadata()

        # Migrate old format (string) to new format (dict)
        migrated = False
        for game_key, value in metadata.items():
            if isinstance(value, str):  # Old format: just date string
                metadata[game_key] = {
                    "last_predicted": value,
                    "results_fetched": False,
                    "odds_used": False,
                    "odds_source": None,
                    "game_date": None,
                    "teams": None,
                    "home_team": None,
                    "home_team_abbr": None
                }
                migrated = True
            elif isinstance(value, dict) and "odds_used" not in value:
                value["odds_used"] = False
                value["odds_source"] = None
                migrated = True

        # Save migrated version
        if migrated:
            self.save_metadata(metadata)

        # Auto-archive old completed entries (lazy archival)
        archived_count = self.archive_old_entries()
        if archived_count > 0:
            # Reload metadata after archival
            metadata = self.load_metadata()

        return metadata

    def was_game_predicted_today(
        self,
        game_date: str,
        team_a_abbr: str,
        team_b_abbr: str,
        home_team_abbr: str
    ) -> tuple[bool, str]:
        """Check if a game was already predicted today.

        Args:
            game_date: Game date in YYYY-MM-DD format
            team_a_abbr: First team abbreviation
            team_b_abbr: Second team abbreviation
            home_team_abbr: Home team abbreviation

        Returns:
            Tuple of (was_predicted, game_key)
        """
        metadata = self.load_predictions_metadata()
        today = date.today().isoformat()

        # Generate game key (home team first)
        if home_team_abbr == team_a_abbr:
            game_key = f"{game_date}_{team_a_abbr}_{team_b_abbr}"
        else:
            game_key = f"{game_date}_{team_b_abbr}_{team_a_abbr}"

        # Check if predicted today
        game_data = metadata.get(game_key)
        if isinstance(game_data, str):  # Old format
            was_predicted = game_data == today
        elif isinstance(game_data, dict):  # New format
            was_predicted = game_data.get("last_predicted") == today
        else:
            was_predicted = False

        return was_predicted, game_key

    def mark_game_predicted(
        self,
        game_key: str,
        game_date: str,
        teams: list[str],
        home_team: str,
        home_team_abbr: str,
        odds_used: bool = False,
        odds_source: Optional[str] = None
    ) -> None:
        """Mark a game as predicted with full metadata.

        Args:
            game_key: Unique game identifier
            game_date: Game date in YYYY-MM-DD format
            teams: List of team names
            home_team: Home team name
            home_team_abbr: Home team abbreviation
            odds_used: Whether odds were used in prediction
            odds_source: Source of odds if used (e.g., "draftkings")
        """
        metadata = self.load_predictions_metadata()
        today = date.today().isoformat()

        metadata[game_key] = {
            "last_predicted": today,
            "results_fetched": False,
            "odds_used": odds_used,
            "odds_source": odds_source,
            "game_date": game_date,
            "teams": teams,
            "home_team": home_team,
            "home_team_abbr": home_team_abbr
        }

        self.save_metadata(metadata)

    def mark_results_fetched(self, game_key: str) -> None:
        """Mark that results have been fetched for a game.

        Args:
            game_key: Unique game identifier
        """
        metadata = self.load_predictions_metadata()
        if game_key in metadata and isinstance(metadata[game_key], dict):
            metadata[game_key]["results_fetched"] = True
            self.save_metadata(metadata)

    def archive_old_entries(self, days_threshold: int = 7) -> int:
        """Archive old completed game entries to keep active metadata small.

        Archives games where:
        - results_fetched = true
        - analysis_generated = true
        - game_date is older than days_threshold

        Args:
            days_threshold: Number of days after which to archive (default: 7)

        Returns:
            Number of entries archived
        """
        # Get archive file path
        archive_path = self.metadata_file_path.replace(".metadata.json", ".metadata.archive.json")

        # Load current metadata
        metadata = self.load_metadata()
        if not metadata:
            return 0

        # Load existing archive
        archive = {}
        if os.path.exists(archive_path):
            try:
                with open(archive_path) as f:
                    archive = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load archive file: {str(e)}")

        # Calculate cutoff date
        cutoff_date = (datetime.now() - timedelta(days=days_threshold)).date()

        # Find entries to archive
        entries_to_archive = []
        for game_key, game_data in metadata.items():
            if not isinstance(game_data, dict):
                continue

            # Check if entry is ready to archive
            results_fetched = game_data.get("results_fetched", False)
            analysis_generated = game_data.get("analysis_generated", False)
            game_date_str = game_data.get("game_date")

            if not (results_fetched and analysis_generated and game_date_str):
                continue

            # Parse game date
            try:
                game_date = datetime.strptime(game_date_str, "%Y-%m-%d").date()
                if game_date < cutoff_date:
                    entries_to_archive.append(game_key)
            except (ValueError, TypeError):
                continue

        # Move entries to archive
        for game_key in entries_to_archive:
            archive[game_key] = metadata[game_key]
            del metadata[game_key]

        # Save both files if any entries were archived
        if entries_to_archive:
            self.save_metadata(metadata)
            ensure_parent_directory(archive_path)
            try:
                with open(archive_path, "w") as f:
                    json.dump(archive, f, indent=2)
            except Exception as e:
                print(f"Warning: Could not save archive file: {str(e)}")

        return len(entries_to_archive)
