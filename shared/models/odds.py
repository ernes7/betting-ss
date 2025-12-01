"""Odds dataclass model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class GameLines:
    """Game-level betting lines.

    Attributes:
        moneyline_home: Home team moneyline odds
        moneyline_away: Away team moneyline odds
        spread_home: Home team spread
        spread_home_odds: Home team spread odds
        spread_away: Away team spread
        spread_away_odds: Away team spread odds
        total: Over/under total
        over_odds: Over odds
        under_odds: Under odds
    """
    moneyline_home: int = 0
    moneyline_away: int = 0
    spread_home: float = 0.0
    spread_home_odds: int = -110
    spread_away: float = 0.0
    spread_away_odds: int = -110
    total: float = 0.0
    over_odds: int = -110
    under_odds: int = -110

    @classmethod
    def from_dict(cls, data: dict) -> "GameLines":
        """Create GameLines from dictionary."""
        moneyline = data.get("moneyline", {})
        spread = data.get("spread", {})
        total = data.get("total", {})

        return cls(
            moneyline_home=int(moneyline.get("home", 0)),
            moneyline_away=int(moneyline.get("away", 0)),
            spread_home=float(spread.get("home", spread.get("away", 0)) * -1 if spread.get("away") else 0),
            spread_home_odds=int(spread.get("home_odds", -110)),
            spread_away=float(spread.get("away", 0)),
            spread_away_odds=int(spread.get("away_odds", -110)),
            total=float(total.get("line", 0)),
            over_odds=int(total.get("over", -110)),
            under_odds=int(total.get("under", -110)),
        )

    def to_dict(self) -> dict:
        """Convert GameLines to dictionary."""
        return {
            "moneyline": {
                "home": self.moneyline_home,
                "away": self.moneyline_away,
            },
            "spread": {
                "home": self.spread_home,
                "home_odds": self.spread_home_odds,
                "away": self.spread_away,
                "away_odds": self.spread_away_odds,
            },
            "total": {
                "line": self.total,
                "over": self.over_odds,
                "under": self.under_odds,
            },
        }


@dataclass
class PlayerProp:
    """A single player prop.

    Attributes:
        player: Player name
        team: Team abbreviation
        market: Prop market (e.g., "passing_yards")
        line: The line value
        over_odds: Over odds
        under_odds: Under odds
        milestones: List of milestone thresholds with odds
    """
    player: str
    team: str
    market: str
    line: float = 0.0
    over_odds: int = -110
    under_odds: int = -110
    milestones: list = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "PlayerProp":
        """Create PlayerProp from dictionary."""
        return cls(
            player=data.get("player", ""),
            team=data.get("team", ""),
            market=data.get("market", data.get("prop_type", "")),
            line=float(data.get("line", 0)),
            over_odds=int(data.get("over_odds", data.get("over", -110))),
            under_odds=int(data.get("under_odds", data.get("under", -110))),
            milestones=data.get("milestones", []),
        )

    def to_dict(self) -> dict:
        """Convert PlayerProp to dictionary."""
        return {
            "player": self.player,
            "team": self.team,
            "market": self.market,
            "line": self.line,
            "over_odds": self.over_odds,
            "under_odds": self.under_odds,
            "milestones": self.milestones,
        }


@dataclass
class Odds:
    """Complete odds for a game.

    Attributes:
        sport: Sport name
        home_team: Home team name/abbreviation
        away_team: Away team name/abbreviation
        game_date: Game date and time
        game_lines: Game-level betting lines
        player_props: List of player props
        source: Odds source (e.g., "draftkings")
        fetched_at: When odds were fetched
    """
    sport: str
    home_team: str
    away_team: str
    game_date: datetime
    game_lines: GameLines = field(default_factory=GameLines)
    player_props: list[PlayerProp] = field(default_factory=list)
    source: str = "draftkings"
    fetched_at: Optional[datetime] = None

    @property
    def game_date_str(self) -> str:
        """Get game date as YYYY-MM-DD string."""
        return self.game_date.strftime("%Y-%m-%d")

    @property
    def matchup(self) -> str:
        """Get matchup string."""
        return f"{self.away_team} @ {self.home_team}"

    def get_props_by_market(self, market: str) -> list[PlayerProp]:
        """Get all player props for a specific market."""
        return [p for p in self.player_props if p.market == market]

    def get_props_by_player(self, player: str) -> list[PlayerProp]:
        """Get all props for a specific player."""
        return [p for p in self.player_props if player.lower() in p.player.lower()]

    @classmethod
    def from_dict(cls, data: dict) -> "Odds":
        """Create Odds from dictionary."""
        # Parse game date
        game_date = data.get("game_date")
        if isinstance(game_date, str):
            game_date = datetime.fromisoformat(game_date.replace("Z", "+00:00"))
        elif not isinstance(game_date, datetime):
            game_date = datetime.now()

        # Parse fetched_at
        fetched_at = data.get("fetched_at")
        if isinstance(fetched_at, str):
            fetched_at = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))

        # Parse game lines
        game_lines_data = data.get("game_lines", {})
        game_lines = GameLines.from_dict(game_lines_data)

        # Parse player props
        player_props_data = data.get("player_props", [])
        player_props = [PlayerProp.from_dict(p) for p in player_props_data]

        # Get team info
        teams = data.get("teams", {})
        home_team = teams.get("home", {}).get("name", data.get("home_team", ""))
        away_team = teams.get("away", {}).get("name", data.get("away_team", ""))

        return cls(
            sport=data.get("sport", ""),
            home_team=home_team,
            away_team=away_team,
            game_date=game_date,
            game_lines=game_lines,
            player_props=player_props,
            source=data.get("source", "draftkings"),
            fetched_at=fetched_at,
        )

    def to_dict(self) -> dict:
        """Convert Odds to dictionary."""
        return {
            "sport": self.sport,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "game_date": self.game_date.isoformat(),
            "game_lines": self.game_lines.to_dict(),
            "player_props": [p.to_dict() for p in self.player_props],
            "source": self.source,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
        }
