"""Unit tests for ResultsParser."""

import pytest

from services.results.parser import ResultsParser
from shared.errors import ResultsParseError


class TestParseFinalScore:
    """Tests for parse_final_score method."""

    def test_parse_final_score_success(self, parser, sample_scoring_data):
        """Test parsing final score from valid scoring data."""
        result = parser.parse_final_score(sample_scoring_data)

        assert result["away"] == 24
        assert result["home"] == 21

    def test_parse_final_score_no_data(self, parser):
        """Test parsing final score with no data raises error."""
        with pytest.raises(ResultsParseError) as exc_info:
            parser.parse_final_score({})

        assert "no data" in str(exc_info.value).lower()

    def test_parse_final_score_empty_data(self, parser):
        """Test parsing final score with empty data list raises error."""
        with pytest.raises(ResultsParseError) as exc_info:
            parser.parse_final_score({"data": []})

        # Empty list is caught by the "no data" check
        assert "no data" in str(exc_info.value).lower()

    def test_parse_final_score_missing_columns(self, parser):
        """Test parsing final score with missing score columns."""
        data = {
            "data": [
                {"quarter": "4", "team": "Cowboys", "detail": "End"}
            ]
        }

        with pytest.raises(ResultsParseError) as exc_info:
            parser.parse_final_score(data)

        assert "Could not parse final scores" in str(exc_info.value)

    def test_parse_final_score_invalid_values(self, parser):
        """Test parsing final score with non-numeric values."""
        data = {
            "data": [
                {"vis_team_score": "N/A", "home_team_score": "N/A"}
            ]
        }

        with pytest.raises(ResultsParseError):
            parser.parse_final_score(data)


class TestParseTeamNames:
    """Tests for parse_team_names method."""

    def test_parse_team_names_success(self, parser, sample_scoring_data):
        """Test parsing team names from scoring data."""
        result = parser.parse_team_names(sample_scoring_data)

        assert result["away"] == "Giants"
        assert result["home"] == "Cowboys"

    def test_parse_team_names_no_data(self, parser):
        """Test parsing team names with no data returns None."""
        result = parser.parse_team_names({})

        assert result["away"] is None
        assert result["home"] is None

    def test_parse_team_names_first_play_home(self, parser):
        """Test parsing when first scoring play is home team."""
        data = {
            "data": [
                {
                    "team": "Cowboys",
                    "vis_team_score": "0",
                    "home_team_score": "7",
                },
                {
                    "team": "Giants",
                    "vis_team_score": "3",
                    "home_team_score": "7",
                },
            ]
        }

        result = parser.parse_team_names(data)

        assert result["home"] == "Cowboys"
        assert result["away"] == "Giants"


class TestDetermineWinner:
    """Tests for determine_winner method."""

    def test_determine_winner_away_wins(self, parser):
        """Test determining winner when away team wins."""
        final_score = {"away": 28, "home": 21}
        teams = {"away": "Giants", "home": "Cowboys"}

        result = parser.determine_winner(final_score, teams)

        assert result == "Giants"

    def test_determine_winner_home_wins(self, parser):
        """Test determining winner when home team wins."""
        final_score = {"away": 21, "home": 28}
        teams = {"away": "Giants", "home": "Cowboys"}

        result = parser.determine_winner(final_score, teams)

        assert result == "Cowboys"

    def test_determine_winner_tie(self, parser):
        """Test determining winner when game is tied."""
        final_score = {"away": 21, "home": 21}
        teams = {"away": "Giants", "home": "Cowboys"}

        result = parser.determine_winner(final_score, teams)

        assert result == "TIE"

    def test_determine_winner_missing_team_name(self, parser):
        """Test determining winner with missing team names."""
        final_score = {"away": 28, "home": 21}
        teams = {"away": None, "home": None}

        result = parser.determine_winner(final_score, teams)

        assert result == "AWAY"


