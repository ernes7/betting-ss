"""Analysis service for comparing predictions to results."""

import json
import os
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from services.analysis.config import AnalysisServiceConfig, get_default_config
from services.analysis.bet_checker import BetChecker
from shared.logging import get_logger
from shared.repositories.analysis_repository import AnalysisRepository


class AnalysisService:
    """Service for analyzing bet predictions against actual results.

    This service compares predictions (EV or AI) against game results
    to determine bet outcomes and calculate performance metrics.

    Attributes:
        sport: Sport code (e.g., 'nfl', 'nba')
        config: Service configuration
        bet_checker: Component for checking bet results
        repository: Data access layer for analysis data
        logger: Service logger
    """

    def __init__(
        self,
        sport: str,
        config: Optional[AnalysisServiceConfig] = None,
        bet_checker: Optional[BetChecker] = None,
        repository: Optional[AnalysisRepository] = None,
    ):
        """Initialize AnalysisService.

        Args:
            sport: Sport code (e.g., 'nfl', 'nba')
            config: Service configuration (uses default if not provided)
            bet_checker: Bet checking component (creates default if not provided)
            repository: Analysis repository (creates default if not provided)
        """
        self.sport = sport.lower()
        self.config = config or get_default_config()
        self.logger = get_logger("analysis")

        # Initialize components with constructor injection
        self.bet_checker = bet_checker or BetChecker(
            matching_config=self.config.matching_config,
            profit_config=self.config.profit_config,
        )

        self.repository = repository or AnalysisRepository(
            sport_code=self.sport,
            analysis_type=self.config.analysis_type,
        )

    @property
    def analysis_dir(self) -> str:
        """Get the analysis directory path for this sport."""
        return self.config.data_root.format(sport=self.sport)

    def analyze_game(
        self,
        game_date: str,
        away_team: str,
        home_team: str,
        prediction_data: Dict[str, Any],
        result_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze a single game's predictions against results.

        Args:
            game_date: Game date in YYYY-MM-DD format
            away_team: Away team abbreviation
            home_team: Home team abbreviation
            prediction_data: Prediction JSON with bets array
            result_data: Results JSON with tables and final_score

        Returns:
            Analysis result dict with bet_results and summary
        """
        self.logger.info(f"Analyzing game: {away_team} @ {home_team} on {game_date}")

        # Check all bets against results
        analysis_result = self.bet_checker.check_all_bets(
            prediction_data, result_data
        )

        # Add metadata
        analysis_result["sport"] = self.sport
        analysis_result["game_date"] = game_date
        analysis_result["away_team"] = away_team
        analysis_result["home_team"] = home_team
        analysis_result["matchup"] = f"{away_team} @ {home_team}"
        analysis_result["analyzed_at"] = datetime.now().isoformat()
        analysis_result["prediction_type"] = prediction_data.get(
            "prediction_type", "unknown"
        )

        # Add final score info
        if "final_score" in result_data:
            analysis_result["final_score"] = result_data["final_score"]

        self.logger.info(
            f"Analysis complete: {analysis_result['summary']['bets_won']}/{analysis_result['summary']['total_bets']} won, "
            f"ROI: {analysis_result['summary']['roi_percent']}%"
        )

        return analysis_result

    def analyze_and_save(
        self,
        game_date: str,
        away_team: str,
        home_team: str,
        prediction_data: Dict[str, Any],
        result_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze a game and save the results.

        Args:
            game_date: Game date in YYYY-MM-DD format
            away_team: Away team abbreviation
            home_team: Home team abbreviation
            prediction_data: Prediction JSON with bets array
            result_data: Results JSON with tables and final_score

        Returns:
            Analysis result dict
        """
        # Check if analysis already exists
        if self.config.skip_existing:
            if self.repository.analysis_exists(game_date, away_team, home_team):
                self.logger.info(f"Analysis already exists for {away_team} @ {home_team}")
                return self.repository.load_analysis(game_date, away_team, home_team)

        # Perform analysis
        analysis_result = self.analyze_game(
            game_date, away_team, home_team, prediction_data, result_data
        )

        # Save result
        self.save_analysis(analysis_result, game_date, away_team, home_team)

        return analysis_result

    def save_analysis(
        self,
        analysis_result: Dict[str, Any],
        game_date: str,
        away_team: str,
        home_team: str,
    ) -> str:
        """Save analysis result to file.

        Args:
            analysis_result: Analysis result dict
            game_date: Game date in YYYY-MM-DD format
            away_team: Away team abbreviation
            home_team: Home team abbreviation

        Returns:
            Path to saved file
        """
        success = self.repository.save_analysis(
            game_date, away_team.lower(), home_team.lower(), analysis_result
        )

        if success:
            self.logger.info(f"Saved analysis for {away_team} @ {home_team}")
        else:
            self.logger.error(f"Failed to save analysis for {away_team} @ {home_team}")

        return success

    def load_analysis(
        self,
        game_date: str,
        away_team: str,
        home_team: str,
    ) -> Optional[Dict[str, Any]]:
        """Load existing analysis for a game.

        Args:
            game_date: Game date in YYYY-MM-DD format
            away_team: Away team abbreviation
            home_team: Home team abbreviation

        Returns:
            Analysis result dict or None if not found
        """
        return self.repository.load_analysis(
            game_date, away_team.lower(), home_team.lower()
        )

    def analyze_games_batch(
        self,
        game_date: str,
        games: List[Dict[str, str]],
        prediction_loader: Callable[[str, Dict], Optional[Dict]],
        result_loader: Callable[[str, Dict], Optional[Dict]],
    ) -> Dict[str, Any]:
        """Analyze multiple games in batch.

        Args:
            game_date: Game date in YYYY-MM-DD format
            games: List of game dicts with 'away_team' and 'home_team'
            prediction_loader: Function to load prediction data
            result_loader: Function to load result data

        Returns:
            Batch summary with individual game results
        """
        self.logger.info(f"Starting batch analysis for {len(games)} games on {game_date}")

        results = []
        games_analyzed = 0
        games_skipped = 0
        total_profit = 0
        total_bets = 0
        total_won = 0

        for game in games:
            away_team = game.get("away_team", "")
            home_team = game.get("home_team", "")

            if not away_team or not home_team:
                self.logger.warning(f"Skipping game with missing team info: {game}")
                games_skipped += 1
                continue

            # Load prediction and result data
            prediction_data = prediction_loader(game_date, game)
            result_data = result_loader(game_date, game)

            if not prediction_data:
                self.logger.warning(f"No prediction found for {away_team} @ {home_team}")
                games_skipped += 1
                continue

            if not result_data:
                self.logger.warning(f"No results found for {away_team} @ {home_team}")
                games_skipped += 1
                continue

            # Analyze the game
            try:
                analysis = self.analyze_and_save(
                    game_date, away_team, home_team, prediction_data, result_data
                )
                results.append(analysis)
                games_analyzed += 1

                # Aggregate stats
                summary = analysis.get("summary", {})
                total_profit += summary.get("total_profit", 0)
                total_bets += summary.get("total_bets", 0)
                total_won += summary.get("bets_won", 0)

            except Exception as e:
                self.logger.error(f"Error analyzing {away_team} @ {home_team}: {e}")
                games_skipped += 1

        # Calculate overall stats
        win_rate = (total_won / total_bets * 100) if total_bets > 0 else 0
        total_staked = total_bets * self.config.profit_config.default_stake
        roi = (total_profit / total_staked * 100) if total_staked > 0 else 0

        batch_summary = {
            "success": games_analyzed > 0,
            "game_date": game_date,
            "games_analyzed": games_analyzed,
            "games_skipped": games_skipped,
            "total_games": len(games),
            "results": results,
            "aggregate_summary": {
                "total_bets": total_bets,
                "total_won": total_won,
                "total_lost": total_bets - total_won,
                "win_rate": round(win_rate, 1),
                "total_profit": round(total_profit, 2),
                "total_staked": total_staked,
                "roi_percent": round(roi, 1),
            },
        }

        self.logger.info(
            f"Batch analysis complete: {games_analyzed}/{len(games)} games, "
            f"ROI: {roi:.1f}%"
        )

        return batch_summary

    def get_analyses_for_date(self, game_date: str) -> List[Dict[str, Any]]:
        """Get all analyses for a specific date.

        Args:
            game_date: Game date in YYYY-MM-DD format

        Returns:
            List of analysis result dicts
        """
        return self.repository.list_analyses_for_date(game_date)

    def get_aggregate_stats(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate aggregate statistics across multiple analyses.

        Args:
            analyses: List of analysis result dicts

        Returns:
            Aggregate statistics dict
        """
        if not analyses:
            return {
                "total_games": 0,
                "total_bets": 0,
                "bets_won": 0,
                "bets_lost": 0,
                "win_rate": 0,
                "total_profit": 0,
                "total_staked": 0,
                "roi_percent": 0,
            }

        total_bets = 0
        bets_won = 0
        bets_lost = 0
        total_profit = 0

        for analysis in analyses:
            summary = analysis.get("summary", {})
            total_bets += summary.get("total_bets", 0)
            bets_won += summary.get("bets_won", 0)
            bets_lost += summary.get("bets_lost", 0)
            total_profit += summary.get("total_profit", 0)

        total_staked = total_bets * self.config.profit_config.default_stake
        win_rate = (bets_won / total_bets * 100) if total_bets > 0 else 0
        roi = (total_profit / total_staked * 100) if total_staked > 0 else 0

        return {
            "total_games": len(analyses),
            "total_bets": total_bets,
            "bets_won": bets_won,
            "bets_lost": bets_lost,
            "win_rate": round(win_rate, 1),
            "total_profit": round(total_profit, 2),
            "total_staked": total_staked,
            "roi_percent": round(roi, 1),
        }

    def format_analysis_markdown(self, analysis_result: Dict[str, Any]) -> str:
        """Format a single analysis as markdown.

        Args:
            analysis_result: Analysis result dict

        Returns:
            Markdown-formatted string
        """
        return self.bet_checker.format_results_markdown(analysis_result)

    def format_batch_summary_markdown(self, batch_result: Dict[str, Any]) -> str:
        """Format batch analysis summary as markdown.

        Args:
            batch_result: Batch analysis result dict

        Returns:
            Markdown-formatted string
        """
        agg = batch_result.get("aggregate_summary", {})
        game_date = batch_result.get("game_date", "Unknown")

        lines = [
            f"# Analysis Summary for {game_date}",
            "",
            f"**Games Analyzed**: {batch_result.get('games_analyzed', 0)}/{batch_result.get('total_games', 0)}",
            f"**Games Skipped**: {batch_result.get('games_skipped', 0)}",
            "",
            "## Aggregate Results",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Bets | {agg.get('total_bets', 0)} |",
            f"| Won | {agg.get('total_won', 0)} |",
            f"| Lost | {agg.get('total_lost', 0)} |",
            f"| Win Rate | {agg.get('win_rate', 0)}% |",
            f"| Total Staked | ${agg.get('total_staked', 0):.2f} |",
            f"| Total Profit | ${agg.get('total_profit', 0):.2f} |",
            f"| ROI | {agg.get('roi_percent', 0)}% |",
            "",
        ]

        # Add individual game summaries
        if batch_result.get("results"):
            lines.append("## Individual Games")
            lines.append("")

            for result in batch_result["results"]:
                matchup = result.get("matchup", "Unknown")
                summary = result.get("summary", {})
                profit = summary.get("total_profit", 0)
                profit_emoji = "🟢" if profit > 0 else "🔴" if profit < 0 else "⚪"

                lines.append(
                    f"- {profit_emoji} **{matchup}**: "
                    f"{summary.get('bets_won', 0)}/{summary.get('total_bets', 0)} won, "
                    f"${profit:.2f} profit"
                )

            lines.append("")

        return "\n".join(lines)
