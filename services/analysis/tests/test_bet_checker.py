"""Unit tests for BetChecker component."""

import pytest

from services.analysis import BetChecker, MatchingConfig, ProfitConfig


class TestBetCheckerInit:
    """Tests for BetChecker initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default configuration."""
        checker = BetChecker()

        assert checker.matching_config is not None
        assert checker.profit_config is not None
        assert checker.matching_config.name_similarity_threshold == 0.85
        assert checker.profit_config.default_stake == 100.0

    def test_init_with_custom_config(self, matching_config, profit_config):
        """Test initialization with custom configuration."""
        checker = BetChecker(
            matching_config=matching_config,
            profit_config=profit_config,
        )

        assert checker.matching_config == matching_config
        assert checker.profit_config == profit_config


class TestBetCheckerNormalize:
    """Tests for bet normalization."""

    def test_normalize_ev_format(self):
        """Test that EV format bets are preserved."""
        checker = BetChecker()

        bet = {
            "market": "passing_yards",
            "player": "Dak Prescott",
            "line": 275.0,
            "side": "over",
            "odds": -110,
        }

        normalized = checker.normalize_bet(bet)

        assert normalized["market"] == "passing_yards"
        assert normalized["player"] == "Dak Prescott"

    def test_normalize_ai_format_player_prop(self):
        """Test normalizing AI format player prop."""
        checker = BetChecker()

        bet = {"bet": "Dak Prescott Over 275 Passing Yards", "odds": -110}

        normalized = checker.normalize_bet(bet)

        assert normalized["player"] == "Dak Prescott"
        assert normalized["line"] == 275.0
        assert normalized["side"] == "over"
        assert normalized["market"] == "passing_yards"
        assert normalized["bet_type"] == "player_prop"

    def test_normalize_ai_format_spread(self):
        """Test normalizing AI format spread bet."""
        checker = BetChecker()

        bet = {"bet": "Cowboys -3.5", "odds": -110}

        normalized = checker.normalize_bet(bet)

        assert normalized["team"] == "Cowboys"
        assert normalized["line"] == -3.5
        assert normalized["bet_type"] == "spread"

    def test_normalize_ai_format_total(self):
        """Test normalizing AI format total bet."""
        checker = BetChecker()

        bet = {"bet": "Over 44.5 Total Points", "odds": -110}

        normalized = checker.normalize_bet(bet)

        assert normalized["line"] == 44.5
        assert normalized["side"] == "over"
        assert normalized["bet_type"] == "total"

    def test_normalize_anytime_td(self):
        """Test normalizing anytime TD bet."""
        checker = BetChecker()

        bet = {"bet": "CeeDee Lamb Anytime TD", "odds": -120}

        normalized = checker.normalize_bet(bet)

        assert normalized["player"] == "CeeDee Lamb"
        assert normalized["market"] == "anytime_td"
        assert normalized["bet_type"] == "player_prop"


class TestBetCheckerCheckBets:
    """Tests for checking bets against results."""

    def test_check_all_bets_winning(self, sample_prediction_data, sample_result_data):
        """Test checking bets that win."""
        checker = BetChecker()

        result = checker.check_all_bets(sample_prediction_data, sample_result_data)

        assert "bet_results" in result
        assert "summary" in result

        # Both bets should win (Prescott 289 > 275, Lamb 112 > 85.5)
        summary = result["summary"]
        assert summary["total_bets"] == 2
        assert summary["bets_won"] == 2
        assert summary["bets_lost"] == 0
        assert summary["win_rate"] == 100.0
        assert summary["total_profit"] > 0

    def test_check_all_bets_losing(self, sample_prediction_data, sample_result_data_losing):
        """Test checking bets that lose."""
        checker = BetChecker()

        result = checker.check_all_bets(sample_prediction_data, sample_result_data_losing)

        summary = result["summary"]
        assert summary["bets_lost"] == 2
        assert summary["bets_won"] == 0
        assert summary["total_profit"] < 0

    def test_check_single_bet_winning(self, sample_result_data):
        """Test checking a single winning bet."""
        checker = BetChecker()

        bet = {
            "market": "passing_yards",
            "player": "Dak Prescott",
            "line": 275.0,
            "side": "over",
            "odds": -110,
            "description": "Dak Prescott Over 275 Pass Yds",
        }

        result = checker.check_single_bet(bet, sample_result_data)

        assert result["won"] is True
        assert result["actual"] == 289
        assert result["profit"] > 0

    def test_check_single_bet_losing(self, sample_result_data_losing):
        """Test checking a single losing bet."""
        checker = BetChecker()

        bet = {
            "market": "passing_yards",
            "player": "Dak Prescott",
            "line": 275.0,
            "side": "over",
            "odds": -110,
            "description": "Dak Prescott Over 275 Pass Yds",
        }

        result = checker.check_single_bet(bet, sample_result_data_losing)

        assert result["won"] is False
        assert result["actual"] == 210
        assert result["profit"] < 0

    def test_check_spread_bet_winning(self, sample_result_data):
        """Test checking a winning spread bet."""
        checker = BetChecker()

        bet = {
            "bet": "Cowboys -3.5",
            "odds": -110,
        }

        result = checker.check_single_bet(bet, sample_result_data)

        # Cowboys won 27-20 (margin = 7, covers -3.5)
        assert result["won"] is True
        assert result["profit"] > 0

    def test_check_spread_bet_losing(self, sample_result_data_losing):
        """Test checking a losing spread bet."""
        checker = BetChecker()

        bet = {
            "bet": "Cowboys -3.5",
            "odds": -110,
        }

        result = checker.check_single_bet(bet, sample_result_data_losing)

        # Cowboys lost 17-24
        assert result["won"] is False
        assert result["profit"] < 0


