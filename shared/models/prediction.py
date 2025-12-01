"""Prediction dataclass model."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from shared.models.bet import Bet


class PredictionSource(Enum):
    """Source of the prediction."""
    AI = "ai"
    EV_CALCULATOR = "ev_calculator"
    MANUAL = "manual"


class PredictionStatus(Enum):
    """Status of the prediction."""
    PENDING = "pending"
    ANALYZED = "analyzed"
    EXPIRED = "expired"


@dataclass
class Prediction:
    """A prediction for a game.

    Attributes:
        id: Unique prediction identifier
        sport: Sport name
        home_team: Home team
        away_team: Away team
        game_date: Game date
        bets: List of recommended bets
        source: Prediction source (AI or EV calculator)
        status: Current status
        confidence: Overall confidence score (0-1)
        analysis_summary: AI analysis summary
        created_at: When prediction was created
        model: AI model used (if applicable)
        tokens_used: Total tokens used (if AI)
        cost: API cost (if AI)
    """
    id: str
    sport: str
    home_team: str
    away_team: str
    game_date: datetime
    bets: list[Bet] = field(default_factory=list)
    source: PredictionSource = PredictionSource.AI
    status: PredictionStatus = PredictionStatus.PENDING
    confidence: float = 0.0
    analysis_summary: str = ""
    created_at: Optional[datetime] = None
    model: str = ""
    tokens_used: int = 0
    cost: float = 0.0

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    @property
    def game_date_str(self) -> str:
        """Get game date as YYYY-MM-DD string."""
        return self.game_date.strftime("%Y-%m-%d")

    @property
    def matchup(self) -> str:
        """Get matchup string."""
        return f"{self.away_team} @ {self.home_team}"

    @property
    def ev_positive_bets(self) -> list[Bet]:
        """Get only EV+ bets."""
        return [b for b in self.bets if b.is_ev_positive]

    @property
    def total_stake(self) -> float:
        """Get total recommended stake."""
        return sum(b.recommended_stake for b in self.bets)

    @property
    def file_name(self) -> str:
        """Get standard file name for this prediction."""
        return f"{self.home_team}_{self.away_team}.json"

    @classmethod
    def from_dict(cls, data: dict) -> "Prediction":
        """Create Prediction from dictionary."""
        # Parse game date
        game_date = data.get("game_date")
        if isinstance(game_date, str):
            game_date = datetime.fromisoformat(game_date.replace("Z", "+00:00"))
        elif not isinstance(game_date, datetime):
            game_date = datetime.now()

        # Parse created_at
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        # Parse source
        source_str = data.get("source", "ai")
        try:
            source = PredictionSource(source_str)
        except ValueError:
            source = PredictionSource.AI

        # Parse status
        status_str = data.get("status", "pending")
        try:
            status = PredictionStatus(status_str)
        except ValueError:
            status = PredictionStatus.PENDING

        # Parse bets
        bets_data = data.get("bets", data.get("recommended_bets", []))
        bets = [Bet.from_dict(b) for b in bets_data]

        # Get team info
        teams = data.get("teams", {})
        home_team = teams.get("home", {}).get("name", data.get("home_team", ""))
        away_team = teams.get("away", {}).get("name", data.get("away_team", ""))

        return cls(
            id=data.get("id", ""),
            sport=data.get("sport", ""),
            home_team=home_team,
            away_team=away_team,
            game_date=game_date,
            bets=bets,
            source=source,
            status=status,
            confidence=float(data.get("confidence", 0)),
            analysis_summary=data.get("analysis_summary", data.get("summary", "")),
            created_at=created_at,
            model=data.get("model", ""),
            tokens_used=int(data.get("tokens_used", data.get("total_tokens", 0))),
            cost=float(data.get("cost", data.get("api_cost", 0))),
        )

    def to_dict(self) -> dict:
        """Convert Prediction to dictionary."""
        return {
            "id": self.id,
            "sport": self.sport,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "game_date": self.game_date.isoformat(),
            "bets": [b.to_dict() for b in self.bets],
            "source": self.source.value,
            "status": self.status.value,
            "confidence": self.confidence,
            "analysis_summary": self.analysis_summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "model": self.model,
            "tokens_used": self.tokens_used,
            "cost": self.cost,
        }
