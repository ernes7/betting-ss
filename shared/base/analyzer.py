"""Base class for prediction analysis across all sports."""

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from anthropic import Anthropic

from shared.base.sport_config import SportConfig


class BaseAnalyzer(ABC):
    """Base analyzer for evaluating prediction accuracy using Claude AI.

    Workflow:
    1. Load prediction JSON (parlays and bets)
    2. Load result JSON (final score, stats, tables)
    3. Send to Claude Haiku for intelligent analysis
    4. Parse AI response to determine hit/miss for each leg
    5. Calculate summary statistics
    6. Save analysis JSON to {sport}/analysis/{date}/{game}.json
    """

    def __init__(self, config: SportConfig, model: str = "claude-sonnet-4-5-20250929"):
        """Initialize analyzer with sport configuration.

        Args:
            config: Sport configuration object implementing SportConfig interface
            model: Claude model to use (default: claude-sonnet-4-5-20250929)
        """
        self.config = config
        self.model = model
        self.client = Anthropic()

    def generate_analysis(self, game_key: str, game_meta: dict) -> dict:
        """Generate analysis for a single game's predictions vs actual results.

        Args:
            game_key: Unique game identifier (e.g., "2025-10-23_team_a_team_b")
            game_meta: Game metadata from predictions metadata file

        Returns:
            Analysis data dictionary with parlay results and summary

        Raises:
            Exception: If prediction or result files not found, or API call fails
        """
        # 1. Load prediction and result data
        prediction_data = self._load_prediction(game_key, game_meta)
        result_data = self._load_result(game_key, game_meta)

        # 2. Validate result data has required tables
        self._validate_result_tables(result_data)

        # 3. Build sport-specific analysis prompt
        prompt = self._build_analysis_prompt(prediction_data, result_data)

        # 4. Call Claude API
        analysis_text, cost, tokens = self._call_claude_api(prompt)

        # 5. Parse Claude's JSON response
        analysis_data = self._parse_analysis_response(analysis_text)

        # 6. Add metadata
        analysis_data.update({
            "sport": self.config.sport_name,
            "game_date": game_meta.get("game_date"),
            "teams": {
                "away": result_data.get("teams", {}).get("away"),
                "home": result_data.get("teams", {}).get("home")
            },
            "final_score": result_data.get("final_score"),
            "prediction_file": self._get_prediction_path(game_key, game_meta),
            "result_file": self._get_result_path(game_key, game_meta),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "model": self.model,
            "api_cost": cost,
            "tokens": tokens
        })

        # 7. Save analysis to file
        self._save_analysis(game_key, game_meta, analysis_data)

        return analysis_data

    def _load_prediction(self, game_key: str, game_meta: dict) -> dict:
        """Load prediction JSON file.

        Args:
            game_key: Game identifier
            game_meta: Game metadata

        Returns:
            Prediction data dictionary
        """
        filepath = self._get_prediction_path(game_key, game_meta)

        if not os.path.exists(filepath):
            raise Exception(f"Prediction file not found: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_result(self, game_key: str, game_meta: dict) -> dict:
        """Load result JSON file.

        Args:
            game_key: Game identifier
            game_meta: Game metadata

        Returns:
            Result data dictionary
        """
        filepath = self._get_result_path(game_key, game_meta)

        if not os.path.exists(filepath):
            raise Exception(f"Result file not found: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _get_prediction_path(self, game_key: str, game_meta: dict) -> str:
        """Build path to prediction JSON file.

        Args:
            game_key: Game identifier
            game_meta: Game metadata

        Returns:
            Absolute path to prediction file
        """
        game_date = game_meta.get("game_date")
        parts = game_key.split("_")

        # Remove date prefix if present
        if parts[0] == game_date:
            filename = "_".join(parts[1:]) + ".json"
        else:
            filename = game_key + ".json"

        return os.path.join(self.config.predictions_dir, game_date, filename)

    def _get_result_path(self, game_key: str, game_meta: dict) -> str:
        """Build path to result JSON file.

        Args:
            game_key: Game identifier
            game_meta: Game metadata

        Returns:
            Absolute path to result file
        """
        game_date = game_meta.get("game_date")
        parts = game_key.split("_")

        # Remove date prefix if present
        if parts[0] == game_date:
            filename = "_".join(parts[1:]) + ".json"
        else:
            filename = game_key + ".json"

        return os.path.join(self.config.results_dir, game_date, filename)

    def _validate_result_tables(self, result_data: dict):
        """Validate that result data contains all required tables.

        Args:
            result_data: Result data dictionary with tables

        Raises:
            Exception: If any required table is missing from result data
        """
        required_tables = ["scoring", "passing", "rushing", "receiving", "defense"]
        missing_tables = []

        tables = result_data.get("tables", {})
        for table_name in required_tables:
            if table_name not in tables:
                missing_tables.append(table_name)

        if missing_tables:
            raise Exception(
                f"Result data is missing required tables: {', '.join(missing_tables)}. "
                f"Cannot perform analysis without complete data. "
                f"Available tables: {', '.join(tables.keys())}"
            )

    @abstractmethod
    def _build_analysis_prompt(self, prediction_data: dict, result_data: dict) -> str:
        """Build sport-specific analysis prompt for Claude.

        Args:
            prediction_data: Prediction JSON data
            result_data: Result JSON data

        Returns:
            Formatted prompt string
        """
        pass

    def _call_claude_api(self, prompt: str) -> tuple[str, float, dict]:
        """Call Claude API to analyze predictions.

        Args:
            prompt: Analysis prompt

        Returns:
            Tuple of (response_text, cost, tokens_dict)
        """
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Extract response text
        response_text = response.content[0].text

        # Calculate cost based on model
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

        # Claude Sonnet 4.5: $3/MTok input, $15/MTok output
        # Claude Haiku 4.5: $0.80/MTok input, $4/MTok output
        if "haiku" in self.model.lower():
            input_cost = (input_tokens / 1_000_000) * 0.80
            output_cost = (output_tokens / 1_000_000) * 4.0
        else:  # Sonnet
            input_cost = (input_tokens / 1_000_000) * 3.0
            output_cost = (output_tokens / 1_000_000) * 15.0

        total_cost = input_cost + output_cost

        tokens = {
            "input": input_tokens,
            "output": output_tokens,
            "total": input_tokens + output_tokens
        }

        return response_text, total_cost, tokens

    def _parse_analysis_response(self, response_text: str) -> dict:
        """Parse Claude's JSON response and validate parlay logic.

        Args:
            response_text: Raw response from Claude

        Returns:
            Parsed and validated analysis dictionary

        Raises:
            Exception: If response is not valid JSON
        """
        try:
            # Try to parse as JSON directly
            analysis_data = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_text = response_text[start:end].strip()
                analysis_data = json.loads(json_text)
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                json_text = response_text[start:end].strip()
                analysis_data = json.loads(json_text)
            else:
                raise Exception(f"Could not parse JSON from response: {response_text[:200]}")

        # Validate parlay logic: A parlay ONLY hits if ALL legs hit
        if "parlay_results" in analysis_data:
            for parlay in analysis_data["parlay_results"]:
                if "legs" in parlay:
                    # Validate each individual leg first
                    for leg in parlay["legs"]:
                        bet_text = leg.get("bet", "").lower()
                        actual_value_text = leg.get("actual_value", "").lower()
                        claimed_hit = leg.get("hit", False)

                        # Basic validation: check if "over" bets with numeric values make sense
                        if "over" in bet_text and actual_value_text:
                            # Try to extract the line and actual value
                            import re

                            # Extract line from bet (e.g., "Over 22.5" -> 22.5)
                            line_match = re.search(r'over\s+(\d+\.?\d*)', bet_text)

                            # Extract actual value (e.g., "18 completions" -> 18)
                            actual_match = re.search(r'(\d+\.?\d*)', actual_value_text)

                            if line_match and actual_match:
                                line = float(line_match.group(1))
                                actual = float(actual_match.group(1))

                                # For "over" bets: should hit if actual > line
                                should_hit = actual > line

                                if claimed_hit != should_hit:
                                    print(f"  [yellow]⚠ Correcting leg '{leg.get('bet')}': Claude said hit={claimed_hit}, but {actual} vs {line} line means hit={should_hit}[/yellow]")
                                    leg["hit"] = should_hit

                        # Similar check for "under" bets
                        elif "under" in bet_text and actual_value_text:
                            import re

                            line_match = re.search(r'under\s+(\d+\.?\d*)', bet_text)
                            actual_match = re.search(r'(\d+\.?\d*)', actual_value_text)

                            if line_match and actual_match:
                                line = float(line_match.group(1))
                                actual = float(actual_match.group(1))

                                # For "under" bets: should hit if actual < line
                                should_hit = actual < line

                                if claimed_hit != should_hit:
                                    print(f"  [yellow]⚠ Correcting leg '{leg.get('bet')}': Claude said hit={claimed_hit}, but {actual} vs {line} line means hit={should_hit}[/yellow]")
                                    leg["hit"] = should_hit

                    # Now count how many legs actually hit (after corrections)
                    actual_hits = sum(1 for leg in parlay["legs"] if leg.get("hit", False))
                    total_legs = len(parlay["legs"])

                    # A parlay hits ONLY if ALL legs hit
                    correct_hit_status = (actual_hits == total_legs)

                    # Fix incorrect parlay status
                    if parlay.get("hit") != correct_hit_status:
                        print(f"  [yellow]⚠ Correcting parlay '{parlay.get('parlay_name')}': Claude said hit={parlay.get('hit')}, but {actual_hits}/{total_legs} legs hit[/yellow]")
                        parlay["hit"] = correct_hit_status

                    # Update legs_hit count
                    parlay["legs_hit"] = actual_hits
                    parlay["legs_total"] = total_legs
                    parlay["hit_rate"] = (actual_hits / total_legs * 100) if total_legs > 0 else 0

            # Recalculate summary statistics
            if "summary" in analysis_data:
                total_parlays = len(analysis_data["parlay_results"])
                parlays_hit = sum(1 for p in analysis_data["parlay_results"] if p.get("hit", False))

                analysis_data["summary"]["parlays_hit"] = parlays_hit
                analysis_data["summary"]["parlays_total"] = total_parlays
                analysis_data["summary"]["parlay_hit_rate"] = (parlays_hit / total_parlays * 100) if total_parlays > 0 else 0

        return analysis_data

    def _save_analysis(self, game_key: str, game_meta: dict, analysis_data: dict):
        """Save analysis to JSON file.

        Args:
            game_key: Game identifier
            game_meta: Game metadata
            analysis_data: Analysis dictionary to save
        """
        # Use the overrideable _get_analysis_path() method
        # This allows subclasses (like NFLEVAnalyzer) to customize the save location
        filepath = self._get_analysis_path(game_key, game_meta)

        # Create directory structure
        date_dir = os.path.dirname(filepath)
        os.makedirs(date_dir, exist_ok=True)

        # Save to JSON file
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False)

        print(f"    [dim]Analysis saved to {filepath}[/dim]")