class TestBetCheckerPlayerMatching:
    """Tests for player name matching."""

    def test_find_player_exact_match(self, sample_result_data):
        """Test finding player with exact name match."""
        checker = BetChecker()

        table_data = sample_result_data["tables"]["passing"]["data"]
        result = checker.find_player("Dak Prescott", table_data)

        assert result is not None
        assert result["player"] == "Dak Prescott"
        assert result["pass_yds"] == 289

    def test_find_player_fuzzy_match(self, sample_result_data):
        """Test finding player with fuzzy matching."""
        checker = BetChecker()

        table_data = sample_result_data["tables"]["receiving"]["data"]
        # Slight variation in name
        result = checker.find_player("CeeDee Lamb", table_data)

        assert result is not None
        assert "Lamb" in result["player"]

    def test_find_player_not_found(self, sample_result_data):
        """Test when player is not found."""
        checker = BetChecker()

        table_data = sample_result_data["tables"]["passing"]["data"]
        result = checker.find_player("Nonexistent Player", table_data)

        assert result is None

    def test_calculate_name_similarity(self):
        """Test name similarity calculation."""
        checker = BetChecker()

        # Exact match
        similarity = checker.calculate_name_similarity("Dak Prescott", "Dak Prescott")
        assert similarity == 1.0

        # Close match
        similarity = checker.calculate_name_similarity("Dak Prescott", "D. Prescott")
        assert similarity > 0.7

        # Different names
        similarity = checker.calculate_name_similarity("Dak Prescott", "Tom Brady")
        assert similarity < 0.5


class TestBetCheckerProfit:
    """Tests for profit calculations."""

    def test_calculate_profit_win_negative_odds(self):
        """Test profit calculation for winning bet with negative odds."""
        checker = BetChecker()

        profit = checker.calculate_profit(won=True, odds=-110)

        # Win at -110 returns $90.91 on $100 stake
        assert abs(profit - 90.91) < 0.01

    def test_calculate_profit_win_positive_odds(self):
        """Test profit calculation for winning bet with positive odds."""
        checker = BetChecker()

        profit = checker.calculate_profit(won=True, odds=150)

        # Win at +150 returns $150 on $100 stake
        assert profit == 150.0

    def test_calculate_profit_loss(self):
        """Test profit calculation for losing bet."""
        checker = BetChecker()

        profit = checker.calculate_profit(won=False, odds=-110)

        # Loss always returns -stake
        assert profit == -100.0

    def test_calculate_profit_push(self):
        """Test profit calculation for push."""
        checker = BetChecker()

        profit = checker.calculate_profit(won=None, odds=-110)

        # Push returns 0
        assert profit == 0.0

    def test_calculate_profit_custom_stake(self):
        """Test profit calculation with custom stake."""
        checker = BetChecker()

        profit = checker.calculate_profit(won=True, odds=-110, stake=50.0)

        # Win at -110 returns $45.45 on $50 stake
        assert abs(profit - 45.45) < 0.01


class TestBetCheckerFormatting:
    """Tests for result formatting."""

    def test_format_results_markdown(self, sample_prediction_data, sample_result_data):
        """Test markdown formatting of results."""
        checker = BetChecker()

        result = checker.check_all_bets(sample_prediction_data, sample_result_data)
        markdown = checker.format_results_markdown(result)

        assert "# Bet Analysis Results" in markdown
        assert "## Summary" in markdown
        assert "Total Bets" in markdown
        assert "Win Rate" in markdown
        assert "ROI" in markdown
        assert "## Bet Details" in markdown

    def test_format_results_markdown_empty(self):
        """Test markdown formatting with no bets."""
        checker = BetChecker()

        result = {"bet_results": [], "summary": {"total_bets": 0}}
        markdown = checker.format_results_markdown(result)

        assert "# Bet Analysis Results" in markdown
        assert "Total Bets**: 0" in markdown
