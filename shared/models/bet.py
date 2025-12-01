"""Bet dataclass model."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class BetType(Enum):
    """Type of bet."""
    MONEYLINE = "moneyline"
    SPREAD = "spread"
    TOTAL = "total"
    PLAYER_PROP = "player_prop"
    TEAM_PROP = "team_prop"


class BetOutcome(Enum):
    """Outcome of a bet."""
    PENDING = "pending"
    WON = "won"
    LOST = "lost"
    PUSH = "push"
    VOID = "void"


@dataclass
class Bet:
    """A single betting opportunity.

    Attributes:
        id: Unique bet identifier
        player: Player name (for player props)
        team: Team abbreviation
        market: Market type (e.g., "passing_yards", "rushing_yards")
        line: The betting line (e.g., 250.5)
        odds: American odds (e.g., -110, +150)
        ev_edge: Expected value edge as decimal (e.g., 0.05 for 5%)
        recommended_stake: Suggested stake amount
        bet_type: Type of bet
        description: Human-readable bet description
    """
    id: str
    player: str
    team: str
    market: str
    line: float
    odds: int
    ev_edge: float = 0.0
    recommended_stake: float = 0.0
    bet_type: BetType = BetType.PLAYER_PROP
    description: str = ""
    outcome: BetOutcome = BetOutcome.PENDING
    actual_result: Optional[float] = None

    @property
    def implied_probability(self) -> float:
        """Calculate implied probability from American odds."""
        if self.odds > 0:
            return 100 / (self.odds + 100)
        else:
            return abs(self.odds) / (abs(self.odds) + 100)

    @property
    def decimal_odds(self) -> float:
        """Convert American odds to decimal odds."""
        if self.odds > 0:
            return (self.odds / 100) + 1
        else:
            return (100 / abs(self.odds)) + 1

    @property
    def is_ev_positive(self) -> bool:
        """Check if bet has positive expected value."""
        return self.ev_edge > 0

    @property
    def ev_edge_percent(self) -> str:
        """Get EV edge as percentage string."""
        return f"{self.ev_edge * 100:.1f}%"

    def format_odds(self) -> str:
        """Format odds as string with sign."""
        return f"+{self.odds}" if self.odds > 0 else str(self.odds)

    @classmethod
    def from_dict(cls, data: dict) -> "Bet":
        """Create Bet from dictionary."""
        # Parse bet type
        bet_type_str = data.get("bet_type", "player_prop")
        try:
            bet_type = BetType(bet_type_str)
        except ValueError:
            bet_type = BetType.PLAYER_PROP

        # Parse outcome
        outcome_str = data.get("outcome", "pending")
        try:
            outcome = BetOutcome(outcome_str)
        except ValueError:
            outcome = BetOutcome.PENDING

        return cls(
            id=data.get("id", ""),
            player=data.get("player", ""),
            team=data.get("team", ""),
            market=data.get("market", data.get("prop_type", "")),
            line=float(data.get("line", 0)),
            odds=int(data.get("odds", -110)),
            ev_edge=float(data.get("ev_edge", data.get("edge", 0))),
            recommended_stake=float(data.get("recommended_stake", data.get("stake", 0))),
            bet_type=bet_type,
            description=data.get("description", ""),
            outcome=outcome,
            actual_result=data.get("actual_result"),
        )

    def to_dict(self) -> dict:
        """Convert Bet to dictionary."""
        return {
            "id": self.id,
            "player": self.player,
            "team": self.team,
            "market": self.market,
            "line": self.line,
            "odds": self.odds,
            "ev_edge": self.ev_edge,
            "recommended_stake": self.recommended_stake,
            "bet_type": self.bet_type.value,
            "description": self.description,
            "outcome": self.outcome.value,
            "actual_result": self.actual_result,
        }
