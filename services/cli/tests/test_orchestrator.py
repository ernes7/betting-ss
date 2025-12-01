"""Unit tests for CLIOrchestrator."""

import pytest
from unittest.mock import MagicMock, patch

from services.cli import CLIOrchestrator, CLIServiceConfig, WorkflowConfig


class TestCLIOrchestratorInit:
    """Tests for CLIOrchestrator initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default configuration."""
        orchestrator = CLIOrchestrator(sport="nfl")

        assert orchestrator.sport == "nfl"
        assert orchestrator.config is not None

    def test_init_normalizes_sport(self):
        """Test that sport is normalized to lowercase."""
        orchestrator = CLIOrchestrator(sport="NFL")

        assert orchestrator.sport == "nfl"

    def test_init_with_custom_config(self, test_cli_config):
        """Test initialization with custom configuration."""
        orchestrator = CLIOrchestrator(
            sport="nfl",
            config=test_cli_config,
        )

        assert orchestrator.config == test_cli_config


class TestCLIOrchestratorLazyLoading:
    """Tests for lazy service loading."""

    def test_services_not_loaded_on_init(self):
        """Test that services are not loaded during initialization."""
        orchestrator = CLIOrchestrator(sport="nfl")

        assert orchestrator._odds_service is None
        assert orchestrator._results_service is None
        assert orchestrator._analysis_service is None


class TestCLIOrchestratorFetchResults:
    """Tests for fetch_results_workflow."""

    def test_fetch_results_empty_games(self, test_cli_config):
        """Test fetching results with empty games list."""
        orchestrator = CLIOrchestrator(
            sport="nfl",
            config=test_cli_config,
        )

        result = orchestrator.fetch_results_workflow(
            game_date="2024-11-24",
            games=[],
        )

        assert result["success"] is True
        assert result["games_processed"] == 0

    def test_fetch_results_skips_existing(self, test_cli_config, sample_games):
        """Test that existing results are skipped."""
        mock_results_service = MagicMock()
        mock_results_service.load_result.return_value = {"exists": True}

        orchestrator = CLIOrchestrator(
            sport="nfl",
            config=test_cli_config,
        )
        orchestrator._results_service = mock_results_service

        result = orchestrator.fetch_results_workflow(
            game_date="2024-11-24",
            games=sample_games,
        )

        assert result["games_skipped"] == 2
        assert result["games_processed"] == 0

    def test_fetch_results_processes_new(self, test_cli_config, sample_games):
        """Test fetching new results."""
        mock_results_service = MagicMock()
        mock_results_service.load_result.return_value = None
        mock_results_service.fetch_game_result.return_value = {"score": "27-20"}

        orchestrator = CLIOrchestrator(
            sport="nfl",
            config=test_cli_config,
        )
        orchestrator._results_service = mock_results_service

        result = orchestrator.fetch_results_workflow(
            game_date="2024-11-24",
            games=sample_games,
        )

        assert result["games_processed"] == 2
        assert result["games_skipped"] == 0

    def test_fetch_results_handles_errors(self, test_cli_config, sample_games):
        """Test error handling during fetch."""
        mock_results_service = MagicMock()
        mock_results_service.load_result.return_value = None
        mock_results_service.fetch_game_result.side_effect = Exception("Network error")

        orchestrator = CLIOrchestrator(
            sport="nfl",
            config=test_cli_config,
        )
        orchestrator._results_service = mock_results_service

        result = orchestrator.fetch_results_workflow(
            game_date="2024-11-24",
            games=sample_games,
        )

        assert result["games_failed"] == 2
        assert result["success"] is False

    def test_fetch_results_with_progress_callback(self, test_cli_config, sample_games):
        """Test progress callback is called."""
        mock_results_service = MagicMock()
        mock_results_service.load_result.return_value = None
        mock_results_service.fetch_game_result.return_value = {"score": "27-20"}

        progress_calls = []

        def track_progress(msg, current, total):
            progress_calls.append((msg, current, total))

        orchestrator = CLIOrchestrator(
            sport="nfl",
            config=test_cli_config,
        )
        orchestrator._results_service = mock_results_service

        orchestrator.fetch_results_workflow(
            game_date="2024-11-24",
            games=sample_games,
            progress_callback=track_progress,
        )

        assert len(progress_calls) == 2
        assert progress_calls[0][1] == 1
        assert progress_calls[1][1] == 2


