# Adding a New Sport

This guide explains how to add a new sport/league to the Sports Betting Analytics Platform.

## Overview

Adding a new sport requires implementing several components:

1. **Sport Configuration** - Implements the `SportConfig` interface
2. **Teams File** - Team metadata with abbreviations
3. **Constants File** - URLs, table mappings, rate limits
4. **Prompt Components** - Sport-specific prompt templates
5. **Odds Scraper** - DraftKings odds parsing (optional)
6. **Results Fetcher** - Boxscore/results parsing
7. **Factory Registration** - Register the new sport

## Prerequisites

Before starting, you need:

- **Data Source**: A statistics website (e.g., Baseball-Reference for MLB, Hockey-Reference for NHL)
- **Understanding of HTML Tables**: Table IDs from the data source for scraping
- **Team List**: All teams with abbreviations used by the data source
- **DraftKings URL Pattern**: If fetching odds from DraftKings

## Directory Structure

Create the following structure under `sports/`:

```
sports/
└── {sport}/
    ├── __init__.py
    ├── {sport}_config.py      # SportConfig implementation
    ├── teams.py               # Team metadata
    ├── constants.py           # URLs, tables, rate limits
    ├── prompt_components.py   # AI prompt templates
    ├── odds_scraper.py        # DraftKings parsing (optional)
    ├── {sport}_results_fetcher.py  # Boxscore parsing
    └── data/
        ├── rankings/          # League-wide stats
        ├── profiles/          # Team-specific data
        ├── predictions/       # AI predictions
        ├── predictions_ev/    # EV calculator predictions
        ├── odds/              # DraftKings odds
        ├── results/           # Game results
        └── analysis/          # P&L analysis
```

---

## Step 1: Create teams.py

Define all teams with their metadata.

**File**: `sports/{sport}/teams.py`

```python
"""Team constants and metadata for {SPORT}."""

# All teams with metadata
TEAMS = [
    {
        "name": "Team Full Name",           # e.g., "Boston Bruins"
        "abbreviation": "ABBR",             # DraftKings abbreviation (e.g., "BOS")
        "ref_abbr": "abbr",                 # Reference site abbreviation (e.g., "bos")
        "city": "City",                     # e.g., "Boston"
        "mascot": "Mascot",                 # e.g., "Bruins"
    },
    # ... add all teams
]

# Utility mappings (auto-generated)
TEAM_NAMES = sorted([team["name"] for team in TEAMS])
TEAM_ABBR_MAP = {team["abbreviation"]: team["name"] for team in TEAMS}
TEAM_NAME_TO_ABBR = {team["name"]: team["abbreviation"] for team in TEAMS}
DK_TO_REF_ABBR = {team["abbreviation"]: team["ref_abbr"] for team in TEAMS}
REF_TO_DK_ABBR = {team["ref_abbr"]: team["abbreviation"] for team in TEAMS}
```

**Key Points**:
- `abbreviation`: What DraftKings uses (usually standard 2-3 letter codes)
- `ref_abbr`: What the reference site uses (may differ from standard)

---

## Step 2: Create constants.py

Define URLs, table mappings, and configuration.

**File**: `sports/{sport}/constants.py`

```python
"""Configuration constants for {SPORT} scraping and analysis."""

from shared.config import (
    SPORTS_REFERENCE_RATE_LIMIT_CALLS,
    SPORTS_REFERENCE_RATE_LIMIT_PERIOD,
)

# Current season year
CURRENT_YEAR = 2025

# Fixed bet amount for P&L calculations
FIXED_BET_AMOUNT = 100

# Rate limiting (use global Sports-Reference limits)
REF_RATE_LIMIT_CALLS = SPORTS_REFERENCE_RATE_LIMIT_CALLS
REF_RATE_LIMIT_PERIOD = SPORTS_REFERENCE_RATE_LIMIT_PERIOD

# URLs for the reference site
STATS_URL = f"https://www.{sport}-reference.com/years/{CURRENT_YEAR}/"
DEFENSIVE_STATS_URL = None  # Set if sport has separate defensive page

# Ranking tables to extract (table_name: html_table_id)
# Inspect the HTML to find table IDs
RANKING_TABLES = {
    "standings": "standings",
    "team_stats": "team_stats",
    # ... add more as needed
}

# Defensive ranking tables (if applicable)
DEFENSIVE_RANKING_TABLES = {
    # "team_defense": "defense_stats",
}

# Team profile tables to extract from team pages
TEAM_PROFILE_TABLES = {
    "roster": "roster",
    "schedule": "games",
    "stats": "team_stats",
    # ... add more as needed
}

# Result tables to extract from boxscore pages
RESULT_TABLES = {
    "scoring": "scoring",
    "team_stats": "team_stats",
    "player_stats": "player_stats",
    # ... add more as needed
}

# Data folder paths
DATA_RANKINGS_DIR = "{sport}/data/rankings"
DATA_PROFILES_DIR = "{sport}/data/profiles"
DATA_ODDS_DIR = "{sport}/data/odds"

# Odds market types (for DraftKings)
ODDS_MARKET_TYPES = {
    "game_lines": ["Moneyline", "Spread", "Total"],
    "player_props": [
        # Sport-specific player prop markets
    ],
}
```

