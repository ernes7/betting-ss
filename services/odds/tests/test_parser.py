"""Unit tests for DraftKings parser."""

import pytest

from services.odds.parser import DraftKingsParser
from shared.errors import OddsParseError


class TestDraftKingsParser:
    """Tests for DraftKingsParser class."""

    def test_clean_odds_positive(self, parser):
        """Test cleaning positive odds."""
        assert parser.clean_odds("+150") == 150
        assert parser.clean_odds("+340") == 340

    def test_clean_odds_negative(self, parser):
        """Test cleaning negative odds with ASCII minus."""
        assert parser.clean_odds("-110") == -110
        assert parser.clean_odds("-200") == -200

    def test_clean_odds_unicode_minus(self, parser):
        """Test cleaning negative odds with Unicode minus (\\u2212)."""
        assert parser.clean_odds("\u2212110") == -110
        assert parser.clean_odds("\u2212200") == -200

    def test_clean_odds_none(self, parser):
        """Test cleaning None returns None."""
        assert parser.clean_odds(None) is None

    def test_clean_odds_empty_string(self, parser):
        """Test cleaning empty string returns None."""
        assert parser.clean_odds("") is None

    def test_clean_odds_invalid(self, parser):
        """Test cleaning invalid string returns None."""
        assert parser.clean_odds("not a number") is None
        assert parser.clean_odds("abc") is None

    def test_parse_team_from_venue_role_home(self, parser):
        """Test parsing home team from venue role."""
        assert parser.parse_team_from_venue_role("Home") == "HOME"
        assert parser.parse_team_from_venue_role("HomePlayer") == "HOME"
        assert parser.parse_team_from_venue_role("HomeTeam") == "HOME"

    def test_parse_team_from_venue_role_away(self, parser):
        """Test parsing away team from venue role."""
        assert parser.parse_team_from_venue_role("Away") == "AWAY"
        assert parser.parse_team_from_venue_role("AwayPlayer") == "AWAY"
        assert parser.parse_team_from_venue_role("AwayTeam") == "AWAY"

    def test_parse_team_from_venue_role_unknown(self, parser):
        """Test parsing unknown venue role returns None."""
        assert parser.parse_team_from_venue_role("Unknown") is None
        assert parser.parse_team_from_venue_role("") is None

    def test_extract_teams(self, parser, sample_stadium_data):
        """Test extracting teams from event data."""
        event = sample_stadium_data["events"][0]
        teams = parser.extract_teams(event)

        assert teams["home"]["name"] == "Dallas Cowboys"
        assert teams["home"]["abbr"] == "DAL"
        assert teams["away"]["name"] == "New York Giants"
        assert teams["away"]["abbr"] == "NYG"

    def test_parse_moneyline(self, parser, sample_stadium_data):
        """Test parsing moneyline market."""
        markets = sample_stadium_data["markets"]
        selections = sample_stadium_data["selections"]

        ml_market = next(m for m in markets if m["marketType"]["name"] == "Moneyline")
        result = parser.parse_moneyline(ml_market, selections)

        assert result["home"] == -150
        assert result["away"] == 130

    def test_parse_spread(self, parser, sample_stadium_data):
        """Test parsing spread market."""
        markets = sample_stadium_data["markets"]
        selections = sample_stadium_data["selections"]

        spread_market = next(m for m in markets if m["marketType"]["name"] == "Spread")
        result = parser.parse_spread(spread_market, selections)

        assert result["home"] == -3.5
        assert result["home_odds"] == -110
        assert result["away"] == 3.5
        assert result["away_odds"] == -110

    def test_parse_total(self, parser, sample_stadium_data):
        """Test parsing total market."""
        markets = sample_stadium_data["markets"]
        selections = sample_stadium_data["selections"]

        total_market = next(m for m in markets if m["marketType"]["name"] == "Total")
        result = parser.parse_total(total_market, selections)

        assert result["line"] == 47.5
        assert result["over"] == -110
        assert result["under"] == -110

    def test_parse_milestones(self, parser, sample_stadium_data):
        """Test parsing milestone selections."""
        markets = sample_stadium_data["markets"]
        selections = sample_stadium_data["selections"]

        passing_market = next(m for m in markets if "Passing Yards" in m["name"])
        milestones = parser.parse_milestones(passing_market, selections)

        assert len(milestones) == 3
        assert milestones[0] == {"line": 250, "odds": -200}
        assert milestones[1] == {"line": 275, "odds": -110}
        assert milestones[2] == {"line": 300, "odds": 150}

    def test_milestones_sorted_by_line(self, parser):
        """Test that milestones are sorted by line value."""
        market = {"id": "test_market"}
        selections = [
            {"marketId": "test_market", "milestoneValue": 300, "displayOdds": {"american": "+150"}},
            {"marketId": "test_market", "milestoneValue": 250, "displayOdds": {"american": "-200"}},
            {"marketId": "test_market", "milestoneValue": 275, "displayOdds": {"american": "-110"}},
        ]

        milestones = parser.parse_milestones(market, selections)

        assert milestones[0]["line"] == 250
        assert milestones[1]["line"] == 275
        assert milestones[2]["line"] == 300

    def test_extract_player_info(self, parser, sample_stadium_data):
        """Test extracting player info from selections."""
        passing_selections = [
            s for s in sample_stadium_data["selections"]
            if s.get("marketId") == "market_passing"
        ]

        player_info = parser.extract_player_info(passing_selections)

        assert player_info["name"] == "Dak Prescott"
        assert player_info["team"] == "HOME"

    def test_extract_player_info_no_selections(self, parser):
        """Test extracting player info from empty selections."""
        assert parser.extract_player_info([]) is None

    def test_extract_stadium_data_missing_initial_state(self, parser):
        """Test extracting stadium data when __INITIAL_STATE__ is missing."""
        html = "<html><body>No data</body></html>"

        with pytest.raises(OddsParseError) as exc_info:
            parser.extract_stadium_data(html)

        assert "Could not find window.__INITIAL_STATE__" in str(exc_info.value)

    def test_extract_stadium_data_invalid_json(self, parser):
        """Test extracting stadium data with invalid JSON."""
        html = "<script>window.__INITIAL_STATE__ = {invalid json};</script>"

        with pytest.raises(OddsParseError) as exc_info:
            parser.extract_stadium_data(html)

        assert "Failed to parse JavaScript JSON" in str(exc_info.value)

    def test_extract_stadium_data_missing_stadium_data(self, parser):
        """Test extracting stadium data when stadiumEventData is missing."""
        html = '<script>window.__INITIAL_STATE__ = {"other": "data"};</script>'

        with pytest.raises(OddsParseError) as exc_info:
            parser.extract_stadium_data(html)

        assert "stadiumEventData not found" in str(exc_info.value)


class TestCleanOddsEdgeCases:
    """Edge case tests for clean_odds function."""

    def test_even_odds(self, parser):
        """Test even odds (100 or -100)."""
        assert parser.clean_odds("+100") == 100
        assert parser.clean_odds("-100") == -100

    def test_large_odds(self, parser):
        """Test very large odds."""
        assert parser.clean_odds("+10000") == 10000
        assert parser.clean_odds("-10000") == -10000

    def test_odds_with_whitespace(self, parser):
        """Test odds with whitespace - Python int() handles this."""
        # Python's int() actually handles leading/trailing whitespace
        assert parser.clean_odds(" -110") == -110
        assert parser.clean_odds("-110 ") == -110
        assert parser.clean_odds(" +150 ") == 150
