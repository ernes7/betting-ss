"""Odds service for loading and managing betting odds data.

This module provides centralized odds file operations including loading,
validation, and interactive selection.
"""

import json
import os
from typing import Optional, List, Tuple
from datetime import date
import inquirer
from rich.console import Console

from shared.config import get_data_path, get_file_path


console = Console()


class OddsService:
    """Service for managing betting odds data."""

    def __init__(self, sport_code: str):
        """Initialize the odds service.

        Args:
            sport_code: Sport identifier (e.g., 'nfl', 'nba')
        """
        self.sport_code = sport_code

    def load_odds_for_game(
        self,
        game_date: str,
        team_a_abbr: str,
        team_b_abbr: str,
        home_team_abbr: str
    ) -> Optional[dict]:
        """Load odds file for a game if it exists.

        Args:
            game_date: Game date in YYYY-MM-DD format
            team_a_abbr: First team abbreviation (lowercase)
            team_b_abbr: Second team abbreviation (lowercase)
            home_team_abbr: Home team abbreviation (lowercase)

        Returns:
            Odds data dictionary or None if file not found
        """
        # Build filename with home team first
        if home_team_abbr == team_a_abbr:
            filename_params = {
                "team_a_abbr": team_a_abbr,
                "team_b_abbr": team_b_abbr
            }
        else:
            filename_params = {
                "team_a_abbr": team_b_abbr,
                "team_b_abbr": team_a_abbr
            }

        # Build filepath
        odds_filepath = get_file_path(
            self.sport_code,
            "odds",
            "prediction_json",  # Uses same format as predictions
            game_date=game_date,
            **filename_params
        )

        # Check if odds file exists
        if not os.path.exists(odds_filepath):
            return None

        # Load odds data
        try:
            with open(odds_filepath, encoding="utf-8") as f:
                odds_data = json.load(f)
            return odds_data
        except Exception as e:
            console.print(f"[yellow]⚠ Warning: Could not load odds file: {str(e)}[/yellow]")
            return None

    def get_available_odds_dates(self) -> List[str]:
        """Get list of dates that have odds data available.

        Returns:
            Sorted list of dates in YYYY-MM-DD format
        """
        odds_dir = get_data_path(self.sport_code, "odds")

        if not os.path.exists(odds_dir):
            return []

        # Get all subdirectories (date folders)
        dates = [
            d for d in os.listdir(odds_dir)
            if os.path.isdir(os.path.join(odds_dir, d))
            and len(d.split("-")) == 3  # Basic date format check
        ]

        return sorted(dates, reverse=True)  # Most recent first

    def get_odds_files_for_date(self, odds_date: str) -> List[Tuple[str, str]]:
        """Get list of odds files available for a specific date.

        Args:
            odds_date: Date in YYYY-MM-DD format

        Returns:
            List of tuples (filepath, display_name)
        """
        odds_dir = get_data_path(self.sport_code, "odds", game_date=odds_date)

        if not os.path.exists(odds_dir):
            return []

        odds_files = []
        for filename in os.listdir(odds_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(odds_dir, filename)
                # Create display name from filename (e.g., "mia_buf.json" -> "MIA vs BUF")
                teams = filename.replace(".json", "").split("_")
                if len(teams) == 2:
                    display_name = f"{teams[0].upper()} vs {teams[1].upper()}"
                else:
                    display_name = filename
                odds_files.append((filepath, display_name))

        return sorted(odds_files, key=lambda x: x[1])

    def select_odds_file_interactive(self) -> Optional[Tuple[str, dict]]:
        """Interactive selection of odds file.

        Returns:
            Tuple of (filepath, odds_data) or None if cancelled
        """
        # Get available dates
        dates = self.get_available_odds_dates()

        if not dates:
            console.print("[yellow]No odds data found.[/yellow]")
            return None

        # Select date
        date_questions = [
            inquirer.List(
                "odds_date",
                message="Select odds date",
                choices=dates,
            ),
        ]
        date_answers = inquirer.prompt(date_questions)
        if not date_answers:
            return None

        odds_date = date_answers["odds_date"]

        # Get files for selected date
        odds_files = self.get_odds_files_for_date(odds_date)

        if not odds_files:
            console.print(f"[yellow]No odds files found for {odds_date}[/yellow]")
            return None

        # Select file
        file_questions = [
            inquirer.List(
                "odds_file",
                message="Select odds file",
                choices=[display_name for _, display_name in odds_files],
            ),
        ]
        file_answers = inquirer.prompt(file_questions)
        if not file_answers:
            return None

        # Find selected file
        selected_display = file_answers["odds_file"]
        selected_filepath = None
        for filepath, display_name in odds_files:
            if display_name == selected_display:
                selected_filepath = filepath
                break

        if not selected_filepath:
            return None

        # Load odds data
        try:
            with open(selected_filepath, encoding="utf-8") as f:
                odds_data = json.load(f)
            return (selected_filepath, odds_data)
        except Exception as e:
            console.print(f"[red]Error loading odds file: {str(e)}[/red]")
            return None

    def odds_exist_for_game(
        self,
        game_date: str,
        team_a_abbr: str,
        team_b_abbr: str,
        home_team_abbr: str
    ) -> bool:
        """Check if odds exist for a specific game.

        Args:
            game_date: Game date in YYYY-MM-DD format
            team_a_abbr: First team abbreviation (lowercase)
            team_b_abbr: Second team abbreviation (lowercase)
            home_team_abbr: Home team abbreviation (lowercase)

        Returns:
            True if odds file exists, False otherwise
        """
        odds_data = self.load_odds_for_game(
            game_date,
            team_a_abbr,
            team_b_abbr,
            home_team_abbr
        )
        return odds_data is not None

    def get_game_lines(self, odds_data: dict) -> Optional[dict]:
        """Extract game lines (moneyline, spread, total) from odds data.

        Args:
            odds_data: Odds data dictionary

        Returns:
            Game lines dictionary or None if not found
        """
        return odds_data.get("game_lines")

    def get_player_props(self, odds_data: dict) -> Optional[List[dict]]:
        """Extract player props from odds data.

        Args:
            odds_data: Odds data dictionary

        Returns:
            List of player prop dictionaries or None if not found
        """
        return odds_data.get("player_props")
