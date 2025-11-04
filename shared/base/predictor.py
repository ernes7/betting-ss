"""Common prediction logic for all sports."""

import os
import anthropic
from dotenv import load_dotenv

from shared.base.sport_config import SportConfig
from shared.base.prompt_builder import PromptBuilder
from shared.utils import FileManager
from shared.utils.data_optimizer import optimize_rankings

# Load environment variables
load_dotenv()


class Predictor:
    """Base predictor class with common logic for all sports."""

    def __init__(self, config: SportConfig, model: str = "claude-sonnet-4-5-20250929"):
        """Initialize predictor with sport-specific configuration.

        Args:
            config: Sport configuration object implementing SportConfig interface
            model: Claude model to use (default: claude-sonnet-4-5-20250929)
        """
        self.config = config
        self.model = model
        self.prompt_builder = PromptBuilder()

    def load_ranking_tables(self) -> dict[str, dict]:
        """Load all ranking tables for this sport.

        Returns:
            Dictionary mapping table names to their data
        """
        return FileManager.load_all_json_in_dir(self.config.data_rankings_dir)

    def load_team_profile(self, team_name: str) -> dict | None:
        """Load a team's profile data.

        Args:
            team_name: Full team name

        Returns:
            Dictionary with all profile tables or None if not found
        """
        # Normalize team name to folder name (lowercase, underscores)
        team_folder = team_name.lower().replace(" ", "_")
        team_dir = os.path.join(self.config.data_profiles_dir, team_folder)

        if not os.path.exists(team_dir):
            return None

        return FileManager.load_all_json_in_dir(team_dir)

    def get_team_from_rankings(self, rankings: dict, team_name: str) -> dict | None:
        """Extract a specific team's data from ranking tables.

        Args:
            rankings: All ranking tables
            team_name: Team name to search for

        Returns:
            Dictionary with team data from all ranking tables
        """
        team_data = {}

        for table_name, table_content in rankings.items():
            if not table_content or "data" not in table_content:
                continue

            # Find team in this table
            for row in table_content["data"]:
                if row.get("team", "").lower() == team_name.lower():
                    team_data[table_name] = row
                    break

        return team_data if team_data else None

    def generate_parlays(
        self,
        team_a: str,
        team_b: str,
        home_team: str,
        rankings: dict | None = None,
        profile_a: dict | None = None,
        profile_b: dict | None = None,
        odds: dict | None = None,
    ) -> dict:
        """Generate betting parlays using Claude API.

        Args:
            team_a: First team name
            team_b: Second team name
            home_team: Which team is playing at home
            rankings: All ranking tables (will load if not provided)
            profile_a: Team A's detailed profile (will load if not provided)
            profile_b: Team B's detailed profile (will load if not provided)
            odds: Betting odds data from sportsbook (optional)

        Returns:
            Dictionary with prediction text, cost, model, and token usage:
            {
                "prediction": str,
                "cost": float,
                "model": str,
                "tokens": {"input": int, "output": int, "total": int}
            }
        """
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return {
                "prediction": "Error: ANTHROPIC_API_KEY not found in .env file",
                "cost": 0.0,
                "model": "unknown",
                "tokens": {"input": 0, "output": 0, "total": 0}
            }

        # Load rankings if not provided
        if rankings is None:
            rankings = self.load_ranking_tables()

        # Optimize rankings to reduce token usage
        optimized_rankings = optimize_rankings(rankings, team_a, team_b)

        # Extract team data from rankings
        team_a_stats = self.get_team_from_rankings(optimized_rankings, team_a)
        team_b_stats = self.get_team_from_rankings(optimized_rankings, team_b)

        if not team_a_stats or not team_b_stats:
            return {
                "prediction": f"Error: Could not find stats for {team_a} or {team_b} in rankings",
                "cost": 0.0,
                "model": "unknown",
                "tokens": {"input": 0, "output": 0, "total": 0}
            }

        # Load profiles if not provided
        if profile_a is None:
            profile_a = self.load_team_profile(team_a)
        if profile_b is None:
            profile_b = self.load_team_profile(team_b)

        # Build the prompt using sport-specific components
        prompt = self.prompt_builder.build_prompt(
            sport_components=self.config.prompt_components,
            team_a=team_a,
            team_b=team_b,
            home_team=home_team,
            team_a_stats=team_a_stats,
            team_b_stats=team_b_stats,
            profile_a=profile_a,
            profile_b=profile_b,
            odds=odds,
        )

        # Call Claude API
        client = anthropic.Anthropic(api_key=api_key)

        try:
            message = client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract token usage and calculate cost
            input_tokens = message.usage.input_tokens
            output_tokens = message.usage.output_tokens
            total_tokens = input_tokens + output_tokens

            # Calculate cost based on model
            # Claude Sonnet 4.5: $3/MTok input, $15/MTok output
            # Claude Haiku 4.5: $0.80/MTok input, $4/MTok output
            if "haiku" in self.model.lower():
                input_cost = (input_tokens / 1_000_000) * 0.80
                output_cost = (output_tokens / 1_000_000) * 4.0
            else:  # Sonnet
                input_cost = (input_tokens / 1_000_000) * 3.0
                output_cost = (output_tokens / 1_000_000) * 15.0

            total_cost = input_cost + output_cost

            return {
                "success": True,
                "prediction": message.content[0].text,
                "cost": total_cost,
                "model": self.model,
                "tokens": {
                    "input": input_tokens,
                    "output": output_tokens,
                    "total": total_tokens
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "prediction": "",
                "cost": 0.0,
                "model": self.model,
                "tokens": {"input": 0, "output": 0, "total": 0}
            }

    def generate_ev_singles(
        self,
        team_a: str,
        team_b: str,
        home_team: str,
        rankings: dict | None = None,
        profile_a: dict | None = None,
        profile_b: dict | None = None,
        odds: dict = None
    ) -> dict:
        """Generate 5 individual EV+ bets with Kelly Criterion.

        Args:
            team_a: First team name
            team_b: Second team name
            home_team: Which team is playing at home
            rankings: All ranking tables (will load if not provided)
            profile_a: Team A's detailed profile (will load if not provided)
            profile_b: Team B's detailed profile (will load if not provided)
            odds: Betting odds (REQUIRED for EV analysis)

        Returns:
            Dictionary with prediction text, cost, model, and token usage:
            {
                "success": bool,
                "prediction": str,
                "cost": float,
                "model": str,
                "tokens": {"input": int, "output": int, "total": int},
                "error": str  # Only if success=False
            }
        """
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "ANTHROPIC_API_KEY not found in .env file",
                "prediction": "",
                "cost": 0.0,
                "model": self.model,
                "tokens": {"input": 0, "output": 0, "total": 0}
            }

        # Odds are required for EV analysis
        if odds is None:
            return {
                "success": False,
                "error": "Odds data is required for EV+ analysis",
                "prediction": "",
                "cost": 0.0,
                "model": self.model,
                "tokens": {"input": 0, "output": 0, "total": 0}
            }

        # Load rankings if not provided
        if rankings is None:
            rankings = self.load_ranking_tables()

        # Optimize rankings to reduce token usage
        optimized_rankings = optimize_rankings(rankings, team_a, team_b)

        # Extract team data from rankings
        team_a_stats = self.get_team_from_rankings(optimized_rankings, team_a)
        team_b_stats = self.get_team_from_rankings(optimized_rankings, team_b)

        if not team_a_stats or not team_b_stats:
            return {
                "success": False,
                "error": f"Could not find stats for {team_a} or {team_b} in rankings",
                "prediction": "",
                "cost": 0.0,
                "model": self.model,
                "tokens": {"input": 0, "output": 0, "total": 0}
            }

        # Load profiles if not provided
        if profile_a is None:
            profile_a = self.load_team_profile(team_a)
        if profile_b is None:
            profile_b = self.load_team_profile(team_b)

        # Build EV-specific prompt
        prompt = self.prompt_builder.build_ev_singles_prompt(
            sport_components=self.config.prompt_components,
            team_a=team_a,
            team_b=team_b,
            home_team=home_team,
            team_a_stats=team_a_stats,
            team_b_stats=team_b_stats,
            profile_a=profile_a,
            profile_b=profile_b,
            odds=odds
        )

        # Call Claude API (same as generate_parlays)
        client = anthropic.Anthropic(api_key=api_key)

        try:
            message = client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )

            # Extract token usage and calculate cost
            input_tokens = message.usage.input_tokens
            output_tokens = message.usage.output_tokens
            total_tokens = input_tokens + output_tokens

            # Calculate cost (Sonnet 4.5: $3/MTok input, $15/MTok output)
            input_cost = (input_tokens / 1_000_000) * 3.0
            output_cost = (output_tokens / 1_000_000) * 15.0
            total_cost = input_cost + output_cost

            return {
                "success": True,
                "prediction": message.content[0].text,
                "cost": total_cost,
                "model": self.model,
                "tokens": {
                    "input": input_tokens,
                    "output": output_tokens,
                    "total": total_tokens
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "prediction": "",
                "cost": 0.0,
                "model": self.model,
                "tokens": {"input": 0, "output": 0, "total": 0}
            }