class TestCLIOrchestratorAnalyze:
    """Tests for analyze_workflow."""

    def test_analyze_calls_analysis_service(self, test_cli_config, sample_games):
        """Test that analyze workflow calls analysis service."""
        mock_analysis_service = MagicMock()
        mock_analysis_service.analyze_games_batch.return_value = {
            "success": True,
            "games_analyzed": 2,
        }

        orchestrator = CLIOrchestrator(
            sport="nfl",
            config=test_cli_config,
        )
        orchestrator._analysis_service = mock_analysis_service

        result = orchestrator.analyze_workflow(
            game_date="2024-11-24",
            games=sample_games,
            prediction_loader=lambda d, g: None,
            result_loader=lambda d, g: None,
        )

        mock_analysis_service.analyze_games_batch.assert_called_once()
        assert result["success"] is True


class TestCLIOrchestratorFullPipeline:
    """Tests for full_pipeline_workflow."""

    def test_full_pipeline_runs_all_stages(self, test_cli_config, sample_games):
        """Test that full pipeline runs all stages."""
        mock_odds_service = MagicMock()
        mock_results_service = MagicMock()
        mock_analysis_service = MagicMock()

        mock_results_service.load_result.return_value = None
        mock_results_service.fetch_game_result.return_value = {"score": "27-20"}
        mock_analysis_service.analyze_games_batch.return_value = {"success": True}

        orchestrator = CLIOrchestrator(
            sport="nfl",
            config=test_cli_config,
        )
        orchestrator._odds_service = mock_odds_service
        orchestrator._results_service = mock_results_service
        orchestrator._analysis_service = mock_analysis_service

        result = orchestrator.full_pipeline_workflow(
            game_date="2024-11-24",
            games=sample_games,
            fetch_odds=True,
            generate_predictions=True,
            fetch_results=True,
            run_analysis=True,
        )

        assert "stages" in result
        assert "odds" in result["stages"]
        assert "predictions" in result["stages"]
        assert "results" in result["stages"]
        assert "analysis" in result["stages"]

    def test_full_pipeline_skips_disabled_stages(self, test_cli_config, sample_games):
        """Test that disabled stages are skipped."""
        mock_results_service = MagicMock()
        mock_results_service.load_result.return_value = None
        mock_results_service.fetch_game_result.return_value = {"score": "27-20"}

        orchestrator = CLIOrchestrator(
            sport="nfl",
            config=test_cli_config,
        )
        orchestrator._results_service = mock_results_service

        result = orchestrator.full_pipeline_workflow(
            game_date="2024-11-24",
            games=sample_games,
            fetch_odds=False,
            generate_predictions=False,
            fetch_results=True,
            run_analysis=False,
        )

        assert "odds" not in result["stages"]
        assert "predictions" not in result["stages"]
        assert "results" in result["stages"]
        assert "analysis" not in result["stages"]


class TestCLIOrchestratorSummary:
    """Tests for workflow summary generation."""

    def test_get_workflow_summary_single(self, sample_workflow_result):
        """Test summary for single workflow result."""
        orchestrator = CLIOrchestrator(sport="nfl")

        summary = orchestrator.get_workflow_summary(sample_workflow_result)

        assert "2024-11-24" in summary
        assert "Processed: 2" in summary

    def test_get_workflow_summary_pipeline(self):
        """Test summary for full pipeline result."""
        orchestrator = CLIOrchestrator(sport="nfl")

        pipeline_result = {
            "success": True,
            "game_date": "2024-11-24",
            "stages": {
                "odds": {"success": True, "games_processed": 2},
                "results": {"success": True, "games_processed": 2},
                "analysis": {"success": True},
            },
        }

        summary = orchestrator.get_workflow_summary(pipeline_result)

        assert "ODDS" in summary
        assert "RESULTS" in summary
        assert "ANALYSIS" in summary
