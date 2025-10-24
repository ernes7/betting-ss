"""Common scraping logic for all sports."""

import os
from ratelimit import limits, sleep_and_retry
from tqdm import tqdm

from shared.base.sport_config import SportConfig
from shared.utils import MetadataManager, WebScraper, TableExtractor, FileManager


class Scraper:
    """Base scraper class with common logic for all sports.

    Uses template method pattern - common algorithm with sport-specific configuration.
    """

    def __init__(self, config: SportConfig):
        """Initialize scraper with sport-specific configuration.

        Args:
            config: Sport configuration object implementing SportConfig interface
        """
        self.config = config
        self.rankings_metadata_mgr = MetadataManager(config.data_rankings_dir)
        self.web_scraper = WebScraper()

    def _create_rate_limited_extract_rankings(self):
        """Create rate-limited version of extract_rankings based on sport config."""

        @sleep_and_retry
        @limits(calls=self.config.rate_limit_calls, period=self.config.rate_limit_period)
        def rate_limited_extract():
            return self._extract_rankings_impl()

        return rate_limited_extract

    def extract_rankings(self) -> dict:
        """Extract all ranking tables for the sport.

        Checks metadata to avoid scraping multiple times per day.

        Returns:
            Dictionary with extraction results (success/failure counts, skipped flag)
        """
        rate_limited_extract = self._create_rate_limited_extract_rankings()
        return rate_limited_extract()

    def _extract_rankings_impl(self) -> dict:
        """Implementation of rankings extraction."""
        # Check if rankings were already scraped today
        if self.rankings_metadata_mgr.was_scraped_today():
            print(f"\n{'=' * 70}")
            print("RANKINGS ALREADY EXTRACTED TODAY")
            print(f"{'=' * 70}")
            print("Using existing ranking data from today")
            print("  Rankings are refreshed once per day to respect rate limits")
            print(f"{'=' * 70}\n")
            return {"success": [], "failed": [], "skipped": True}

        print(f"Fetching fresh ranking data from {self.config.stats_url}...")
        results = {"success": [], "failed": [], "skipped": False}

        with self.web_scraper.launch() as page:
            # Navigate once to the stats page
            self.web_scraper.navigate_and_wait(page, self.config.stats_url)

            # Extract all tables from the same page with progress bar
            with tqdm(
                total=len(self.config.ranking_tables),
                desc="Extracting tables",
                unit="table",
            ) as pbar:
                for output_name, table_id in self.config.ranking_tables.items():
                    pbar.set_description(f"Extracting {output_name}")

                    table_data = TableExtractor.extract(page, table_id)

                    if table_data:
                        # Save to JSON
                        output_path = os.path.join(
                            self.config.data_rankings_dir, f"{output_name}.json"
                        )
                        FileManager.save_json(output_path, table_data)

                        results["success"].append(output_name)
                        pbar.write(f"  [OK] {output_name}: {len(table_data['data'])} rows")
                    else:
                        results["failed"].append(output_name)
                        pbar.write(f"  [WARN] Table '{table_id}' not found")

                    pbar.update(1)

        # Update metadata with today's date
        if results["success"]:
            self.rankings_metadata_mgr.mark_scraped_today()

        # Print summary
        print(f"\n{'=' * 70}")
        print("EXTRACTION COMPLETE")
        print(f"{'=' * 70}")
        print(
            f"Success: {len(results['success'])}/{len(self.config.ranking_tables)} tables"
        )
        if results["failed"]:
            print(f"Failed: {', '.join(results['failed'])}")
        print(f"{'=' * 70}\n")

        return results

    def _create_rate_limited_extract_profile(self):
        """Create rate-limited version of extract_team_profile based on sport config."""

        @sleep_and_retry
        @limits(calls=self.config.rate_limit_calls, period=self.config.rate_limit_period)
        def rate_limited_extract(team_name: str, team_abbr: str):
            return self._extract_team_profile_impl(team_name, team_abbr)

        return rate_limited_extract

    def extract_team_profile(self, team_name: str) -> dict:
        """Extract all profile tables for a single team.

        Args:
            team_name: Full team name (e.g., "Miami Dolphins")

        Returns:
            Dictionary mapping table names to extracted data
        """
        # Get team metadata
        team = self.config.get_team_by_name(team_name)
        if not team:
            print(f"Error: Team '{team_name}' not found in {self.config.sport_name} teams")
            return {}

        # Get sport-specific team abbreviation
        # Different sports use different keys (pfr_abbr for NFL, pbr_abbr for NBA, etc.)
        team_abbr = None
        for key in ["pfr_abbr", "pbr_abbr", "abbr"]:
            if key in team:
                team_abbr = team[key]
                break

        if not team_abbr:
            print(f"Error: Could not find abbreviation for team '{team_name}'")
            return {}

        rate_limited_extract = self._create_rate_limited_extract_profile()
        return rate_limited_extract(team_name, team_abbr)

    def _extract_team_profile_impl(self, team_name: str, team_abbr: str) -> dict:
        """Implementation of team profile extraction."""
        url = self.config.build_team_url(team_abbr)

        print(f"\nExtracting profile data for {team_name}...")
        print(f"URL: {url}")

        # Create team-specific directory
        team_folder = team_name.lower().replace(" ", "_")
        team_dir = os.path.join(self.config.data_profiles_dir, team_folder)
        os.makedirs(team_dir, exist_ok=True)

        extracted_data = {}

        with self.web_scraper.launch() as page:
            try:
                # Load page once
                response = self.web_scraper.navigate_and_wait(page, url)

                # Check for rate limiting or errors
                if response and response.status == 429:
                    print("  [ERROR] Rate limited (HTTP 429) - cannot extract data")
                    return {}
                elif response and response.status != 200:
                    print(f"  [ERROR] HTTP {response.status} - cannot extract data")
                    return {}

                # Extract each table
                for output_name, table_id in self.config.profile_tables.items():
                    # Handle dynamic table IDs (e.g., {pfr_abbr}_injury_report)
                    actual_table_id = table_id.format(
                        pfr_abbr=team_abbr, pbr_abbr=team_abbr
                    )

                    print(f"  Extracting {output_name} (#{actual_table_id})...")

                    table_data = TableExtractor.extract(page, actual_table_id)

                    if table_data:
                        # Save to file in team-specific folder
                        filepath = os.path.join(team_dir, f"{output_name}.json")
                        FileManager.save_json(filepath, table_data)

                        extracted_data[output_name] = table_data
                        print(f"    [OK] Saved to {filepath}")
                    else:
                        print(
                            f"    Warning: Table #{actual_table_id} not found, skipping..."
                        )

            except Exception as e:
                print(f"Error loading page for {team_name}: {str(e)}")
                return {}

        print(f"Completed profile extraction for {team_name}")
        return extracted_data
