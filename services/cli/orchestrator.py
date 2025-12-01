"""CLI Orchestrator service for coordinating betting workflows.

This service coordinates between ODDS, PREDICTION, RESULTS, and ANALYSIS
services to provide unified CLI workflows.
"""

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from services.cli.config import CLIServiceConfig, get_default_config
from shared.logging import get_logger


class CLIOrchestrator:
    """Orchestrates CLI workflows across multiple services.

    This class coordinates the flow between fetching odds, generating
    predictions, fetching results, and running analysis.

    Attributes:
        sport: Sport code ('nfl' or 'nba')
        config: CLI service configuration
        logger: Service logger
    """

    def __init__(
        self,
        sport: str,
        config: Optional[CLIServiceConfig] = None,
    ):
        """Initialize CLIOrchestrator.

        Args:
            sport: Sport code ('nfl' or 'nba')
            config: CLI service configuration
        """
        self.sport = sport.lower()
        self.config = config or get_default_config()
        self.logger = get_logger("cli")

        # Lazy-loaded services
        self._odds_service = None
        self._prediction_service = None
        self._results_service = None
        self._analysis_service = None

    @property
    def odds_service(self):
        """Get or create odds service (lazy loading)."""
        if self._odds_service is None:
            from services.odds import OddsService
            self._odds_service = OddsService(sport=self.sport)
        return self._odds_service

    @property
    def results_service(self):
        """Get or create results service (lazy loading)."""
        if self._results_service is None:
            from services.results import ResultsService
            self._results_service = ResultsService(sport=self.sport)
        return self._results_service

    @property
    def prediction_service(self):
        """Get or create prediction service (lazy loading)."""
        if self._prediction_service is None:
            from services.prediction import PredictionService
            from shared.factory import SportFactory
            sport = SportFactory.create(self.sport)
            self._prediction_service = PredictionService(
                sport=self.sport,
                sport_config=sport.config,
            )
        return self._prediction_service

    @property
    def analysis_service(self):
        """Get or create analysis service (lazy loading)."""
        if self._analysis_service is None:
            from services.analysis import AnalysisService
            self._analysis_service = AnalysisService(sport=self.sport)
        return self._analysis_service

    def fetch_odds_workflow(
        self,
        game_date: str,
        games: List[Dict[str, str]],
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> Dict[str, Any]:
        """Execute odds fetching workflow.

        Args:
            game_date: Game date in YYYY-MM-DD format
            games: List of game dicts with team info
            progress_callback: Optional callback(message, current, total)

        Returns:
            Workflow result summary
        """
        self.logger.info(f"Starting odds fetch workflow for {len(games)} games on {game_date}")

        results = {
            "success": True,
            "game_date": game_date,
            "games_processed": 0,
            "games_skipped": 0,
            "games_failed": 0,
            "details": [],
        }

        for i, game in enumerate(games):
            if progress_callback:
                progress_callback(
                    f"Fetching odds for {game.get('away_team', '?')} @ {game.get('home_team', '?')}",
                    i + 1,
                    len(games),
                )

            try:
                # Check if already exists
                if self.config.workflow.skip_existing:
                    existing = self.odds_service.load_odds(
                        game_date,
                        game.get("away_team", ""),
                        game.get("home_team", ""),
                    )
                    if existing:
                        results["games_skipped"] += 1
                        results["details"].append({
                            "game": game,
                            "status": "skipped",
                            "reason": "Already exists",
                        })
                        continue

                # Fetch odds (implementation depends on OddsService)
                # This is a placeholder - actual implementation would call scraper
                results["games_processed"] += 1
                results["details"].append({
                    "game": game,
                    "status": "success",
                })

            except Exception as e:
                self.logger.error(f"Error fetching odds for {game}: {e}")
                results["games_failed"] += 1
                results["details"].append({
                    "game": game,
                    "status": "failed",
                    "error": str(e),
                })

        results["success"] = results["games_failed"] == 0
        return results

    def fetch_results_workflow(
        self,
        game_date: str,
        games: List[Dict[str, str]],
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> Dict[str, Any]:
        """Execute results fetching workflow.

        Args:
            game_date: Game date in YYYY-MM-DD format
            games: List of game dicts with team info
            progress_callback: Optional callback(message, current, total)

        Returns:
            Workflow result summary
        """
        self.logger.info(f"Starting results fetch workflow for {len(games)} games on {game_date}")

        results = {
            "success": True,
            "game_date": game_date,
            "games_processed": 0,
            "games_skipped": 0,
            "games_failed": 0,
            "details": [],
        }

        for i, game in enumerate(games):
            if progress_callback:
                progress_callback(
                    f"Fetching results for {game.get('away_team', '?')} @ {game.get('home_team', '?')}",
                    i + 1,
                    len(games),
                )

            try:
                away_team = game.get("away_team", "")
                home_team = game.get("home_team", "")

                # Check if already exists
                if self.config.workflow.skip_existing:
                    existing = self.results_service.load_result(
                        game_date, away_team, home_team
                    )
                    if existing:
                        results["games_skipped"] += 1
                        results["details"].append({
                            "game": game,
                            "status": "skipped",
                            "reason": "Already exists",
                        })
                        continue

                # Fetch results
                result_data = self.results_service.fetch_game_result(
                    game_date=game_date,
                    away_team=away_team,
                    home_team=home_team,
                )

                if result_data and self.config.workflow.save_results:
                    self.results_service.save_result(
                        result_data, game_date, away_team, home_team
                    )

                results["games_processed"] += 1
                results["details"].append({
                    "game": game,
                    "status": "success",
                    "result": result_data,
                })

            except Exception as e:
                self.logger.error(f"Error fetching results for {game}: {e}")
                results["games_failed"] += 1
                results["details"].append({
                    "game": game,
                    "status": "failed",
                    "error": str(e),
                })

        results["success"] = results["games_failed"] == 0
        return results

    def analyze_workflow(
        self,
        game_date: str,
        games: List[Dict[str, str]],
        prediction_loader: Callable[[str, Dict], Optional[Dict]],
        result_loader: Callable[[str, Dict], Optional[Dict]],
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> Dict[str, Any]:
        """Execute analysis workflow.

        Args:
            game_date: Game date in YYYY-MM-DD format
            games: List of game dicts with team info
            prediction_loader: Function to load prediction data
            result_loader: Function to load result data
            progress_callback: Optional callback(message, current, total)

        Returns:
            Workflow result summary with aggregate statistics
        """
        self.logger.info(f"Starting analysis workflow for {len(games)} games on {game_date}")

        # Use AnalysisService batch method
        return self.analysis_service.analyze_games_batch(
            game_date=game_date,
            games=games,
            prediction_loader=prediction_loader,
            result_loader=result_loader,
        )

    def full_pipeline_workflow(
        self,
        game_date: str,
        games: List[Dict[str, str]],
        fetch_odds: bool = True,
        generate_predictions: bool = True,
        fetch_results: bool = True,
        run_analysis: bool = True,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> Dict[str, Any]:
        """Execute full betting pipeline workflow.

        This is the main workflow that runs:
        1. Fetch odds for all games
        2. Generate predictions for all games
        3. Fetch results for all games
        4. Run analysis comparing predictions to results

        Args:
            game_date: Game date in YYYY-MM-DD format
            games: List of game dicts with team info
            fetch_odds: Whether to fetch odds
            generate_predictions: Whether to generate predictions
            fetch_results: Whether to fetch results
            run_analysis: Whether to run analysis
            progress_callback: Optional callback(message, current, total)

        Returns:
            Full workflow result summary
        """
        self.logger.info(f"Starting full pipeline for {len(games)} games on {game_date}")

        results = {
            "success": True,
            "game_date": game_date,
            "total_games": len(games),
            "stages": {},
        }

        total_stages = sum([fetch_odds, generate_predictions, fetch_results, run_analysis])
        current_stage = 0

        # Stage 1: Fetch odds
        if fetch_odds:
            current_stage += 1
            if progress_callback:
                progress_callback(f"Stage {current_stage}/{total_stages}: Fetching odds", current_stage, total_stages)

            odds_result = self.fetch_odds_workflow(game_date, games)
            results["stages"]["odds"] = odds_result
            if not odds_result["success"]:
                results["success"] = False

        # Stage 2: Generate predictions
        if generate_predictions:
            current_stage += 1
            if progress_callback:
                progress_callback(f"Stage {current_stage}/{total_stages}: Generating predictions", current_stage, total_stages)

            # Predictions would be generated here
            results["stages"]["predictions"] = {
                "success": True,
                "message": "Prediction generation not yet integrated",
            }

        # Stage 3: Fetch results
        if fetch_results:
            current_stage += 1
            if progress_callback:
                progress_callback(f"Stage {current_stage}/{total_stages}: Fetching results", current_stage, total_stages)

            results_result = self.fetch_results_workflow(game_date, games)
            results["stages"]["results"] = results_result
            if not results_result["success"]:
                results["success"] = False

        # Stage 4: Run analysis
        if run_analysis:
            current_stage += 1
            if progress_callback:
                progress_callback(f"Stage {current_stage}/{total_stages}: Running analysis", current_stage, total_stages)

            def load_prediction(date, game):
                # Load from prediction service
                return None  # Placeholder

            def load_result(date, game):
                return self.results_service.load_result(
                    date,
                    game.get("away_team", ""),
                    game.get("home_team", ""),
                )

            analysis_result = self.analyze_workflow(
                game_date, games, load_prediction, load_result
            )
            results["stages"]["analysis"] = analysis_result

        self.logger.info(f"Full pipeline completed: {results['success']}")
        return results

    def get_workflow_summary(self, workflow_result: Dict[str, Any]) -> str:
        """Generate human-readable summary of workflow result.

        Args:
            workflow_result: Result from any workflow method

        Returns:
            Formatted summary string
        """
        lines = []
        lines.append(f"Workflow for {workflow_result.get('game_date', 'Unknown date')}")
        lines.append("-" * 40)

        if "stages" in workflow_result:
            # Full pipeline result
            for stage, result in workflow_result["stages"].items():
                status = "✅" if result.get("success", False) else "❌"
                lines.append(f"{status} {stage.upper()}")
                if "games_processed" in result:
                    lines.append(f"   Processed: {result['games_processed']}")
                if "games_skipped" in result:
                    lines.append(f"   Skipped: {result['games_skipped']}")
                if "games_failed" in result:
                    lines.append(f"   Failed: {result['games_failed']}")
        else:
            # Single workflow result
            processed = workflow_result.get("games_processed", 0)
            skipped = workflow_result.get("games_skipped", 0)
            failed = workflow_result.get("games_failed", 0)
            lines.append(f"Processed: {processed}")
            lines.append(f"Skipped: {skipped}")
            lines.append(f"Failed: {failed}")

        return "\n".join(lines)
