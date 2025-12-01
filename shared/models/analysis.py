"""Analysis dataclass model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from shared.models.bet import BetOutcome


@dataclass
class BetResult:
    """Result of a single bet.

    Attributes:
        bet_id: Reference to the original bet
        player: Player name
        market: Bet market
        line: The betting line
        odds: American odds
        predicted_value: What was predicted
        actual_value: What actually happened
        outcome: Win/Loss/Push
        profit: Profit or loss amount
    """
    bet_id: str
    player: str
    market: str
    line: float
    odds: int
    predicted_value: float = 0.0
    actual_value: float = 0.0
    outcome: BetOutcome = BetOutcome.PENDING
    profit: float = 0.0
    stake: float = 0.0

    @property
    def hit(self) -> bool:
        """Check if bet was a winner."""
        return self.outcome == BetOutcome.WON

    @property
    def roi(self) -> float:
        """Calculate ROI for this bet."""
        if self.stake == 0:
            return 0.0
        return self.profit / self.stake

    @classmethod
    def from_dict(cls, data: dict) -> "BetResult":
        """Create BetResult from dictionary."""
        # Parse outcome
        outcome_str = data.get("outcome", "pending")
        try:
            outcome = BetOutcome(outcome_str)
        except ValueError:
            outcome = BetOutcome.PENDING

        return cls(
            bet_id=data.get("bet_id", data.get("id", "")),
            player=data.get("player", ""),
            market=data.get("market", ""),
            line=float(data.get("line", 0)),
            odds=int(data.get("odds", -110)),
            predicted_value=float(data.get("predicted_value", 0)),
            actual_value=float(data.get("actual_value", data.get("result", 0))),
            outcome=outcome,
            profit=float(data.get("profit", data.get("pnl", 0))),
            stake=float(data.get("stake", data.get("recommended_stake", 0))),
        )

    def to_dict(self) -> dict:
        """Convert BetResult to dictionary."""
        return {
            "bet_id": self.bet_id,
            "player": self.player,
            "market": self.market,
            "line": self.line,
            "odds": self.odds,
            "predicted_value": self.predicted_value,
            "actual_value": self.actual_value,
            "outcome": self.outcome.value,
            "profit": self.profit,
            "stake": self.stake,
        }


@dataclass
class Analysis:
    """Analysis comparing predictions to results.

    Attributes:
        sport: Sport name
        home_team: Home team
        away_team: Away team
        game_date: Game date
        bet_results: List of individual bet results
        total_stake: Total amount wagered
        total_profit: Net profit/loss
        win_count: Number of winning bets
        loss_count: Number of losing bets
        push_count: Number of pushes
        win_rate: Win percentage
        roi: Return on investment
        created_at: When analysis was created
    """
    sport: str
    home_team: str
    away_team: str
    game_date: datetime
    bet_results: list[BetResult] = field(default_factory=list)
    total_stake: float = 0.0
    total_profit: float = 0.0
    win_count: int = 0
    loss_count: int = 0
    push_count: int = 0
    win_rate: float = 0.0
    roi: float = 0.0
    created_at: Optional[datetime] = None
    summary: str = ""

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        self._calculate_metrics()

    def _calculate_metrics(self):
        """Calculate metrics from bet results."""
        if not self.bet_results:
            return

        self.win_count = sum(1 for b in self.bet_results if b.outcome == BetOutcome.WON)
        self.loss_count = sum(1 for b in self.bet_results if b.outcome == BetOutcome.LOST)
        self.push_count = sum(1 for b in self.bet_results if b.outcome == BetOutcome.PUSH)

        total_decided = self.win_count + self.loss_count
        if total_decided > 0:
            self.win_rate = self.win_count / total_decided

        self.total_stake = sum(b.stake for b in self.bet_results)
        self.total_profit = sum(b.profit for b in self.bet_results)

        if self.total_stake > 0:
            self.roi = self.total_profit / self.total_stake

    @property
    def game_date_str(self) -> str:
        """Get game date as YYYY-MM-DD string."""
        return self.game_date.strftime("%Y-%m-%d")

    @property
    def matchup(self) -> str:
        """Get matchup string."""
        return f"{self.away_team} @ {self.home_team}"

    @property
    def is_profitable(self) -> bool:
        """Check if analysis is profitable."""
        return self.total_profit > 0

    @property
    def total_bets(self) -> int:
        """Get total number of bets."""
        return len(self.bet_results)

    @property
    def file_name(self) -> str:
        """Get standard file name for this analysis."""
        return f"{self.home_team}_{self.away_team}.json"

    @classmethod
    def from_dict(cls, data: dict) -> "Analysis":
        """Create Analysis from dictionary."""
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

        # Parse bet results
        bet_results_data = data.get("bet_results", data.get("bets", []))
        bet_results = [BetResult.from_dict(b) for b in bet_results_data]

        # Get team info
        teams = data.get("teams", {})
        home_team = teams.get("home", {}).get("name", data.get("home_team", ""))
        away_team = teams.get("away", {}).get("name", data.get("away_team", ""))

        analysis = cls(
            sport=data.get("sport", ""),
            home_team=home_team,
            away_team=away_team,
            game_date=game_date,
            bet_results=bet_results,
            created_at=created_at,
            summary=data.get("summary", ""),
        )

        # Override calculated metrics if provided
        if "total_stake" in data:
            analysis.total_stake = float(data["total_stake"])
        if "total_profit" in data:
            analysis.total_profit = float(data["total_profit"])
        if "win_count" in data:
            analysis.win_count = int(data["win_count"])
        if "loss_count" in data:
            analysis.loss_count = int(data["loss_count"])
        if "push_count" in data:
            analysis.push_count = int(data["push_count"])
        if "win_rate" in data:
            analysis.win_rate = float(data["win_rate"])
        if "roi" in data:
            analysis.roi = float(data["roi"])

        return analysis

    def to_dict(self) -> dict:
        """Convert Analysis to dictionary."""
        return {
            "sport": self.sport,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "game_date": self.game_date.isoformat(),
            "bet_results": [b.to_dict() for b in self.bet_results],
            "total_stake": self.total_stake,
            "total_profit": self.total_profit,
            "win_count": self.win_count,
            "loss_count": self.loss_count,
            "push_count": self.push_count,
            "win_rate": self.win_rate,
            "roi": self.roi,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "summary": self.summary,
        }
