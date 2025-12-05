"""Odds scraper for DraftKings.

Sport-agnostic scraper that extracts betting odds from DraftKings JSON API.
Uses the new pandas-based Scraper class.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from shared.scraping import Scraper
from shared.logging import get_logger
from shared.errors import OddsFetchError, OddsParseError
from shared.utils.timezone_utils import get_eastern_now

from services.odds.parser import DraftKingsParser
from services.odds.config import OddsServiceConfig


logger = get_logger("odds")


# Market type to prop name mapping
MARKET_NAME_MAP = {
    # NFL
    "Passing Yards Milestones": "passing_yards",
    "Passing Touchdowns Milestones": "passing_tds",
    "Pass Completions Milestones": "pass_completions",
    "Pass Attempts Milestones": "pass_attempts",
    "Rushing Yards Milestones": "rushing_yards",
    "Rushing Attempts Milestones": "rush_attempts",
    "Receiving Yards Milestones": "receiving_yards",
    "Receptions Milestones": "receptions",
    "Rushing + Receiving Yards Milestones": "rush_rec_yards",
    "Rushing and Receiving Yards Milestones": "rush_rec_yards",
    "Sacks Milestones": "sacks",
    "Tackles + Assists Milestones": "tackles_assists",
    "Interceptions Milestones": "interceptions",
    # NBA
    "Points Milestones": "points",
    "Rebounds Milestones": "rebounds",
    "Assists Milestones": "assists",
    "3-Pointers Made Milestones": "threes_made",
    "Pts + Reb Milestones": "pts_reb",
    "Pts + Ast Milestones": "pts_ast",
    "Reb + Ast Milestones": "reb_ast",
    "Pts + Reb + Ast Milestones": "pts_reb_ast",
}


class OddsScraper:
    """Scrapes betting odds from DraftKings JSON API.

    Uses constructor injection for all configuration.
    Sport-agnostic - works for NFL, NBA, and other sports.

    Example:
        config = OddsServiceConfig(
            included_markets=NFL_INCLUDED_MARKETS,
            excluded_markets=NFL_EXCLUDED_MARKETS,
        )
        scraper = OddsScraper(config=config, sport="nfl")

        # From API
        odds = scraper.fetch_odds_from_api(event_id)

        # From HTML file (legacy support)
        odds = scraper.extract_odds_from_file(html_path)
    """

    def __init__(
        self,
        config: OddsServiceConfig,
        sport: str,
        scraper: Scraper | None = None,
    ):
        """Initialize the odds scraper.

        Args:
            config: Odds service configuration
            sport: Sport name (nfl, nba)
            scraper: Optional Scraper instance (created if not provided)
        """
        self.config = config
        self.sport = sport.lower()
        self.parser = DraftKingsParser()
        self.scraper = scraper or Scraper(config.scraper_config)

    def fetch_odds_from_api(self, event_id: str) -> dict[str, Any]:
        """Fetch odds from DraftKings JSON API.

        Args:
            event_id: DraftKings event ID

        Returns:
            Dictionary with game info and odds

        Raises:
            OddsFetchError: If fetching fails
            OddsParseError: If parsing fails
        """
        api_url = f"https://sportsbook-nash.draftkings.com/api/sportscontent/dkusnj/v1/events/{event_id}/categories"
        logger.info(f"Fetching odds from API for event {event_id}")

        try:
            data = self.scraper.fetch_json(api_url)

            if not data:
                raise OddsFetchError(
                    "Empty response from DraftKings API",
                    context={"event_id": event_id, "url": api_url}
                )

            return self._extract_odds_from_api_data(data, event_id)

        except OddsParseError:
            raise
        except Exception as e:
            raise OddsFetchError(
                f"Failed to fetch odds from API: {e}",
                context={"event_id": event_id, "error": str(e)}
            )

    def fetch_odds_from_url(self, url: str) -> dict[str, Any]:
        """Fetch odds from a DraftKings event URL.

        Extracts event ID from URL and fetches from API.

        Args:
            url: DraftKings event URL (e.g., https://sportsbook.draftkings.com/event/...)

        Returns:
            Dictionary with game info and odds

        Raises:
            OddsFetchError: If URL parsing or fetching fails
        """
        import re

        # Extract event ID from URL
        # URL formats:
        # https://sportsbook.draftkings.com/event/nyg-dal/28937481
        # https://sportsbook.draftkings.com/event/28937481
        match = re.search(r'/event/(?:[^/]+/)?(\d+)', url)
        if not match:
            raise OddsFetchError(
                "Could not extract event ID from URL",
                context={"url": url}
            )

        event_id = match.group(1)
        return self.fetch_odds_from_api(event_id)

    def extract_odds_from_file(self, html_path: str | Path) -> dict[str, Any]:
        """Extract odds from a saved DraftKings HTML file.

        Legacy support for HTML files that contain embedded JSON data.

        Args:
            html_path: Path to the HTML file

        Returns:
            Dictionary with game info and odds

        Raises:
            OddsFetchError: If file not found
            OddsParseError: If parsing fails
        """
        html_path = Path(html_path)
        logger.info(f"Extracting odds from {html_path}")

        if not html_path.exists():
            raise OddsFetchError(
                f"HTML file not found: {html_path}",
                context={"path": str(html_path)}
            )

        html_content = html_path.read_text(encoding='utf-8')
        stadium_data = self.parser.extract_stadium_data(html_content)

        return self._extract_odds_from_data(stadium_data)

    def extract_odds_from_data(self, stadium_data: dict) -> dict[str, Any]:
        """Extract odds from stadium data dictionary.

        Public method for when you have the data already.

        Args:
            stadium_data: The stadiumEventData dictionary from DraftKings

        Returns:
            Dictionary with game info and odds
        """
        return self._extract_odds_from_data(stadium_data)

    def _extract_odds_from_api_data(self, api_data: dict, event_id: str) -> dict[str, Any]:
        """Extract odds from DraftKings API response.

        Args:
            api_data: API response data
            event_id: Event ID for context

        Returns:
            Dictionary with game info and odds
        """
        # API response has different structure than HTML stadiumEventData
        # Need to adapt parsing based on actual API response
        events = api_data.get("events", [])
        markets = api_data.get("markets", [])
        selections = api_data.get("selections", [])

        if not events:
            raise OddsParseError(
                "No event data found in API response",
                context={"event_id": event_id}
            )

        event = events[0]
        logger.info(f"Found {len(markets)} markets, {len(selections)} selections")

        result = {
            "sport": self.sport,
            "teams": self.parser.extract_teams(event),
            "game_date": event.get("startEventDate"),
            "fetched_at": get_eastern_now().isoformat(),
            "source": self.config.source,
            "game_lines": self._extract_game_lines(event_id, markets, selections),
            "player_props": self._extract_player_props(event_id, markets, selections),
        }

        logger.info(f"Extracted {len(result['game_lines'])} game lines")
        logger.info(f"Extracted {len(result['player_props'])} player prop markets")

        return result

    def _extract_odds_from_data(self, stadium_data: dict) -> dict[str, Any]:
        """Extract odds from stadiumEventData dict.

        Args:
            stadium_data: The stadiumEventData dictionary from DraftKings HTML

        Returns:
            Dictionary with game info and odds

        Raises:
            OddsParseError: If data extraction fails
        """
        events = stadium_data.get("events", [])
        markets = stadium_data.get("markets", [])
        selections = stadium_data.get("selections", [])

        if not events:
            raise OddsParseError("No event data found")

        event = events[0]
        event_id = event["id"]

        logger.info(f"Found {len(markets)} markets, {len(selections)} selections")

        result = {
            "sport": self.sport,
            "teams": self.parser.extract_teams(event),
            "game_date": event.get("startEventDate"),
            "fetched_at": get_eastern_now().isoformat(),
            "source": self.config.source,
            "game_lines": self._extract_game_lines(event_id, markets, selections),
            "player_props": self._extract_player_props(event_id, markets, selections),
        }

        logger.info(f"Extracted {len(result['game_lines'])} game lines")
        logger.info(f"Extracted {len(result['player_props'])} player prop markets")

        return result

    def _extract_game_lines(
        self,
        event_id: str,
        markets: list[dict],
        selections: list[dict]
    ) -> dict[str, Any]:
        """Extract moneyline, spread, and total game lines."""
        game_lines = {}

        for market in markets:
            if market.get("eventId") != event_id:
                continue

            market_type = market.get("marketType", {}).get("name")

            if market_type == "Moneyline":
                game_lines["moneyline"] = self.parser.parse_moneyline(market, selections)
            elif market_type == "Spread":
                game_lines["spread"] = self.parser.parse_spread(market, selections)
            elif market_type == "Total":
                game_lines["total"] = self.parser.parse_total(market, selections)

        return game_lines

    def _extract_player_props(
        self,
        event_id: str,
        markets: list[dict],
        selections: list[dict]
    ) -> list[dict]:
        """Extract player prop markets."""
        player_markets: dict[str, dict] = {}

        for market in markets:
            if market.get("eventId") != event_id:
                continue

            market_type = market.get("marketType", {}).get("name")

            # Skip excluded markets
            if market_type in self.config.excluded_markets:
                continue

            # Skip if not in included types
            if self.config.included_markets and market_type not in self.config.included_markets:
                continue

            # Handle different market types
            if market_type == "Anytime Touchdown Scorer":
                self._add_td_scorer_props(market, selections, player_markets)
            elif "Milestones" in str(market_type):
                self._add_milestone_prop(market, market_type, selections, player_markets)
            elif market_type in ("Double-Double", "Triple-Double"):
                self._add_special_prop(market, market_type, selections, player_markets)

        return list(player_markets.values())

    def _add_td_scorer_props(
        self,
        market: dict,
        all_selections: list[dict],
        player_markets: dict
    ):
        """Add touchdown scorer props to player_markets."""
        market_id = market["id"]
        market_selections = [s for s in all_selections if s.get("marketId") == market_id]

        for selection in market_selections:
            participants = selection.get("participants", [])
            if not participants or participants[0].get("type") != "Player":
                continue

            player_name = participants[0].get("name")
            venue_role = participants[0].get("venueRole", "")
            team = self.parser.parse_team_from_venue_role(venue_role)

            key = f"{player_name}_{team}"
            if key not in player_markets:
                player_markets[key] = {
                    "player": player_name,
                    "team": team,
                    "position": None,
                    "props": []
                }

            odds = self.parser.clean_odds(selection.get("displayOdds", {}).get("american"))
            player_markets[key]["props"].append({
                "market": "anytime_td",
                "odds": odds
            })

    def _add_milestone_prop(
        self,
        market: dict,
        market_type: str,
        all_selections: list[dict],
        player_markets: dict
    ):
        """Add milestone prop to player_markets."""
        market_id = market["id"]
        market_selections = [s for s in all_selections if s.get("marketId") == market_id]

        if not market_selections:
            return

        player_info = self.parser.extract_player_info(market_selections)
        if not player_info:
            return

        player_name = player_info["name"]
        team = player_info["team"]

        key = f"{player_name}_{team}"
        if key not in player_markets:
            player_markets[key] = {
                "player": player_name,
                "team": team,
                "position": None,
                "props": []
            }

        prop_name = MARKET_NAME_MAP.get(market_type)
        if not prop_name:
            return

        milestones = self.parser.parse_milestones(market, all_selections)
        if milestones:
            player_markets[key]["props"].append({
                "market": prop_name,
                "milestones": milestones
            })

    def _add_special_prop(
        self,
        market: dict,
        market_type: str,
        all_selections: list[dict],
        player_markets: dict
    ):
        """Add special props (double-double, triple-double) to player_markets."""
        market_id = market["id"]
        market_selections = [s for s in all_selections if s.get("marketId") == market_id]

        prop_name = market_type.lower().replace("-", "_")

        for selection in market_selections:
            participants = selection.get("participants", [])
            if not participants or participants[0].get("type") != "Player":
                continue

            player_name = participants[0].get("name")
            venue_role = participants[0].get("venueRole", "")
            team = self.parser.parse_team_from_venue_role(venue_role)

            key = f"{player_name}_{team}"
            if key not in player_markets:
                player_markets[key] = {
                    "player": player_name,
                    "team": team,
                    "position": None,
                    "props": []
                }

            odds = self.parser.clean_odds(selection.get("displayOdds", {}).get("american"))
            player_markets[key]["props"].append({
                "market": prop_name,
                "odds": odds
            })
