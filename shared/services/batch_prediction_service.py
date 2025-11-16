"""Service for running dual predictions (EV Calculator + AI Predictor) in batch."""

import os
import json
import re
import time
from typing import Dict, List, Tuple
from datetime import datetime
from tqdm import tqdm

from shared.models.ev_calculator import EVCalculator
from shared.base.predictor import Predictor
from shared.services.comparison_service import ComparisonService
from shared.repositories.ev_results_repository import EVResultsRepository
from shared.repositories.comparison_repository import ComparisonRepository
from shared.repositories.prediction_repository import PredictionRepository
from shared.repositories.odds_repository import OddsRepository
from shared.config import get_data_path
from shared.utils.timezone_utils import get_eastern_now


class BatchPredictionService:
    """Service for running both EV Calculator and AI Predictor on multiple games."""

    def __init__(self, sport_code: str, sport_config):
        """Initialize batch prediction service.

        Args:
            sport_code: Sport identifier (e.g., 'nfl')
            sport_config: Sport configuration object
        """
        self.sport_code = sport_code
        self.sport_config = sport_config

        # Initialize repositories
        self.ev_repo = EVResultsRepository(sport_code)
        self.comparison_repo = ComparisonRepository(sport_code)
        self.prediction_repo = PredictionRepository(sport_code)
        self.odds_repo = OddsRepository(sport_code)

        # Initialize services
        self.comparison_service = ComparisonService()
        self.predictor = Predictor(sport_config)

    @staticmethod
    def _parse_ev_singles_text(prediction_text: str) -> list[dict]:
        """Parse EV singles prediction text to extract structured bet data.

        Returns:
            List of bet dictionaries with EV analysis
        """
        bets = []
        # Pattern to match simplified EV singles output format (no Calculation, no per-bet Reasoning)
        bet_pattern = r'## Bet (\d+):.+?\n\*\*Bet\*\*: (.+?)\n\*\*Odds\*\*: ([+-]?\d+)\n\*\*Implied Probability\*\*: ([\d.]+)%[^\n]*\n\*\*True Probability\*\*: ([\d.]+)%[^\n]*\n\*\*Expected Value\*\*: \+?([\d.]+)%'

        for match in re.finditer(bet_pattern, prediction_text, re.DOTALL):
            bets.append({
                "rank": int(match.group(1)),
                "bet": match.group(2).strip(),
                "odds": int(match.group(3)),
                "implied_probability": float(match.group(4)),
                "true_probability": float(match.group(5)),
                "expected_value": float(match.group(6))
            })

        return bets

    def run_dual_predictions(
        self,
        game_date: str,
        base_dir: str = ".",
        conservative_adjustment: float = 0.85,
        min_ev_threshold: float = 3.0,
        skip_existing: bool = True
    ) -> Dict:
        """Run both EV Calculator and AI Predictor for all games on a date.

        Args:
            game_date: Game date in YYYY-MM-DD format
            base_dir: Base directory for data files
            conservative_adjustment: EV calculator conservative adjustment (0.85 = 15% reduction)
            min_ev_threshold: Minimum EV% to include in results (default 3.0%)
            skip_existing: If True, skip games that already have both predictions

        Returns:
            Summary dictionary with results
        """
        # Load schedule
        schedule_path = os.path.join(
            get_data_path(self.sport_code, "odds", game_date=game_date),
            "schedule.json"
        )

        if not os.path.exists(schedule_path):
            return {
                "success": False,
                "error": f"No schedule found for {game_date}. Please fetch odds first.",
                "games_processed": 0
            }

        with open(schedule_path, 'r') as f:
            schedule = json.load(f)

        # Filter games: not started + odds fetched + valid team abbreviations
        eligible_games = [
            game for game in schedule.get("games", [])
            if (not game.get("has_started", True)
                and game.get("odds_fetched", False)
                and game.get("teams", {}).get("away", {}).get("pfr_abbr")
                and game.get("teams", {}).get("home", {}).get("pfr_abbr"))
        ]

        if not eligible_games:
            return {
                "success": True,
                "message": f"No eligible games found for {game_date}",
                "games_processed": 0,
                "total_cost": 0.0
            }

        # Process each game
        results = {
            "success": True,
            "games_processed": 0,
            "games_skipped": 0,
            "total_cost": 0.0,
            "total_time": 0.0,
            "agreement_rates": [],
            "ev_results": [],
            "ai_predictions": [],
            "comparisons": [],
            "errors": []
        }

        print(f"\n{'=' * 70}")
        print(f"BATCH DUAL PREDICTION: {game_date}")
        print(f"{'=' * 70}")
        print(f"Eligible games: {len(eligible_games)}")
        print(f"{'=' * 70}\n")

        with tqdm(total=len(eligible_games), desc="Processing games", unit="game") as pbar:
            for idx, game in enumerate(eligible_games):
                game_start_time = time.time()

                # Extract game info
                teams = game.get("teams", {})
                away_name = teams.get("away", {}).get("name", "")
                home_name = teams.get("home", {}).get("name", "")
                # Use 'or' pattern for None-safety when pfr_abbr exists but is None
                away_abbr = (teams.get("away", {}).get("pfr_abbr") or "").lower()
                home_abbr = (teams.get("home", {}).get("pfr_abbr") or "").lower()

                pbar.set_description(f"[{results['games_processed']+1}/{len(eligible_games)}] {away_abbr.upper()} @ {home_abbr.upper()}")

                # Check if both predictions already exist
                if skip_existing:
                    ev_exists = self.ev_repo.load_ev_results(game_date, home_abbr, away_abbr) is not None
                    ai_exists = self.prediction_repo.load_prediction(game_date, home_abbr, away_abbr) is not None

                    if ev_exists and ai_exists:
                        results["games_skipped"] += 1
                        pbar.write(f"  ⏭️  Skipping (predictions already exist)")
                        pbar.update(1)
                        continue

                ai_prediction_made = False
                try:
                    # Run dual prediction for this game
                    game_result = self._process_single_game(
                        game_date=game_date,
                        away_name=away_name,
                        home_name=home_name,
                        away_abbr=away_abbr,
                        home_abbr=home_abbr,
                        base_dir=base_dir,
                        conservative_adjustment=conservative_adjustment,
                        min_ev_threshold=min_ev_threshold
                    )

                    if game_result["success"]:
                        results["games_processed"] += 1
                        results["total_cost"] += game_result.get("ai_cost", 0.0)
                        results["agreement_rates"].append(game_result.get("agreement_rate", 0.0))
                        results["ev_results"].append(game_result["ev_file"])
                        results["ai_predictions"].append(game_result["ai_file"])
                        results["comparisons"].append(game_result["comparison_file"])

                        # Display results
                        game_time = time.time() - game_start_time
                        results["total_time"] += game_time

                        pbar.write(f"  ✅ EV complete ({game_result['ev_time']:.1f}s)")
                        pbar.write(f"  ✅ AI complete ({game_result['ai_time']:.1f}s, ${game_result['ai_cost']:.2f})")
                        pbar.write(f"  ✅ Comparison saved (agreement: {game_result['agreement_rate']:.1%})")
                        ai_prediction_made = True
                    else:
                        results["errors"].append({
                            "game": f"{away_abbr}_at_{home_abbr}",
                            "error": game_result.get("error", "Unknown error")
                        })
                        pbar.write(f"  ❌ Error: {game_result.get('error', 'Unknown error')}")

                except Exception as e:
                    results["errors"].append({
                        "game": f"{away_abbr}_at_{home_abbr}",
                        "error": str(e)
                    })
                    pbar.write(f"  ❌ Error: {str(e)}")

                pbar.update(1)

                # Rate limiting: Wait 60 seconds between AI predictions (not on last game)
                if ai_prediction_made and idx < len(eligible_games) - 1:
                    pbar.write(f"  ⏸️  Waiting 60s to avoid rate limits...")
                    time.sleep(60)

        # Print summary
        print(f"\n{'=' * 70}")
        print("BATCH DUAL PREDICTION SUMMARY")
        print(f"{'=' * 70}")
        print(f"Games processed: {results['games_processed']}/{len(eligible_games)}")
        print(f"Games skipped: {results['games_skipped']}")
        print(f"Total API cost: ${results['total_cost']:.2f}")
        print(f"Total time: {results['total_time'] / 60:.1f}m")

        if results["agreement_rates"]:
            avg_agreement = sum(results["agreement_rates"]) / len(results["agreement_rates"])
            print(f"Avg agreement rate: {avg_agreement:.1%}")

        print(f"\nFiles created:")
        print(f"  - {results['games_processed']} AI predictions (*_ai.json)")
        print(f"  - {results['games_processed']} EV results (*_ev.json)")
        print(f"  - {results['games_processed']} comparisons (*_comparison.json)")

        if results["errors"]:
            print(f"\nErrors: {len(results['errors'])}")
            for err in results["errors"]:
                print(f"  - {err['game']}: {err['error']}")

        print(f"{'=' * 70}\n")

        return results

    def _process_single_game(
        self,
        game_date: str,
        away_name: str,
        home_name: str,
        away_abbr: str,
        home_abbr: str,
        base_dir: str,
        conservative_adjustment: float,
        min_ev_threshold: float
    ) -> Dict:
        """Process a single game with both systems.

        Args:
            game_date: Game date in YYYY-MM-DD format
            away_name: Away team full name
            home_name: Home team full name
            away_abbr: Away team abbreviation
            home_abbr: Home team abbreviation
            base_dir: Base directory for data
            conservative_adjustment: EV conservative adjustment
            min_ev_threshold: Minimum EV threshold

        Returns:
            Result dictionary with success status and data
        """
        try:
            # Load odds
            odds_data = self.odds_repo.load_odds(game_date, away_abbr, home_abbr)
            if not odds_data:
                return {"success": False, "error": "Odds not found"}

            # 1. Run EV Calculator
            ev_start = time.time()
            ev_calculator = EVCalculator(
                odds_data=odds_data,
                sport_config=self.sport_config,
                base_dir=base_dir,
                conservative_adjustment=conservative_adjustment
            )

            top_ev_bets = ev_calculator.get_top_n(
                n=5,
                min_ev_threshold=min_ev_threshold,
                deduplicate_players=True
            )

            # Count total bets analyzed
            all_bets = ev_calculator.calculate_all_ev(min_ev_threshold=0.0)
            total_bets_analyzed = len(all_bets)

            # Format and save EV results
            ev_results = self.ev_repo.format_ev_results_for_save(
                ev_calculator_output=top_ev_bets,
                teams=[away_name, home_name],
                home_team=home_name,
                game_date=game_date,
                total_bets_analyzed=total_bets_analyzed,
                conservative_adjustment=conservative_adjustment
            )

            self.ev_repo.save_ev_results(game_date, home_abbr, away_abbr, ev_results, "json")

            # Also save markdown
            ev_markdown = self.ev_repo.format_ev_results_to_markdown(ev_results)
            self.ev_repo.save_ev_results(game_date, home_abbr, away_abbr, ev_markdown, "md")

            ev_time = time.time() - ev_start

            # 2. Run AI Predictor
            ai_start = time.time()

            # Load data for AI predictor
            rankings = self.predictor.load_ranking_tables()
            profile_a = self.predictor.load_team_profile(away_name)
            profile_b = self.predictor.load_team_profile(home_name)

            ai_result = self.predictor.generate_predictions(
                team_a=away_name,
                team_b=home_name,
                home_team=home_name,
                rankings=rankings,
                profile_a=profile_a,
                profile_b=profile_b,
                odds=odds_data
            )

            # Check if AI prediction succeeded
            if not ai_result.get("success"):
                return {
                    "success": False,
                    "error": f"AI prediction failed: {ai_result.get('error', 'Unknown error')}"
                }

            # Parse AI prediction text into structured data
            prediction_text = ai_result["prediction"]
            bets = self._parse_ev_singles_text(prediction_text)

            # Calculate summary stats
            if bets:
                ev_values = [bet["expected_value"] for bet in bets]
                summary = {
                    "total_bets": len(bets),
                    "avg_ev": round(sum(ev_values) / len(ev_values), 2),
                    "ev_range": [round(min(ev_values), 2), round(max(ev_values), 2)]
                }
            else:
                summary = {"total_bets": 0, "avg_ev": 0, "ev_range": [0, 0]}

            # Build JSON structure for AI prediction
            prediction_data = {
                "sport": self.sport_code,
                "prediction_type": "ev_singles",
                "teams": [away_name, home_name],
                "home_team": home_name,
                "date": game_date,
                "generated_at": get_eastern_now().strftime("%Y-%m-%d %H:%M:%S"),
                "model": ai_result["model"],
                "api_cost": ai_result["cost"],
                "tokens": ai_result["tokens"],
                "bets": bets,
                "summary": summary
            }

            # Save AI prediction with _ai suffix
            self.prediction_repo.save_prediction(
                game_date, home_abbr, away_abbr,
                prediction_data,
                file_format="json",
                use_ai_suffix=True
            )
            self.prediction_repo.save_prediction(
                game_date, home_abbr, away_abbr,
                prediction_text,
                file_format="md",
                use_ai_suffix=True
            )

            ai_time = time.time() - ai_start
            ai_cost = ai_result.get("cost", 0.0)

            # 3. Generate Comparison
            comparison = self.comparison_service.compare_predictions(
                ev_results, prediction_data
            )

            self.comparison_repo.save_comparison(
                game_date, home_abbr, away_abbr, comparison
            )

            return {
                "success": True,
                "ev_time": ev_time,
                "ai_time": ai_time,
                "ai_cost": ai_cost,
                "agreement_rate": comparison.get("agreement_rate", 0.0),
                "ev_file": f"{home_abbr}_{away_abbr}_ev.json",
                "ai_file": f"{home_abbr}_{away_abbr}_ai.json",
                "comparison_file": f"{home_abbr}_{away_abbr}_comparison.json"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
