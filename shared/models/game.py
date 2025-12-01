"""Game dataclass model."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class GameStatus(Enum):
    """Status of a game."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"


@dataclass
class Team:
    """Team information.

    Attributes:
        name: Full team name (e.g., "Dallas Cowboys")
        abbreviation: Short abbreviation (e.g., "DAL")
        city: City name (e.g., "Dallas")
        nickname: Team nickname (e.g., "Cowboys")
    """
    name: str
    abbreviation: str
    city: str = ""
    nickname: str = ""

    def __str__(self) -> str:
        return self.name

    @classmethod
    def from_dict(cls, data: dict) -> "Team":
        """Create Team from dictionary."""
        return cls(
            name=data.get("name", ""),
            abbreviation=data.get("abbreviation", data.get("abbr", "")),
            city=data.get("city", ""),
            nickname=data.get("nickname", ""),
        )


@dataclass
class Game:
    """Game information.

    Attributes:
        id: Unique game identifier
        sport: Sport name (nfl, nba, etc.)
        home_team: Home team
        away_team: Away team
        game_date: Date and time of the game
        status: Current game status
        venue: Stadium/arena name
    """
    id: str
    sport: str
    home_team: Team
    away_team: Team
    game_date: datetime
    status: GameStatus = GameStatus.SCHEDULED
    venue: str = ""

    @property
    def game_date_str(self) -> str:
        """Get game date as YYYY-MM-DD string."""
        return self.game_date.strftime("%Y-%m-%d")

    @property
    def matchup(self) -> str:
        """Get matchup string (e.g., 'DAL vs NYG')."""
        return f"{self.away_team.abbreviation} @ {self.home_team.abbreviation}"

    @property
    def file_name(self) -> str:
        """Get standard file name for this game."""
        return f"{self.home_team.abbreviation}_{self.away_team.abbreviation}.json"

    @classmethod
    def from_dict(cls, data: dict) -> "Game":
        """Create Game from dictionary."""
        # Parse game date
        game_date = data.get("game_date")
        if isinstance(game_date, str):
            game_date = datetime.fromisoformat(game_date.replace("Z", "+00:00"))
        elif not isinstance(game_date, datetime):
            game_date = datetime.now()

        # Parse status
        status_str = data.get("status", "scheduled")
        try:
            status = GameStatus(status_str)
        except ValueError:
            status = GameStatus.SCHEDULED

        # Parse teams
        home_team_data = data.get("home_team", data.get("teams", {}).get("home", {}))
        away_team_data = data.get("away_team", data.get("teams", {}).get("away", {}))

        if isinstance(home_team_data, dict):
            home_team = Team.from_dict(home_team_data)
        else:
            home_team = Team(name=str(home_team_data), abbreviation=str(home_team_data)[:3].upper())

        if isinstance(away_team_data, dict):
            away_team = Team.from_dict(away_team_data)
        else:
            away_team = Team(name=str(away_team_data), abbreviation=str(away_team_data)[:3].upper())

        return cls(
            id=data.get("id", ""),
            sport=data.get("sport", ""),
            home_team=home_team,
            away_team=away_team,
            game_date=game_date,
            status=status,
            venue=data.get("venue", ""),
        )

    def to_dict(self) -> dict:
        """Convert Game to dictionary."""
        return {
            "id": self.id,
            "sport": self.sport,
            "home_team": {
                "name": self.home_team.name,
                "abbreviation": self.home_team.abbreviation,
                "city": self.home_team.city,
                "nickname": self.home_team.nickname,
            },
            "away_team": {
                "name": self.away_team.name,
                "abbreviation": self.away_team.abbreviation,
                "city": self.away_team.city,
                "nickname": self.away_team.nickname,
            },
            "game_date": self.game_date.isoformat(),
            "status": self.status.value,
            "venue": self.venue,
        }
