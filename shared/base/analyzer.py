"""Base class for prediction analysis across all sports - Refactored with repositories."""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional

from anthropic import Anthropic

from shared.base.sport_config import SportConfig
from shared.repositories import PredictionRepository, ResultsRepository, AnalysisRepository, EVResultsRepository
from shared.config import calculate_api_cost
from shared.utils.timezone_utils import get_eastern_now


class BaseAnalyzer(ABC):
    """Base analyzer for evaluating prediction accuracy using Claude AI.

    Workflow:
    1. Load prediction JSON (parlays and bets)
    2. Load result JSON (final score, stats, tables)
    3. Send to Claude for intelligent analysis
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

        # Initialize repositories based on sport
        sport_code = config.sport_name.lower()  # "nfl" or "nba"
        self.prediction_repo = PredictionRepository(sport_code)
        self.results_repo = ResultsRepository(sport_code)
        self.analysis_repo = AnalysisRepository(sport_code)
        self.ev_results_repo = EVResultsRepository(sport_code)

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
        # 1. Load prediction and result data using repositories
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
            "prediction_file": self._get_prediction_identifier(game_key, game_meta),
            "result_file": self._get_result_identifier(game_key, game_meta),
            "generated_at": get_eastern_now().strftime("%Y-%m-%d %H:%M:%S"),
            "model": self.model,
            "api_cost": cost,
            "tokens": tokens
        })

        # 7. Save analysis using repository
        self._save_analysis(game_key, game_meta, analysis_data)

        return analysis_data

    def _load_prediction(self, game_key: str, game_meta: dict) -> dict:
        """Load prediction JSON file using repository.

        Args:
            game_key: Game identifier
            game_meta: Game metadata

        Returns:
            Prediction data dictionary
        """
        game_date = game_meta.get("game_date")

        # Extract team abbreviations from game_key
        # game_key format: "{date}_{home_abbr}_{away_abbr}" (e.g., "2025-11-02_cin_chi")
        parts = game_key.split("_")
        if parts[0] == game_date:
            team_a_abbr = parts[1] if len(parts) > 1 else "unknown"  # home
            team_b_abbr = parts[2] if len(parts) > 2 else "unknown"  # away
        else:
            # Fallback: try to extract from metadata or raise error
            raise Exception(f"Unable to parse team abbreviations from game_key: {game_key}")

        data = self.prediction_repo.load_prediction(game_date, team_a_abbr, team_b_abbr)

        if data is None:
            raise Exception(f"Prediction file not found: {game_date}/{team_a_abbr}_{team_b_abbr}.json")

        return data

    def _load_result(self, game_key: str, game_meta: dict) -> dict:
        """Load result JSON file using repository.

        Args:
            game_key: Game identifier
            game_meta: Game metadata

        Returns:
            Result data dictionary
        """
        game_date = game_meta.get("game_date")

        # Extract team abbreviations from game_key
        # game_key format: "{date}_{home_abbr}_{away_abbr}" (e.g., "2025-11-02_cin_chi")
        parts = game_key.split("_")
        if parts[0] == game_date:
            home_abbr = parts[1] if len(parts) > 1 else "unknown"
            away_abbr = parts[2] if len(parts) > 2 else "unknown"
        else:
            # Fallback: try to extract from metadata or raise error
            raise Exception(f"Unable to parse team abbreviations from game_key: {game_key}")

        # Results format: {away_abbr}_at_{home_abbr}.json
        data = self.results_repo.load_result(game_date, away_abbr, home_abbr)

        if data is None:
            raise Exception(f"Result file not found: {game_date}/{away_abbr}_at_{home_abbr}.json")

        return data

    def _extract_filename_from_key(self, game_key: str, game_date: str) -> str:
        """Extract filename from game key.

        Args:
            game_key: Game identifier (e.g., "w8_team1_team2" or "2025-10-23_team1_team2")
            game_date: Game date string

        Returns:
            Filename without extension
        """
        parts = game_key.split("_")

        # Remove date prefix if present
        if parts[0] == game_date:
            return "_".join(parts[1:])
        else:
            return game_key

    def _get_prediction_identifier(self, game_key: str, game_meta: dict) -> str:
        """Get prediction file identifier for metadata.

        Args:
            game_key: Game identifier
            game_meta: Game metadata

        Returns:
            Relative path to prediction file
        """
        game_date = game_meta.get("game_date")
        filename = self._extract_filename_from_key(game_key, game_date)
        return f"{self.config.sport_name}/data/predictions/{game_date}/{filename}.json"

    def _get_result_identifier(self, game_key: str, game_meta: dict) -> str:
        """Get result file identifier for metadata.

        Args:
            game_key: Game identifier
            game_meta: Game metadata

        Returns:
            Relative path to result file
        """
        game_date = game_meta.get("game_date")
        filename = self._extract_filename_from_key(game_key, game_date)
        return f"{self.config.sport_name}/data/results/{game_date}/{filename}.json"

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

        # Calculate cost using shared config
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        total_cost = calculate_api_cost(input_tokens, output_tokens, self.model)

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

        # Add margin calculations for each bet
        if 'bet_results' in analysis_data:
            for bet in analysis_data['bet_results']:
                # Get predicted line and actual numeric values
                predicted_line = bet.get('predicted_line')
                actual_numeric = bet.get('actual_numeric')

                # Only calculate margin if both values are not None
                if predicted_line is not None and actual_numeric is not None:
                    # Calculate margin (actual - predicted)
                    bet['margin'] = actual_numeric - predicted_line

                    # Calculate margin percentage
                    if predicted_line != 0:
                        bet['margin_pct'] = round((bet['margin'] / predicted_line) * 100, 2)
                    else:
                        bet['margin_pct'] = 0
                else:
                    # For bets without numeric lines (moneylines, TDs, spreads)
                    bet['margin'] = None
                    bet['margin_pct'] = None

                # Classify bet type
                bet['bet_type'] = self._classify_bet_type(bet.get('bet', ''))

        return analysis_data

    def _classify_bet_type(self, bet_description: str) -> str:
        """Classify bet into type based on description.

        Args:
            bet_description: Bet description string

        Returns:
            Bet type: "player_prop", "spread", "total", or "moneyline"
        """
        bet_lower = bet_description.lower()

        # Player props (contains over/under with stat types)
        if any(word in bet_lower for word in ['over', 'under']):
            if any(stat in bet_lower for stat in ['rushing', 'passing', 'receiving', 'reception', 'yards', 'touchdowns', 'tds']):
                return "player_prop"
            elif 'total' in bet_lower:
                return "total"

        # Spreads (contains + or - with team name)
        if ('+' in bet_description or '-' in bet_description) and 'ml' not in bet_lower:
            return "spread"

        # Moneyline
        if 'ml' in bet_lower or 'moneyline' in bet_lower:
            return "moneyline"

        return "unknown"

    def _save_analysis(self, game_key: str, game_meta: dict, analysis_data: dict):
        """Save analysis using repository.

        Args:
            game_key: Game identifier
            game_meta: Game metadata
            analysis_data: Analysis dictionary to save
        """
        game_date = game_meta.get("game_date")

        # Extract team abbreviations from game_key
        # game_key format: "{date}_{home_abbr}_{away_abbr}" (e.g., "2025-11-02_cin_chi")
        parts = game_key.split("_")
        if parts[0] == game_date:
            team_a_abbr = parts[1] if len(parts) > 1 else "unknown"  # home
            team_b_abbr = parts[2] if len(parts) > 2 else "unknown"  # away
        else:
            # Fallback: try to extract from metadata or raise error
            raise Exception(f"Unable to parse team abbreviations from game_key: {game_key}")

        # Save using repository
        self.analysis_repo.save_analysis(game_date, team_a_abbr, team_b_abbr, analysis_data)

        print(f"    [dim]Analysis saved to {self.config.sport_name}/data/analysis/{game_date}/{team_a_abbr}_{team_b_abbr}.json[/dim]")

    def _load_ev_prediction(self, game_key: str, game_meta: dict) -> Optional[dict]:
        """Load EV prediction JSON file using repository.

        Args:
            game_key: Game identifier
            game_meta: Game metadata

        Returns:
            EV prediction data dictionary or None if not found
        """
        game_date = game_meta.get("game_date")

        # Extract team abbreviations from game_key
        parts = game_key.split("_")
        if parts[0] == game_date:
            team_a_abbr = parts[1] if len(parts) > 1 else "unknown"
            team_b_abbr = parts[2] if len(parts) > 2 else "unknown"
        else:
            raise Exception(f"Unable to parse team abbreviations from game_key: {game_key}")

        return self.ev_results_repo.load_ev_results(game_date, team_a_abbr, team_b_abbr)

    def check_prediction_types(self, game_key: str, game_meta: dict) -> dict:
        """Check which prediction types exist for a game.

        Args:
            game_key: Game identifier
            game_meta: Game metadata

        Returns:
            Dict with 'has_ai' and 'has_ev' boolean flags
        """
        has_ai = False
        has_ev = False

        try:
            ai_prediction = self._load_prediction(game_key, game_meta)
            has_ai = ai_prediction is not None
        except:
            pass

        try:
            ev_prediction = self._load_ev_prediction(game_key, game_meta)
            has_ev = ev_prediction is not None
        except:
            pass

        return {"has_ai": has_ai, "has_ev": has_ev}

    def generate_dual_analysis(self, game_key: str, game_meta: dict) -> dict:
        """Generate analysis for both AI and EV predictions vs actual results.

        Args:
            game_key: Unique game identifier
            game_meta: Game metadata from predictions metadata file

        Returns:
            Combined analysis data dictionary with both systems' results

        Raises:
            Exception: If prediction or result files not found, or API call fails
        """
        # 1. Load both prediction types and result data
        ai_prediction_data = self._load_prediction(game_key, game_meta)
        ev_prediction_data = self._load_ev_prediction(game_key, game_meta)
        result_data = self._load_result(game_key, game_meta)

        # Validate result data
        self._validate_result_tables(result_data)

        # 2. Analyze AI predictions if they exist
        ai_analysis = None
        ai_cost = 0
        ai_tokens = {}

        if ai_prediction_data:
            prompt = self._build_analysis_prompt(ai_prediction_data, result_data)
            analysis_text, cost, tokens = self._call_claude_api(prompt)
            ai_analysis = self._parse_analysis_response(analysis_text)
            ai_cost = cost
            ai_tokens = tokens

        # 3. Analyze EV predictions if they exist
        ev_analysis = None
        ev_cost = 0
        ev_tokens = {}

        if ev_prediction_data:
            # Build EV-specific prompt (convert EV format to match AI format)
            ev_formatted = self._convert_ev_to_analysis_format(ev_prediction_data)
            prompt = self._build_analysis_prompt(ev_formatted, result_data)
            analysis_text, cost, tokens = self._call_claude_api(prompt)
            ev_analysis = self._parse_analysis_response(analysis_text)
            ev_cost = cost
            ev_tokens = tokens

        # 4. Combine both analyses
        combined_analysis = {
            "sport": self.config.sport_name,
            "game_date": game_meta.get("game_date"),
            "teams": {
                "away": result_data.get("teams", {}).get("away"),
                "home": result_data.get("teams", {}).get("home")
            },
            "final_score": result_data.get("final_score"),
            "generated_at": get_eastern_now().strftime("%Y-%m-%d %H:%M:%S"),
            "model": self.model,
            "total_api_cost": ai_cost + ev_cost,
            "total_tokens": {
                "input": ai_tokens.get("input", 0) + ev_tokens.get("input", 0),
                "output": ai_tokens.get("output", 0) + ev_tokens.get("output", 0),
                "total": ai_tokens.get("total", 0) + ev_tokens.get("total", 0)
            }
        }

        # Add AI system results if available
        if ai_analysis:
            combined_analysis["ai_system"] = {
                "prediction_file": self._get_prediction_identifier(game_key, game_meta).replace(".json", "_ai.json"),
                "bet_results": ai_analysis.get("bet_results", []),
                "summary": ai_analysis.get("summary", {}),
                "insights": ai_analysis.get("insights", []),
                "api_cost": ai_cost,
                "tokens": ai_tokens
            }

        # Add EV system results if available
        if ev_analysis:
            game_date = game_meta.get("game_date")
            filename = self._extract_filename_from_key(game_key, game_date)
            combined_analysis["ev_system"] = {
                "prediction_file": f"{self.config.sport_name}/data/predictions/{game_date}/{filename}_ev.json",
                "bet_results": ev_analysis.get("bet_results", []),
                "summary": ev_analysis.get("summary", {}),
                "insights": ev_analysis.get("insights", []),
                "api_cost": ev_cost,
                "tokens": ev_tokens
            }

        # 5. Add comparison if both exist
        if ai_analysis and ev_analysis:
            combined_analysis["comparison"] = self._compare_system_results(ai_analysis, ev_analysis)

        # 6. Save combined analysis
        self._save_analysis(game_key, game_meta, combined_analysis)

        return combined_analysis

    def _convert_ev_to_analysis_format(self, ev_prediction_data: dict) -> dict:
        """Convert EV prediction format to match AI prediction format for analysis.

        Args:
            ev_prediction_data: EV prediction data with 'bets' list

        Returns:
            Formatted dict matching AI prediction structure
        """
        # Convert EV bet format to AI bet format
        formatted_bets = []
        for bet in ev_prediction_data.get("bets", []):
            formatted_bets.append({
                "rank": bet.get("rank"),
                "bet": bet.get("description"),  # EV uses 'description', AI uses 'bet'
                "odds": bet.get("odds"),
                "ev_percent": bet.get("ev_percent")
            })

        return {
            "sport": ev_prediction_data.get("sport"),
            "teams": ev_prediction_data.get("teams"),
            "home_team": ev_prediction_data.get("home_team"),
            "date": ev_prediction_data.get("date"),
            "bets": formatted_bets
        }

    def _compare_system_results(self, ai_analysis: dict, ev_analysis: dict) -> dict:
        """Compare performance between AI and EV systems.

        Args:
            ai_analysis: AI system analysis results
            ev_analysis: EV system analysis results

        Returns:
            Comparison dictionary with consensus metrics
        """
        ai_summary = ai_analysis.get("summary", {})
        ev_summary = ev_analysis.get("summary", {})

        # Find consensus bets (bets that appear in both systems and both won)
        ai_bets = ai_analysis.get("bet_results", [])
        ev_bets = ev_analysis.get("bet_results", [])

        consensus_winners = []
        for ai_bet in ai_bets:
            if not ai_bet.get("won"):
                continue

            # Simple matching: check if any EV bet won and has similar description
            ai_desc = ai_bet.get("bet", "").lower()
            for ev_bet in ev_bets:
                if not ev_bet.get("won"):
                    continue

                ev_desc = ev_bet.get("bet", "").lower()

                # Basic fuzzy matching - check if player name appears in both
                ai_words = set(ai_desc.split())
                ev_words = set(ev_desc.split())
                common_words = ai_words.intersection(ev_words)

                # If they share 2+ words (likely player name), consider it a match
                if len(common_words) >= 2:
                    consensus_winners.append({
                        "ai_bet": ai_bet.get("bet"),
                        "ev_bet": ev_bet.get("bet"),
                        "ai_profit": ai_bet.get("profit"),
                        "ev_profit": ev_bet.get("profit")
                    })
                    break

        return {
            "consensus_winners": consensus_winners,
            "consensus_count": len(consensus_winners),
            "ai_win_rate": ai_summary.get("win_rate", 0),
            "ev_win_rate": ev_summary.get("win_rate", 0),
            "ai_roi": ai_summary.get("roi_percent", 0),
            "ev_roi": ev_summary.get("roi_percent", 0),
            "ai_total_profit": ai_summary.get("total_profit", 0),
            "ev_total_profit": ev_summary.get("total_profit", 0),
            "better_system": "ai" if ai_summary.get("total_profit", 0) > ev_summary.get("total_profit", 0) else "ev"
        }
