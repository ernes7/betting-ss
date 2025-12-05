"""Repository for EV calculator results data access."""

import os
from typing import Dict, List, Optional
from datetime import datetime
from shared.repositories.base_repository import BaseRepository
from shared.utils.path_utils import get_data_path, get_file_path


class EVResultsRepository(BaseRepository):
    """Repository for managing EV calculator results."""

    def __init__(self, sport_code: str):
        """Initialize the EV results repository.

        Args:
            sport_code: Sport identifier (e.g., 'nfl', 'nba')
        """
        self.sport_code = sport_code
        base_path = get_data_path(sport_code, "predictions")  # Same base as AI predictions
        super().__init__(base_path)

    def save_ev_results(
        self,
        game_date: str,
        team_a_abbr: str,
        team_b_abbr: str,
        ev_data: dict,
        file_format: str = "json"
    ) -> bool:
        """Save EV calculator results.

        Args:
            game_date: Game date in YYYY-MM-DD format
            team_a_abbr: First team abbreviation (lowercase)
            team_b_abbr: Second team abbreviation (lowercase)
            ev_data: EV results data dictionary
            file_format: File format ('json' or 'md')

        Returns:
            True if successful, False otherwise
        """
        file_type = "prediction_ev_json" if file_format == "json" else "prediction_ev"
        filepath = get_file_path(
            self.sport_code,
            "predictions",
            file_type,
            game_date=game_date,
            team_a_abbr=team_a_abbr,
            team_b_abbr=team_b_abbr
        )

        if file_format == "json":
            return self.save(filepath, ev_data)
        else:
            # For markdown files, ev_data should be a string
            try:
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(ev_data)
                return True
            except Exception as e:
                print(f"Error saving markdown file {filepath}: {str(e)}")
                return False

    def load_ev_results(
        self,
        game_date: str,
        team_a_abbr: str,
        team_b_abbr: str
    ) -> Optional[dict]:
        """Load EV calculator results.

        Args:
            game_date: Game date in YYYY-MM-DD format
            team_a_abbr: First team abbreviation (lowercase)
            team_b_abbr: Second team abbreviation (lowercase)

        Returns:
            EV results data dictionary or None
        """
        filepath = get_file_path(
            self.sport_code,
            "predictions",
            "prediction_ev_json",
            game_date=game_date,
            team_a_abbr=team_a_abbr,
            team_b_abbr=team_b_abbr
        )
        return self.load(filepath)

    def list_ev_results_for_date(self, game_date: str) -> List[dict]:
        """List all EV results for a specific date.

        Args:
            game_date: Game date in YYYY-MM-DD format

        Returns:
            List of EV results data dictionaries
        """
        results_dir = get_data_path(
            self.sport_code,
            "predictions",
            game_date=game_date
        )

        if not os.path.exists(results_dir):
            return []

        ev_results = []
        for filename in os.listdir(results_dir):
            # Only load files with _ev.json suffix
            if filename.endswith("_ev.json"):
                filepath = os.path.join(results_dir, filename)
                ev_data = self.load(filepath)
                if ev_data:
                    ev_results.append(ev_data)

        return ev_results

    def format_ev_results_for_save(
        self,
        ev_calculator_output: List[dict],
        teams: List[str],
        home_team: str,
        game_date: str,
        total_bets_analyzed: int = 0,
        conservative_adjustment: float = 0.85
    ) -> dict:
        """Format EV calculator output into standardized JSON structure.

        Args:
            ev_calculator_output: List of bet dicts from EVCalculator.get_top_n()
            teams: List of team names [away, home]
            home_team: Home team name
            game_date: Game date in YYYY-MM-DD format
            total_bets_analyzed: Total number of bets analyzed before filtering
            conservative_adjustment: Conservative adjustment factor used

        Returns:
            Formatted dict ready for saving
        """
        # Calculate summary statistics
        ev_values = [bet.get("ev_percent", 0) for bet in ev_calculator_output]
        avg_ev = sum(ev_values) / len(ev_values) if ev_values else 0

        # Count bets above 3% threshold (typical minimum)
        bets_above_3_percent = len([ev for ev in ev_values if ev >= 3.0])

        return {
            "sport": self.sport_code,
            "prediction_type": "ev_calculator",
            "teams": teams,
            "home_team": home_team,
            "date": game_date,
            "generated_at": datetime.now().isoformat(),
            "conservative_adjustment": conservative_adjustment,
            "bets": ev_calculator_output,  # Already formatted by EV calculator
            "summary": {
                "total_bets_analyzed": total_bets_analyzed,
                "bets_above_3_percent": bets_above_3_percent,
                "top_5_avg_ev": round(avg_ev, 2),
                "min_ev_threshold": 3.0
            }
        }

    def format_ev_results_to_markdown(self, ev_data: dict) -> str:
        """Format EV results as markdown.

        Args:
            ev_data: EV results dictionary (from format_ev_results_for_save)

        Returns:
            Markdown formatted string
        """
        teams = ev_data.get("teams", [])
        home_team = ev_data.get("home_team", "")
        date = ev_data.get("date", "")
        bets = ev_data.get("bets", [])
        summary = ev_data.get("summary", {})

        # Build markdown
        md = f"# EV Calculator Results: {teams[0]} @ {teams[1]}\n\n"
        md += f"**Date**: {date}  \n"
        md += f"**Home Team**: {home_team}  \n"
        md += f"**Generated**: {ev_data.get('generated_at', '')}  \n\n"

        md += "---\n\n"
        md += "## Summary\n\n"
        md += f"- Total bets analyzed: {summary.get('total_bets_analyzed', 0)}\n"
        md += f"- Bets above 3% EV: {summary.get('bets_above_3_percent', 0)}\n"
        md += f"- Top 5 average EV: {summary.get('top_5_avg_ev', 0)}%\n"
        md += f"- Conservative adjustment: {ev_data.get('conservative_adjustment', 0.85) * 100}%\n\n"

        md += "---\n\n"
        md += "## Top 5 EV+ Bets\n\n"

        for bet in bets:
            rank = bet.get("rank", 0)
            description = bet.get("description", "")
            odds = bet.get("odds", 0)
            ev_percent = bet.get("ev_percent", 0)
            implied_prob = bet.get("implied_prob", 0)
            true_prob = bet.get("true_prob", 0)
            adjusted_prob = bet.get("adjusted_prob", 0)
            reasoning = bet.get("reasoning", "")

            md += f"### Bet {rank}: {description}\n\n"
            md += f"**Odds**: {odds:+d} (Decimal: {bet.get('decimal_odds', 0):.2f})  \n"
            md += f"**Implied Probability**: {implied_prob:.1f}%  \n"
            md += f"**True Probability**: {true_prob:.1f}%  \n"
            md += f"**Adjusted Probability**: {adjusted_prob:.1f}%  \n"
            md += f"**Expected Value**: {ev_percent:+.2f}%  \n\n"
            md += f"**Reasoning**: {reasoning}\n\n"
            md += "---\n\n"

        return md
