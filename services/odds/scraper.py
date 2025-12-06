"""Odds scraper for DraftKings.

Sport-agnostic scraper that extracts betting odds from DraftKings JSON API.
All sport-specific details (API URLs, market mappings) come from the config.
"""

from pathlib import Path
from typing import Any

from shared.scraping import Scraper
from shared.logging import get_logger
from shared.errors import OddsFetchError, OddsParseError
from shared.utils.timezone_utils import get_eastern_now

from services.odds.parser import DraftKingsParser
from services.odds.config import OddsServiceConfig


logger = get_logger("odds")


class OddsScraper:
    """Scrapes betting odds from DraftKings JSON API.

    This is a sport-agnostic black box. All sport-specific details
    (API URLs, market mappings) come from the config parameter.

    Example:
        from sports.nfl.nfl_config import get_nfl_odds_config

        config = get_nfl_odds_config()
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
            config: Odds service configuration (required)
            sport: Sport name (e.g., 'nfl', 'bundesliga')
            scraper: Optional Scraper instance (created if not provided)

        Raises:
            ValueError: If config is missing required fields
        """
        if not config.api_url_template:
            raise ValueError("OddsServiceConfig must provide api_url_template")

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
        api_url = self.config.api_url_template.format(event_id=event_id)
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

    def fetch_schedule(self) -> list[dict[str, Any]]:
        """Fetch upcoming games from league API.

        Returns:
            List of games with event_id, matchup, start_date

        Raises:
            OddsFetchError: If league_url not configured or fetch fails
        """
        if not self.config.league_url:
            raise OddsFetchError(
                "league_url not configured",
                context={"sport": self.sport}
            )

        logger.info(f"Fetching schedule from {self.config.league_url}")

        try:
            data = self.scraper.fetch_json(self.config.league_url)

            games = []
            for event in data.get("events", []):
                games.append({
                    "event_id": event.get("id"),
                    "matchup": event.get("name"),
                    "start_date": event.get("startEventDate"),
                })

            logger.info(f"Found {len(games)} upcoming games")
            return games

        except Exception as e:
            raise OddsFetchError(
                f"Failed to fetch schedule: {e}",
                context={"url": self.config.league_url, "error": str(e)}
            )

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
            "game_props": self._extract_game_props(event_id, markets, selections),
            "player_props": self._extract_player_props(event_id, markets, selections),
        }

        logger.info(f"Extracted {len(result['game_lines'])} game lines")
        logger.info(f"Extracted {len(result['game_props'])} game props")
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
            "game_props": self._extract_game_props(event_id, markets, selections),
            "player_props": self._extract_player_props(event_id, markets, selections),
        }

        logger.info(f"Extracted {len(result['game_lines'])} game lines")
        logger.info(f"Extracted {len(result['game_props'])} game props")
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

    def _extract_game_props(
        self,
        event_id: str,
        markets: list[dict],
        selections: list[dict]
    ) -> list[dict]:
        """Extract game-level prop markets (BTTS, corners, total goals, etc.)."""
        game_props = []

        for market in markets:
            if market.get("eventId") != event_id:
                continue

            market_type = market.get("marketType", {}).get("name")

            # Only process markets in game_prop_markets config
            if market_type not in self.config.game_prop_markets:
                continue

            market_id = market.get("id")
            market_name = market.get("name", market_type)
            market_selections = [s for s in selections if s.get("marketId") == market_id]

            # Get prop name from config mapping
            prop_name = self.config.market_name_map.get(
                market_type,
                market_type.lower().replace(" ", "_")
            )

            prop_data = {
                "market": prop_name,
                "market_name": market_name,  # Full name (e.g., "Stuttgart: Team Total Goals")
                "selections": []
            }

            for sel in market_selections:
                label = sel.get("label", "")
                points = sel.get("points")
                odds = self.parser.clean_odds(sel.get("displayOdds", {}).get("american"))

                prop_data["selections"].append({
                    "label": label,
                    "line": points,
                    "odds": odds
                })

            if prop_data["selections"]:
                game_props.append(prop_data)

        return game_props

    def _extract_player_props(
        self,
        event_id: str,
        markets: list[dict],
        selections: list[dict]
    ) -> list[dict]:
        """Extract player prop markets using config-driven parsing."""
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

            # Config-driven parsing based on market category
            if market_type in self.config.player_prop_markets:
                self._add_player_prop(market, market_type, selections, player_markets)
            elif market_type in self.config.milestone_markets:
                self._add_milestone_prop(market, market_type, selections, player_markets)

        return list(player_markets.values())

    def _add_player_prop(
        self,
        market: dict,
        market_type: str,
        all_selections: list[dict],
        player_markets: dict
    ):
        """Add player prop (one player per selection) to player_markets.

        Used for markets like Anytime Goalscorer, Anytime TD, Double-Double, etc.
        Each selection represents one player with their odds.
        """
        market_id = market["id"]
        market_selections = [s for s in all_selections if s.get("marketId") == market_id]

        # Get prop name from config mapping, fallback to slugified market type
        prop_name = self.config.market_name_map.get(
            market_type,
            market_type.lower().replace(" ", "_").replace("-", "_")
        )

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

        prop_name = self.config.market_name_map.get(market_type)
        if not prop_name:
            return

        milestones = self.parser.parse_milestones(market, all_selections)
        if milestones:
            player_markets[key]["props"].append({
                "market": prop_name,
                "milestones": milestones
            })

