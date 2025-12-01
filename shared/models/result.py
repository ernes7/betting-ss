"""Result dataclass model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any


@dataclass
class PlayerStats:
    """Individual player statistics from a game.

    Attributes:
        player: Player name
        team: Team abbreviation
        stats: Dictionary of stat values
    """
    player: str
    team: str
    stats: dict[str, Any] = field(default_factory=dict)

    def get_stat(self, stat_name: str, default: Any = 0) -> Any:
        """Get a specific stat value."""
        return self.stats.get(stat_name, default)

    @classmethod
    def from_dict(cls, data: dict) -> "PlayerStats":
        """Create PlayerStats from dictionary."""
        return cls(
            player=data.get("player", ""),
            team=data.get("team", ""),
            stats=data.get("stats", data),
        )

    def to_dict(self) -> dict:
        """Convert PlayerStats to dictionary."""
        return {
            "player": self.player,
            "team": self.team,
            "stats": self.stats,
        }


@dataclass
class GameScore:
    """Final game score.

    Attributes:
        home_score: Home team final score
        away_score: Away team final score
        home_quarters: List of quarterly scores for home team
        away_quarters: List of quarterly scores for away team
    """
    home_score: int = 0
    away_score: int = 0
    home_quarters: list[int] = field(default_factory=list)
    away_quarters: list[int] = field(default_factory=list)

    @property
    def total(self) -> int:
        """Get total points scored."""
        return self.home_score + self.away_score

    @property
    def home_won(self) -> bool:
        """Check if home team won."""
        return self.home_score > self.away_score

    @property
    def margin(self) -> int:
        """Get home team margin (positive = home win)."""
        return self.home_score - self.away_score

    @classmethod
    def from_dict(cls, data: dict) -> "GameScore":
        """Create GameScore from dictionary."""
        return cls(
            home_score=int(data.get("home_score", data.get("home", 0))),
            away_score=int(data.get("away_score", data.get("away", 0))),
            home_quarters=data.get("home_quarters", []),
            away_quarters=data.get("away_quarters", []),
        )

    def to_dict(self) -> dict:
        """Convert GameScore to dictionary."""
        return {
            "home_score": self.home_score,
            "away_score": self.away_score,
            "home_quarters": self.home_quarters,
            "away_quarters": self.away_quarters,
        }


@dataclass
class Result:
    """Game result with scores and player statistics.

    Attributes:
        sport: Sport name
        home_team: Home team
        away_team: Away team
        game_date: Game date
        score: Final score
        player_stats: List of player statistics
        team_stats: Dictionary of team-level statistics
        fetched_at: When result was fetched
        source: Data source (e.g., "pro-football-reference")
    """
    sport: str
    home_team: str
    away_team: str
    game_date: datetime
    score: GameScore = field(default_factory=GameScore)
    player_stats: list[PlayerStats] = field(default_factory=list)
    team_stats: dict[str, Any] = field(default_factory=dict)
    fetched_at: Optional[datetime] = None
    source: str = "reference"

    def __post_init__(self):
        if self.fetched_at is None:
            self.fetched_at = datetime.now()

    @property
    def game_date_str(self) -> str:
        """Get game date as YYYY-MM-DD string."""
        return self.game_date.strftime("%Y-%m-%d")

    @property
    def matchup(self) -> str:
        """Get matchup string."""
        return f"{self.away_team} @ {self.home_team}"

    @property
    def winner(self) -> str:
        """Get winning team."""
        return self.home_team if self.score.home_won else self.away_team

    @property
    def file_name(self) -> str:
        """Get standard file name for this result."""
        return f"{self.home_team}_{self.away_team}.json"

    def get_player_stats(self, player: str) -> Optional[PlayerStats]:
        """Get stats for a specific player."""
        for ps in self.player_stats:
            if player.lower() in ps.player.lower():
                return ps
        return None

    def get_player_stat(self, player: str, stat_name: str, default: Any = 0) -> Any:
        """Get a specific stat for a player."""
        ps = self.get_player_stats(player)
        return ps.get_stat(stat_name, default) if ps else default

    @classmethod
    def from_dict(cls, data: dict) -> "Result":
        """Create Result from dictionary."""
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

        # Parse score
        score_data = data.get("score", data.get("final_score", {}))
        score = GameScore.from_dict(score_data)

        # Parse player stats
        player_stats_data = data.get("player_stats", [])
        player_stats = [PlayerStats.from_dict(p) for p in player_stats_data]

        # Get team info
        teams = data.get("teams", {})
        home_team = teams.get("home", {}).get("name", data.get("home_team", ""))
        away_team = teams.get("away", {}).get("name", data.get("away_team", ""))

        return cls(
            sport=data.get("sport", ""),
            home_team=home_team,
            away_team=away_team,
            game_date=game_date,
            score=score,
            player_stats=player_stats,
            team_stats=data.get("team_stats", {}),
            fetched_at=fetched_at,
            source=data.get("source", "reference"),
        )

    def to_dict(self) -> dict:
        """Convert Result to dictionary."""
        return {
            "sport": self.sport,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "game_date": self.game_date.isoformat(),
            "score": self.score.to_dict(),
            "player_stats": [p.to_dict() for p in self.player_stats],
            "team_stats": self.team_stats,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
            "source": self.source,
        }
