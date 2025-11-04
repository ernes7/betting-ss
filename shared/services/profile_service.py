"""Profile service for loading team profiles with automatic scraping fallback.

This module provides centralized team profile management, including loading
profiles from disk and triggering scraping when data is missing or stale.
"""

import json
import os
from datetime import date
from typing import Dict, Optional, List
from rich.console import Console

from shared.services.metadata_service import MetadataService
from shared.config import get_data_path


console = Console()


class ProfileService:
    """Service for managing team profile data."""

    def __init__(
        self,
        sport_code: str,
        scraper,
        metadata_service: MetadataService
    ):
        """Initialize the profile service.

        Args:
            sport_code: Sport identifier (e.g., 'nfl', 'nba')
            scraper: Scraper instance for fetching fresh profiles
            metadata_service: MetadataService instance for tracking scrapes
        """
        self.sport_code = sport_code
        self.scraper = scraper
        self.metadata_service = metadata_service

    def load_team_profiles(
        self,
        *team_names: str,
        force_refresh: bool = False
    ) -> Dict[str, Optional[Dict]]:
        """Load profiles for multiple teams.

        Always fetches fresh data unless the team was already scraped today,
        unless force_refresh is True.

        Args:
            *team_names: Variable number of team names to load
            force_refresh: If True, force scraping even if scraped today

        Returns:
            Dictionary mapping team names to their profile data (or None if failed)
        """
        metadata = self.metadata_service.load_metadata()
        profiles = {}

        for team_name in team_names:
            # Normalize team name to folder name
            team_folder = team_name.lower().replace(" ", "_")
            profile_dir = os.path.join(
                get_data_path(self.sport_code, "profiles"),
                team_folder
            )

            # Check if we need to scrape fresh data
            needs_scraping = force_refresh or not self._was_scraped_today(team_folder, metadata)

            if not needs_scraping:
                console.print(
                    f"  [dim]Profile for {team_name} already scraped today, "
                    f"using existing data...[/dim]"
                )
            else:
                self._scrape_team_profile(team_name, team_folder, metadata)

            # Load profile from disk
            profiles[team_name] = self._load_profile_from_disk(team_name, profile_dir)

        return profiles

    def load_single_profile(
        self,
        team_name: str,
        force_refresh: bool = False
    ) -> Optional[Dict]:
        """Load profile for a single team.

        Args:
            team_name: Team name to load
            force_refresh: If True, force scraping even if scraped today

        Returns:
            Profile data dictionary or None if failed
        """
        profiles = self.load_team_profiles(team_name, force_refresh=force_refresh)
        return profiles.get(team_name)

    def _was_scraped_today(self, team_folder: str, metadata: Dict) -> bool:
        """Check if a team was scraped today.

        Args:
            team_folder: Normalized team folder name
            metadata: Metadata dictionary

        Returns:
            True if scraped today, False otherwise
        """
        today = date.today().isoformat()
        return metadata.get(team_folder) == today

    def _scrape_team_profile(
        self,
        team_name: str,
        team_folder: str,
        metadata: Dict
    ) -> None:
        """Scrape fresh profile data for a team.

        Args:
            team_name: Full team name
            team_folder: Normalized team folder name
            metadata: Metadata dictionary
        """
        console.print(f"  [cyan]Fetching fresh profile data for {team_name}...[/cyan]")

        try:
            # Use scraper to extract profile
            self.scraper.extract_team_profile(team_name)
            console.print(f"  [green]✓ Successfully extracted profile for {team_name}[/green]")

            # Update metadata with today's date
            metadata[team_folder] = date.today().isoformat()
            self.metadata_service.save_metadata(metadata)
        except Exception as e:
            console.print(f"  [red]✗ Failed to extract profile for {team_name}: {str(e)}[/red]")

    def _load_profile_from_disk(
        self,
        team_name: str,
        profile_dir: str
    ) -> Optional[Dict]:
        """Load profile data from disk.

        Args:
            team_name: Team name for display
            profile_dir: Directory containing profile JSON files

        Returns:
            Profile data dictionary or None if failed
        """
        # Check if profile directory exists
        if not os.path.exists(profile_dir):
            console.print(f"  [red]✗ Profile directory not found for {team_name}[/red]")
            return None

        # Load all JSON files in the team's folder
        team_profile = {}
        for json_file in os.listdir(profile_dir):
            if json_file.endswith(".json"):
                table_name = json_file.replace(".json", "")
                filepath = os.path.join(profile_dir, json_file)
                try:
                    with open(filepath, encoding="utf-8") as f:
                        team_profile[table_name] = json.load(f)
                except Exception as e:
                    console.print(
                        f"  [yellow]⚠ Warning: Could not load {json_file}: {str(e)}[/yellow]"
                    )
                    continue

        if team_profile:
            console.print(f"  [green]✓ Loaded {len(team_profile)} tables for {team_name}[/green]")
            return team_profile
        else:
            return None

    def profile_exists(self, team_name: str) -> bool:
        """Check if a profile exists for a team.

        Args:
            team_name: Team name to check

        Returns:
            True if profile directory exists and contains JSON files
        """
        team_folder = team_name.lower().replace(" ", "_")
        profile_dir = os.path.join(
            get_data_path(self.sport_code, "profiles"),
            team_folder
        )

        if not os.path.exists(profile_dir):
            return False

        # Check if directory contains any JSON files
        json_files = [f for f in os.listdir(profile_dir) if f.endswith(".json")]
        return len(json_files) > 0

    def get_profile_tables(self, team_name: str) -> List[str]:
        """Get list of available tables for a team's profile.

        Args:
            team_name: Team name

        Returns:
            List of table names (without .json extension)
        """
        team_folder = team_name.lower().replace(" ", "_")
        profile_dir = os.path.join(
            get_data_path(self.sport_code, "profiles"),
            team_folder
        )

        if not os.path.exists(profile_dir):
            return []

        return [
            f.replace(".json", "")
            for f in os.listdir(profile_dir)
            if f.endswith(".json")
        ]