class TestSplitPlayerOffense:
    """Tests for split_player_offense method."""

    def test_split_player_offense_all_categories(self, parser, sample_player_offense_data):
        """Test splitting player offense into all categories."""
        result = parser.split_player_offense(sample_player_offense_data)

        assert result["passing"] is not None
        assert result["rushing"] is not None
        assert result["receiving"] is not None

    def test_split_player_offense_passing_players(self, parser, sample_player_offense_data):
        """Test that passing table contains only passers."""
        result = parser.split_player_offense(sample_player_offense_data)

        passing_players = [p["player"] for p in result["passing"]["data"]]

        # Only Dak Prescott has passing stats
        assert "Dak Prescott" in passing_players
        assert len(passing_players) == 1

    def test_split_player_offense_rushing_players(self, parser, sample_player_offense_data):
        """Test that rushing table contains only rushers."""
        result = parser.split_player_offense(sample_player_offense_data)

        rushing_players = [p["player"] for p in result["rushing"]["data"]]

        # Prescott and Pollard have rushing stats
        assert "Dak Prescott" in rushing_players
        assert "Tony Pollard" in rushing_players
        assert len(rushing_players) == 2

    def test_split_player_offense_receiving_players(self, parser, sample_player_offense_data):
        """Test that receiving table contains only receivers."""
        result = parser.split_player_offense(sample_player_offense_data)

        receiving_players = [p["player"] for p in result["receiving"]["data"]]

        # Pollard and Lamb have receiving stats
        assert "Tony Pollard" in receiving_players
        assert "CeeDee Lamb" in receiving_players
        assert len(receiving_players) == 2

    def test_split_player_offense_empty_data(self, parser):
        """Test splitting empty player offense data."""
        result = parser.split_player_offense({})

        assert result["passing"] is None
        assert result["rushing"] is None
        assert result["receiving"] is None

    def test_split_player_offense_no_players(self, parser):
        """Test splitting player offense with no players with stats."""
        data = {
            "data": [
                {
                    "player": "Bench Player",
                    "pass_cmp": "0",
                    "pass_att": "0",
                    "rush_att": "0",
                    "targets": "0",
                    "rec": "0",
                }
            ]
        }

        result = parser.split_player_offense(data)

        # All tables should be None since no players have stats
        assert result["passing"] is None
        assert result["rushing"] is None
        assert result["receiving"] is None


class TestExtractPlayerStats:
    """Tests for extract_player_stats method."""

    def test_extract_player_stats_from_tables(self, parser):
        """Test extracting player stats from tables."""
        tables = {
            "passing": {
                "data": [
                    {"player": "Dak Prescott", "pass_yds": "280"},
                ]
            }
        }

        result = parser.extract_player_stats(tables, "passing")

        assert len(result) == 1
        assert result[0]["player"] == "Dak Prescott"

    def test_extract_player_stats_missing_table(self, parser):
        """Test extracting from missing table returns empty list."""
        result = parser.extract_player_stats({}, "passing")

        assert result == []


class TestGetPlayerStat:
    """Tests for get_player_stat method."""

    def test_get_player_stat_found(self, parser):
        """Test getting a player stat that exists."""
        tables = {
            "passing": {
                "data": [
                    {"player": "Dak Prescott", "pass_yds": "280"},
                ]
            }
        }

        result = parser.get_player_stat(tables, "Dak Prescott", "pass_yds")

        assert result == "280"

    def test_get_player_stat_not_found(self, parser):
        """Test getting a player stat that doesn't exist."""
        tables = {
            "passing": {
                "data": [
                    {"player": "Dak Prescott", "pass_yds": "280"},
                ]
            }
        }

        result = parser.get_player_stat(tables, "Unknown Player", "pass_yds", default=0)

        assert result == 0

    def test_get_player_stat_partial_name_match(self, parser):
        """Test getting player stat with partial name match."""
        tables = {
            "passing": {
                "data": [
                    {"player": "Dak Prescott", "pass_yds": "280"},
                ]
            }
        }

        result = parser.get_player_stat(tables, "Prescott", "pass_yds")

        assert result == "280"


class TestSafeInt:
    """Tests for _safe_int helper method."""

    def test_safe_int_valid(self, parser):
        """Test safe int with valid values."""
        assert parser._safe_int("42") == 42
        assert parser._safe_int(42) == 42
        assert parser._safe_int("0") == 0

    def test_safe_int_invalid(self, parser):
        """Test safe int with invalid values returns 0."""
        assert parser._safe_int(None) == 0
        assert parser._safe_int("") == 0
        assert parser._safe_int("N/A") == 0
        assert parser._safe_int("abc") == 0