**Finding Table IDs**:
1. Open the reference site in a browser
2. Right-click on a table → Inspect
3. Look for `id="table_name"` in the HTML

---

## Step 3: Create {sport}_config.py

Implement the `SportConfig` interface.

**File**: `sports/{sport}/{sport}_config.py`

```python
"""Sport-specific configuration implementing SportConfig interface."""

from shared.base.sport_config import SportConfig
from sports.{sport}.teams import TEAMS
from sports.{sport}.constants import (
    CURRENT_YEAR,
    REF_RATE_LIMIT_CALLS,
    REF_RATE_LIMIT_PERIOD,
    STATS_URL,
    DEFENSIVE_STATS_URL,
    RANKING_TABLES,
    DEFENSIVE_RANKING_TABLES,
    TEAM_PROFILE_TABLES,
    RESULT_TABLES,
    DATA_RANKINGS_DIR,
    DATA_PROFILES_DIR,
)
from sports.{sport}.prompt_components import {Sport}PromptComponents


class {Sport}Config(SportConfig):
    """Sport-specific configuration."""

    @property
    def sport_name(self) -> str:
        return "{sport}"

    @property
    def teams(self) -> list[dict]:
        return TEAMS

    @property
    def ranking_tables(self) -> dict[str, str]:
        return RANKING_TABLES

    @property
    def profile_tables(self) -> dict[str, str]:
        return TEAM_PROFILE_TABLES

    @property
    def result_tables(self) -> dict[str, str]:
        return RESULT_TABLES

    @property
    def stats_url(self) -> str:
        return STATS_URL

    @property
    def defensive_stats_url(self) -> str:
        return DEFENSIVE_STATS_URL

    @property
    def defensive_ranking_tables(self) -> dict[str, str]:
        return DEFENSIVE_RANKING_TABLES

    @property
    def rate_limit_calls(self) -> int:
        return REF_RATE_LIMIT_CALLS

    @property
    def rate_limit_period(self) -> int:
        return REF_RATE_LIMIT_PERIOD

    @property
    def data_rankings_dir(self) -> str:
        return DATA_RANKINGS_DIR

    @property
    def data_profiles_dir(self) -> str:
        return DATA_PROFILES_DIR

    @property
    def predictions_dir(self) -> str:
        return "{sport}/data/predictions"

    @property
    def predictions_ev_dir(self) -> str:
        return "{sport}/data/predictions_ev"

    @property
    def results_dir(self) -> str:
        return "{sport}/data/results"

    @property
    def analysis_dir(self) -> str:
        return "{sport}/data/analysis"

    @property
    def analysis_ev_dir(self) -> str:
        return "{sport}/data/analysis_ev"

    @property
    def prompt_components(self) -> {Sport}PromptComponents:
        return {Sport}PromptComponents()

    def build_team_url(self, team_abbr: str) -> str:
        """Build team URL using reference site pattern."""
        return f"https://www.{sport}-reference.com/teams/{team_abbr}/{CURRENT_YEAR}.htm"

    def build_boxscore_url(self, game_date: str, home_team_abbr: str) -> str:
        """Build boxscore URL for game results."""
        date_str = game_date.replace("-", "")
        return f"https://www.{sport}-reference.com/boxscores/{date_str}0{home_team_abbr}.htm"
```

---

## Step 4: Create prompt_components.py

Define sport-specific prompts for AI predictions.

**File**: `sports/{sport}/prompt_components.py`

