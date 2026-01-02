"""Common prediction logic for all sports."""

import os
import anthropic
from dotenv import load_dotenv

from config import settings
from shared.base.sport_config import SportConfig
from shared.base.prompt_builder import PromptBuilder
from shared.utils import FileManager
from shared.utils.data_optimizer import optimize_rankings

# Load environment variables
load_dotenv()

# Load Claude API config
_claude_config = settings.get('api', {}).get('claude', {})


class Predictor:
    """Base predictor class with common logic for all sports."""

    def __init__(self, config: SportConfig, model: str | None = None):
        """Initialize predictor with sport-specific configuration.

        Args:
            config: Sport configuration object implementing SportConfig interface
            model: Claude model to use (default from config/settings.yaml)
        """
        self.config = config
        self.model = model or _claude_config.get('model', 'claude-sonnet-4-5')
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

    def generate_predictions(
        self,
        team_a: str,
        team_b: str,
        home_team: str,
        rankings: dict | None = None,
        profile_a: dict | None = None,
        profile_b: dict | None = None,
        odds: dict = None,
        game_date: str | None = None,
        odds_dir: str | None = None,
    ) -> dict:
        """Generate betting predictions.

        Args:
            team_a: First team name
            team_b: Second team name
            home_team: Which team is playing at home
            rankings: All ranking tables (will load if not provided)
            profile_a: Team A's detailed profile (will load if not provided)
            profile_b: Team B's detailed profile (will load if not provided)
            odds: Betting odds (REQUIRED for EV analysis)
            game_date: Game date (used for path-based prompt builders)
            odds_dir: Directory containing odds CSVs (for path-based builders)

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

        # Odds are required
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

        # Debug: Show input parameters
        print(f"\n{'='*60}")
        print("DEBUG: Predictor.generate_predictions() called")
        print(f"{'='*60}")
        print(f"Input parameters:")
        print(f"  team_a (raw):   '{team_a}'")
        print(f"  team_b (raw):   '{team_b}'")
        print(f"  home_team:      '{home_team}'")
        print(f"  game_date:      '{game_date}'")
        print(f"  odds_dir:       '{odds_dir}'")
        print(f"  sport:          '{self.config.sport_name}'")
        print(f"  has prompt_builder: {self.config.prompt_builder is not None}")

        # Resolve team names through sport-specific teams.py
        if self.config.sport_name == "bundesliga":
            from sports.futbol.bundesliga.teams import find_team_by_name
            team_a_info = find_team_by_name(team_a)
            team_b_info = find_team_by_name(team_b)
            home_team_info = find_team_by_name(home_team)
            print(f"\nTeam name resolution (via teams.py):")
            print(f"  team_a lookup: '{team_a}' -> {team_a_info['name'] if team_a_info else 'NOT FOUND'}")
            print(f"  team_b lookup: '{team_b}' -> {team_b_info['name'] if team_b_info else 'NOT FOUND'}")
            print(f"  home_team lookup: '{home_team}' -> {home_team_info['name'] if home_team_info else 'NOT FOUND'}")
            if team_a_info:
                team_a = team_a_info["name"]
            if team_b_info:
                team_b = team_b_info["name"]
            if home_team_info:
                home_team = home_team_info["name"]
            print(f"  Resolved: team_a='{team_a}', team_b='{team_b}', home_team='{home_team}'")
        elif self.config.sport_name == "nfl":
            from sports.nfl.teams import find_team_by_abbr
            team_a_info = find_team_by_abbr(team_a)
            team_b_info = find_team_by_abbr(team_b)
            home_team_info = find_team_by_abbr(home_team)
            if team_a_info:
                team_a = team_a_info["name"]
            if team_b_info:
                team_b = team_b_info["name"]
            if home_team_info:
                home_team = home_team_info["name"]

        # Build prediction prompt
        if self.config.prompt_builder:
            # Sport-specific prompt builder (e.g., Bundesliga) loads data directly from CSVs
            # Determine which team is home/away
            if home_team == team_b:
                home_team_name, away_team_name = team_b, team_a
            else:
                home_team_name, away_team_name = team_a, team_b

            print(f"\nHome/Away determination:")
            print(f"  home_team param (resolved): '{home_team}'")
            print(f"  Result: HOME='{home_team_name}', AWAY='{away_team_name}'")

            # Get profile folder from teams.py based on sport
            if self.config.sport_name == "bundesliga":
                from sports.futbol.bundesliga.teams import find_team_by_name
                home_info = find_team_by_name(home_team_name)
                away_info = find_team_by_name(away_team_name)
                home_folder = home_info.get("profile_folder") if home_info else home_team_name.lower().replace(" ", "_").replace(".", "")
                away_folder = away_info.get("profile_folder") if away_info else away_team_name.lower().replace(" ", "_").replace(".", "")
                print(f"\nProfile folder lookup (via teams.py):")
                print(f"  home_info found: {home_info is not None}")
                if home_info:
                    print(f"    -> profile_folder: '{home_info.get('profile_folder')}'")
                print(f"  away_info found: {away_info is not None}")
                if away_info:
                    print(f"    -> profile_folder: '{away_info.get('profile_folder')}'")
                print(f"  Final folders: home='{home_folder}', away='{away_folder}'")
            elif self.config.sport_name == "nfl":
                # NFL profiles use full team names (e.g., 'atlanta_falcons', 'tampa_bay_buccaneers')
                home_folder = home_team_name.lower().replace(" ", "_").replace(".", "")
                away_folder = away_team_name.lower().replace(" ", "_").replace(".", "")
            else:
                # Fallback: convert team names to folder format (lowercase, underscores)
                home_folder = home_team_name.lower().replace(" ", "_").replace(".", "")
                away_folder = away_team_name.lower().replace(" ", "_").replace(".", "")
                print(f"\nProfile folder (derived from name):")
                print(f"  home_folder: '{home_folder}'")
                print(f"  away_folder: '{away_folder}'")

            # Build profile paths (flat structure - no date folders)
            profiles_base = self.config.data_profiles_dir
            home_profile_path = os.path.join(profiles_base, home_folder)
            away_profile_path = os.path.join(profiles_base, away_folder)

            print(f"\nProfile paths (flat structure):")
            print(f"  profiles_base:      '{profiles_base}'")
            print(f"  home_profile_dir:   '{home_profile_path}'")
            print(f"    -> exists: {os.path.exists(home_profile_path)}")
            if os.path.exists(home_profile_path):
                print(f"    -> contents: {os.listdir(home_profile_path)}")
            print(f"  away_profile_dir:   '{away_profile_path}'")
            print(f"    -> exists: {os.path.exists(away_profile_path)}")
            if os.path.exists(away_profile_path):
                print(f"    -> contents: {os.listdir(away_profile_path)}")

            print(f"\nOdds:")
            print(f"  odds_dir: '{odds_dir}'")
            if odds_dir and os.path.exists(odds_dir):
                print(f"    -> exists: True")
                print(f"    -> contents: {os.listdir(odds_dir)}")
            else:
                print(f"    -> exists: False")

            print(f"\nRankings (flat structure):")
            print(f"  rankings_dir: '{self.config.data_rankings_dir}'")
            if os.path.exists(self.config.data_rankings_dir):
                ranking_files = [f for f in os.listdir(self.config.data_rankings_dir) if f.endswith('.csv')]
                print(f"    -> available files: {ranking_files[:5]}{'...' if len(ranking_files) > 5 else ''}")

            print(f"\n{'='*60}")
            print("Calling sport-specific prompt builder...")
            print(f"{'='*60}\n")

            # Build paths for sport-specific prompt builder
            prompt = self.config.prompt_builder(
                home_team=home_team_name,
                away_team=away_team_name,
                rankings_dir=self.config.data_rankings_dir,
                home_profile_dir=home_profile_path,
                away_profile_dir=away_profile_path,
                odds_dir=odds_dir or "",
            )
        else:
            # Default NFL-style prompt - requires ranking validation
            optimized_rankings = optimize_rankings(rankings, team_a, team_b)
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

            prompt = self.prompt_builder.build_prompt(
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

        # Call Claude API with temperature 0 for deterministic output
        client = anthropic.Anthropic(api_key=api_key)
        max_tokens = _claude_config.get('max_tokens', 16000)
        temperature = _claude_config.get('temperature', 0.0)

        print(f"\n{'='*60}")
        print("DEBUG: Claude API Call")
        print(f"{'='*60}")
        print(f"  Model:       {self.model}")
        print(f"  Max tokens:  {max_tokens}")
        print(f"  Temperature: {temperature}")
        print(f"  Prompt size: {len(prompt)} chars")
        print(f"  Calling API...")

        try:
            message = client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )

            # Extract text from response
            prediction_text = message.content[0].text if message.content else ""

            # Extract token usage and calculate cost
            input_tokens = message.usage.input_tokens
            output_tokens = message.usage.output_tokens
            total_tokens = input_tokens + output_tokens

            # Calculate cost using config values
            input_cost_per_mtok = _claude_config.get('input_cost_per_mtok', 3.0)
            output_cost_per_mtok = _claude_config.get('output_cost_per_mtok', 15.0)
            input_cost = (input_tokens / 1_000_000) * input_cost_per_mtok
            output_cost = (output_tokens / 1_000_000) * output_cost_per_mtok
            total_cost = input_cost + output_cost

            print(f"\n{'='*60}")
            print("DEBUG: Claude API Response")
            print(f"{'='*60}")
            print(f"  Input tokens:  {input_tokens:,}")
            print(f"  Output tokens: {output_tokens:,}")
            print(f"  Total tokens:  {total_tokens:,}")
            print(f"  Input cost:    ${input_cost:.4f}")
            print(f"  Output cost:   ${output_cost:.4f}")
            print(f"  Total cost:    ${total_cost:.4f}")
            print(f"  Response size: {len(prediction_text)} chars")
            print(f"{'='*60}\n")

            return {
                "success": True,
                "prediction": prediction_text,
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
