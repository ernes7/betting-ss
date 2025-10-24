"""Metadata tracking for scraping operations."""

import json
import os
from datetime import date
from pathlib import Path


class MetadataManager:
    """Manages metadata files to track when data was last scraped."""

    def __init__(self, data_dir: str):
        """Initialize metadata manager for a specific data directory.

        Args:
            data_dir: Directory where data is stored (e.g., "nfl/data/rankings")
        """
        self.data_dir = data_dir
        self.metadata_file = os.path.join(data_dir, ".metadata.json")

    def load_metadata(self) -> dict:
        """Load metadata file tracking when data was last scraped."""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file) as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load metadata file: {str(e)}")
                return {}
        return {}

    def save_metadata(self, metadata: dict):
        """Save metadata file."""
        os.makedirs(self.data_dir, exist_ok=True)
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save metadata file: {str(e)}")

    def was_scraped_today(self) -> bool:
        """Check if data was scraped today."""
        metadata = self.load_metadata()
        today = date.today().isoformat()
        return metadata.get("last_scraped") == today

    def mark_scraped_today(self):
        """Mark data as scraped today."""
        metadata = {"last_scraped": date.today().isoformat()}
        self.save_metadata(metadata)