```python
"""Sport-specific prompt components for AI predictions."""


class {Sport}PromptComponents:
    """Prompt templates for {SPORT} betting analysis."""

    @property
    def sport_name(self) -> str:
        return "{SPORT}"

    @property
    def bet_types(self) -> str:
        """Return available bet types for this sport."""
        return """
Available Bet Types:
- Moneyline (game winner)
- Spread (point/goal/run differential)
- Total (over/under combined score)
- Player Props:
  - Points/Goals scored
  - Assists
  - Shots on goal
  - Other sport-specific stats
"""

    @property
    def key_factors(self) -> str:
        """Return key factors for analysis."""
        return """
Key Factors to Consider:
- Recent form (last 5-10 games)
- Head-to-head history
- Home/away performance
- Injuries and lineup changes
- Rest days between games
- Strength of schedule
"""

    @property
    def analysis_instructions(self) -> str:
        """Return analysis instructions."""
        return """
Analysis Instructions:
1. Compare team statistics
2. Evaluate player matchups
3. Consider situational factors
4. Calculate true probability
5. Identify value vs bookmaker odds
6. Focus on +3% EV minimum threshold
"""
```

---

## Step 5: Register the Sport

Add the new sport to the factory.

**File**: `shared/register_sports.py`

```python
"""Register all available sports with the factory."""

from shared.factory import SportFactory


def register_all_sports():
    """Register all sport configurations with the factory."""
    from sports.nfl.nfl_config import NFLConfig
    from sports.nba.nba_config import NBAConfig
    from sports.{sport}.{sport}_config import {Sport}Config  # ADD THIS

    SportFactory.register("nfl", NFLConfig)
    SportFactory.register("nba", NBAConfig)
    SportFactory.register("{sport}", {Sport}Config)  # ADD THIS


register_all_sports()
```

---

## Step 6: Create Data Directories

Create the data folder structure:

```bash
mkdir -p sports/{sport}/data/rankings
mkdir -p sports/{sport}/data/profiles
mkdir -p sports/{sport}/data/predictions
mkdir -p sports/{sport}/data/predictions_ev
mkdir -p sports/{sport}/data/odds
mkdir -p sports/{sport}/data/results
mkdir -p sports/{sport}/data/analysis
```

---

## Step 7: Add to CLI (Optional)

Add the sport to the CLI menu in `cli.py`:

```python
SPORTS = {
    "1": {"name": "NFL", "emoji": "🏈", "code": "nfl"},
    "2": {"name": "NBA", "emoji": "🏀", "code": "nba"},
    "3": {"name": "{SPORT}", "emoji": "🏒", "code": "{sport}"},  # ADD THIS
}
```

---

## Testing Your Implementation

1. **Verify Registration**:
   ```python
   from shared.factory import SportFactory
   config = SportFactory.create("{sport}")
   print(config.config.sport_name)  # Should print "{sport}"
   ```

2. **Test Team Lookup**:
   ```python
   team = config.config.get_team_by_name("Team Name")
   print(team)  # Should return team dict
   ```

3. **Test URL Building**:
   ```python
   url = config.config.build_team_url("abbr")
   print(url)  # Should return valid URL
   ```

4. **Run Tests**:
   ```bash
   poetry run pytest sports/{sport}/tests/ -v
   ```

---

## Checklist

- [ ] Created `sports/{sport}/` directory structure
- [ ] Implemented `teams.py` with all teams
- [ ] Implemented `constants.py` with URLs and table mappings
- [ ] Implemented `{sport}_config.py` extending `SportConfig`
- [ ] Implemented `prompt_components.py`
- [ ] Registered sport in `shared/register_sports.py`
- [ ] Created data directories
- [ ] Added to CLI menu (optional)
- [ ] Tested registration and team lookup
- [ ] Added unit tests

---

## Reference: NFL Implementation

For a complete working example, see the NFL implementation:

- `sports/nfl/nfl_config.py` - SportConfig implementation
- `sports/nfl/teams.py` - Team metadata
- `sports/nfl/constants.py` - URLs and table mappings
- `sports/nfl/prompt_components.py` - Prompt templates

---

## Common Issues

1. **Table IDs Not Found**: Use browser dev tools to inspect table elements
2. **Rate Limiting**: Use the shared Sports-Reference rate limits
3. **Abbreviation Mismatch**: Ensure DraftKings and reference site abbreviations are mapped correctly
4. **Circular Imports**: Import sport configs inside `register_all_sports()` function
