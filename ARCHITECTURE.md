# Sports Betting Analytics Platform - Architecture Guide

## Quick Reference

### File Naming Conventions

**All files follow the same pattern**: `{HOME_ABBR}_{AWAY_ABBR}.json` (home team first, lowercase PFR abbreviations)

```
Predictions:  nfl/data/predictions/2025-11-02/cin_chi.json
Results:      nfl/data/results/2025-11-02/cin_chi.json
Analysis:     nfl/data/analysis/2025-11-02/cin_chi.json
Odds:         nfl/data/odds/2025-11-02/cin_chi.json
```

**Metadata Key**: `{game_date}_{home_abbr}_{away_abbr}` (matches filename pattern)

### Team Abbreviations

**PFR (Pro-Football-Reference)**: Used throughout the system
- Format: 3 letters, lowercase
- Examples: `kan` (KC Chiefs), `was` (Washington), `rav` (Baltimore), `sdg` (LA Chargers)
- Source: `nfl/teams.py` → TEAMS dict → `pfr_abbr` field
- Used for: All file naming, URLs, internal references

**DraftKings**: Only used during odds fetching
- Format: 2-3 uppercase letters
- Examples: `KC`, `BAL`, `MIA`
- Automatically converted to PFR abbreviations when saving odds files

### Data Flow Overview

```
1. RANKINGS (auto, daily)    → nfl/data/rankings/*.json (6 tables)
2. PROFILES (auto, daily)    → nfl/data/profiles/{team}/*.json (8 tables/team)
3. ODDS (required)           → User provides DraftKings URL → nfl/data/odds/{date}/{home}_{away}.json
4. PREDICTIONS (on-demand)   → Claude AI → nfl/data/predictions/{date}/{home}_{away}.{md,json}
5. RESULTS (post-game)       → Scrape boxscores → nfl/data/results/{date}/{home}_{away}.json
6. ANALYSIS (post-game)      → Claude AI → nfl/data/analysis/{date}/{home}_{away}.json
```

### Common Commands

```bash
# Start CLI
poetry run python cli.py

# Workflow
1. Select sport (NFL/NBA)
2. Predict Game → Enter date, teams, DraftKings URL
3. Fetch Results → After games complete
4. View Analysis → See P&L, ROI, win rate

# Streamlit Dashboard
streamlit run streamlit/app.py
```

---

## Project Structure

### Directory Overview

```
betting-ss/
├── shared/                       # Cross-sport infrastructure
│   ├── base/                     # Abstract interfaces
│   │   ├── predictor.py          # Base prediction logic (EV+ analysis)
│   │   ├── analyzer.py           # Base P&L analysis logic
│   │   ├── scraper.py            # Base scraping logic
│   │   ├── results_fetcher.py    # Base results fetching
│   │   ├── sport_config.py       # Sport configuration interface
│   │   └── prompt_builder.py     # Prompt template builder
│   ├── services/                 # Business logic layer
│   │   ├── odds_service.py       # Odds loading operations
│   │   ├── profile_service.py    # Profile loading with auto-scraping
│   │   ├── metadata_service.py   # Metadata load/save operations
│   │   └── team_service.py       # Team operations
│   ├── repositories/             # Data access layer (JSON → DB ready)
│   │   ├── prediction_repository.py
│   │   ├── results_repository.py
│   │   ├── odds_repository.py
│   │   └── analysis_repository.py
│   ├── config/                   # Configuration layer
│   │   ├── api_config.py         # Claude API settings
│   │   ├── paths_config.py       # Path templates
│   │   └── scraping_config.py    # Rate limits, browser config
│   ├── utils/                    # Utilities
│   │   ├── console_utils.py      # CLI formatting (16 functions)
│   │   ├── validation_utils.py   # Input validation (9 functions)
│   │   ├── web_scraper.py        # Playwright web scraping
│   │   └── table_extractor.py    # HTML table extraction
│   ├── factory.py                # SportFactory (creates sport instances)
│   └── register_sports.py        # Sport registration
│
├── nfl/                          # NFL implementation
│   ├── cli_utils/
│   │   ├── predict.py            # NFL prediction CLI command
│   │   ├── fetch_odds.py         # NFL odds fetching (URL-based)
│   │   └── fetch_results.py      # NFL results fetching
│   ├── nfl_config.py             # NFL sport configuration
│   ├── nfl_analyzer.py           # NFL-specific P&L analysis
│   ├── nfl_results_fetcher.py    # NFL results extraction
│   ├── odds_scraper.py           # DraftKings odds parser
│   ├── prompt_components.py      # NFL prompt templates
│   ├── teams.py                  # NFL team metadata (32 teams)
│   └── data/
│       ├── rankings/             # League-wide stats (6 tables)
│       ├── profiles/             # Team-specific data (8 tables/team)
│       ├── predictions/          # EV+ predictions with Kelly stakes
│       ├── odds/                 # DraftKings betting lines
│       ├── results/              # Game results from boxscores
│       └── analysis/             # P&L analysis (bet-by-bet)
│
├── nba/                          # NBA implementation (parallel structure)
│   └── (same structure as NFL)
│
├── streamlit/                    # Web dashboard
│   ├── components/               # Modular UI components
│   ├── app.py                    # Main dashboard
│   └── theme.py                  # Custom CSS
│
├── cli.py                        # Main CLI entry point
└── README.md                     # User-facing documentation
```

### Clean Architecture Layers

The project follows **Clean Architecture** principles with clear separation of concerns:

**Configuration Layer** (`shared/config/`)
- API settings, cost calculation
- Path templates for all data directories
- Rate limits, browser configuration

**Service Layer** (`shared/services/`)
- Business logic for odds, profiles, metadata
- Automatic path construction
- Consistent error handling
- Sport-agnostic interfaces

**Repository Layer** (`shared/repositories/`)
- Data access abstraction
- JSON file operations
- Database-ready (easy migration from JSON to SQL)
- Follows Repository pattern

**Benefits**:
- No code duplication across CLI commands
- Easy to test (mockable services)
- Consistent UX and error handling
- Same code works for NFL, NBA, future sports

---

## Complete Data Flow Pipeline

### 1. Rankings Scraping (Automatic, Daily)

```
TRIGGER: First prediction of the day
SOURCE: Pro-Football-Reference league pages
SCRAPER: shared/base/scraper.py → extract_rankings()
CONFIG: nfl/nfl_config.py → RANKING_TABLES (6 tables)
OUTPUT: nfl/data/rankings/*.json
  - team_offense.json
  - passing_offense.json
  - rushing_offense.json
  - scoring_offense.json
  - afc_standings.json
  - nfc_standings.json
METADATA: nfl/data/rankings/.metadata.json
  {"last_scraped": "2025-11-02"}
```

**Purpose**: Provides league-wide context for all teams

### 2. Team Profiles Scraping (Automatic, Daily Per Team)

```
TRIGGER: Prediction request for a team
SOURCE: Pro-Football-Reference team pages
SCRAPER: shared/base/scraper.py → extract_team_profile()
CONFIG: nfl/nfl_config.py → TEAM_PROFILE_TABLES (8 tables)
OUTPUT: nfl/data/profiles/{team_name}/*.json
  - injury_report.json
  - team_stats.json
  - schedule_results.json
  - passing.json
  - rushing_receiving.json
  - defense_fumbles.json
  - scoring_summary.json
  - touchdown_log.json
METADATA: nfl/data/profiles/.metadata.json
  {"{team_folder_name}": "2025-11-02"}
```

**Purpose**: Provides team-specific details, injuries, recent performance

### 3. Odds Fetching (Required, URL-Based)

```
TRIGGER: User provides DraftKings URL during prediction
SOURCE: DraftKings game page (fetched automatically via Playwright)
INPUT: DraftKings URL (e.g., https://sportsbook.draftkings.com/leagues/football/...)
SCRAPER: nfl/odds_scraper.py → NFLOddsScraper.extract_odds()
PROCESS:
  1. Playwright fetches HTML from URL
  2. Extract game lines (moneyline, spread, total)
  3. Extract player props (all milestone formats: 150+, 175+, 200+, etc.)
  4. Convert DraftKings abbreviations to PFR
  5. Save with standardized naming
OUTPUT: nfl/data/odds/{date}/{home_abbr}_{away_abbr}.json
METADATA: nfl/data/odds/.metadata.json
  {
    "{date}_{home}_{away}": {
      "fetched_at": "ISO timestamp",
      "game_date": "2025-11-02",
      "home_team_abbr": "cin",
      "away_team_abbr": "chi",
      "source": "draftkings"
    }
  }
```

**Data Structure**:
```json
{
  "sport": "nfl",
  "teams": {
    "away": {"name": "Chicago Bears", "abbr": "CHI", "pfr_abbr": "chi"},
    "home": {"name": "Cincinnati Bengals", "abbr": "CIN", "pfr_abbr": "cin"}
  },
  "game_date": "2025-11-02T18:00:00Z",
  "fetched_at": "2025-11-01T14:30:00",
  "source": "draftkings",
  "game_lines": {
    "moneyline": {"away": 280, "home": -350},
    "spread": {"away": 8.5, "away_odds": -110, "home": -8.5, "home_odds": -110},
    "total": {"line": 47.5, "over": -110, "under": -110}
  },
  "player_props": [
    {
      "player": "Joe Burrow",
      "team": "cin",
      "props": [
        {
          "market": "passing_yards",
          "milestones": [
            {"line": 200, "odds": -400},
            {"line": 225, "odds": -200},
            {"line": 250, "odds": 100},
            {"line": 275, "odds": 250}
          ]
        }
      ]
    }
  ]
}
```

**Purpose**: Required for EV+ analysis - provides market odds to calculate expected value

### 4. Prediction Generation (On-Demand, EV+ Singles)

```
TRIGGER: User request via CLI
INPUT:
  - Game date
  - Team A, Team B, Home team
  - DraftKings URL (required)
PROCESS: nfl/cli_utils/predict.py → predict_game()
  1. Check if already predicted today (metadata)
  2. Fetch odds from DraftKings URL (automatic)
  3. Load/scrape rankings (if needed)
  4. Load/scrape team profiles (if needed)
  5. Extract team stats from rankings
  6. Build comprehensive prompt:
     - Rankings data (6 tables)
     - Both team profiles (8 tables each)
     - Betting odds (game lines + player props)
     - EV calculation methodology
     - Kelly Criterion formulas
     - Minimum +3% EV threshold
  7. Call Claude Sonnet 4.5 API
  8. Parse top 5 EV+ bets
  9. Save prediction files
  10. Update metadata
OUTPUT:
  - nfl/data/predictions/{date}/{home}_{away}.md
  - nfl/data/predictions/{date}/{home}_{away}.json
METADATA: nfl/data/predictions/.metadata.json
  {
    "{date}_{home}_{away}": {
      "last_predicted": "2025-11-01",
      "results_fetched": false,
      "odds_used": true,
      "odds_source": "draftkings",
      "game_date": "2025-11-02",
      "teams": ["Chicago Bears", "Cincinnati Bengals"],
      "home_team": "Cincinnati Bengals",
      "home_team_abbr": "cin"
    }
  }
```

**Prediction JSON Structure**:
```json
{
  "sport": "nfl",
  "prediction_type": "ev_singles",
  "teams": ["Chicago Bears", "Cincinnati Bengals"],
  "home_team": "Cincinnati Bengals",
  "date": "2025-11-02",
  "generated_at": "2025-11-01 20:32:32",
  "model": "claude-sonnet-4-5-20250929",
  "api_cost": 0.119,
  "tokens": {"input": 36181, "output": 698, "total": 36879},
  "bets": [
    {
      "rank": 1,
      "bet": "Joe Burrow Over 250.5 Passing Yards",
      "odds": 150,
      "implied_probability": 40.0,
      "true_probability": 58.0,
      "expected_value": 8.5,
      "kelly_full": 29.3,
      "kelly_half": 14.7,
      "reasoning": "Burrow averages 285 yards at home with favorable matchup..."
    }
  ],
  "summary": {
    "total_bets": 5,
    "avg_ev": 6.2,
    "ev_range": [3.5, 8.5],
    "avg_kelly_half": 12.4
  }
}
```

**Purpose**: Identifies profitable betting opportunities with mathematical edge

### 5. Results Fetching (Post-Game)

```
TRIGGER: User request after games complete
SOURCE: Pro-Football-Reference boxscores
PROCESS: nfl/cli_utils/fetch_results.py → fetch_results()
  1. Load predictions metadata
  2. Prompt for game date
  3. Find games with results_fetched = false
  4. For each game:
     a. Build boxscore URL using home_team_abbr
     b. Scrape boxscore tables
     c. Extract final score and player stats
     d. Save results file
     e. Update metadata: results_fetched = true
OUTPUT: nfl/data/results/{date}/{home}_{away}.json
METADATA: predictions/.metadata.json updated with results_fetched_at
```

**Results JSON Structure**:
```json
{
  "sport": "nfl",
  "game_date": "2025-11-02",
  "teams": {"away": "Bears", "home": "Bengals"},
  "final_score": {"away": 7, "home": 28},
  "winner": "Bengals",
  "boxscore_url": "https://...",
  "fetched_at": "2025-11-03 11:13:34",
  "tables": {
    "scoring": {...},
    "team_stats": {...},
    "player_offense": {...},
    "defense": {...}
  }
}
```

**Purpose**: Provides actual game outcomes for accuracy analysis

### 6. P&L Analysis (Post-Game)

```
TRIGGER: User request after results available
SOURCE: Prediction JSON + Results JSON
PROCESS: shared/base/analyzer.py → generate_analysis()
  1. Load prediction (5 EV+ bets)
  2. Load results (final stats)
  3. Build analysis prompt
  4. Call Claude API to evaluate each bet
  5. Calculate profit/loss:
     - Win: $100 × (odds/100) for American odds > 0
     - Win: $100 × (100/abs(odds)) for American odds < 0
     - Loss: -$100
  6. Calculate summary metrics:
     - Total P&L
     - ROI percentage
     - Win rate
     - Realized edge vs predicted edge
  7. Save analysis
  8. Update metadata
OUTPUT: nfl/data/analysis/{date}/{home}_{away}.json
METADATA: predictions/.metadata.json updated with analysis_generated_at
```

**Analysis JSON Structure**:
```json
{
  "bet_results": [
    {
      "rank": 1,
      "bet": "Joe Burrow Over 250.5 Passing Yards",
      "odds": 150,
      "ev_percent": 8.5,
      "implied_probability": 40.0,
      "true_probability": 58.0,
      "kelly_half": 14.7,
      "won": true,
      "actual_value": "299 passing yards",
      "stake": 100,
      "profit": 150.00,
      "reasoning": "Burrow completed 25/34 passes for 299 yards..."
    }
  ],
  "summary": {
    "total_bets": 5,
    "bets_won": 3,
    "bets_lost": 2,
    "win_rate": 60.0,
    "total_profit": 210.00,
    "total_staked": 500.00,
    "roi_percent": 42.0,
    "avg_predicted_ev": 6.2,
    "realized_ev": 3.5
  },
  "insights": [
    "3 of 5 bets hit for 60% win rate and +42% ROI",
    "Passing yard props outperformed (2/2 winners)",
    "True probability estimates were conservative but accurate"
  ]
}
```

**Purpose**: Tracks actual performance, validates prediction accuracy, calculates ROI

---

## Architecture Patterns

### Factory Pattern

**Location**: `shared/factory.py`

```python
class SportFactory:
    _sports = {}

    @classmethod
    def register(cls, name, config_class):
        """Register a sport configuration"""
        cls._sports[name] = config_class

    @classmethod
    def create(cls, sport_name):
        """Create a Sport instance with scraper and predictor"""
        config = cls._sports[sport_name]()
        return Sport(
            config=config,
            scraper=Scraper(config),
            predictor=Predictor(config),
            analyzer=Analyzer(config),
            results_fetcher=ResultsFetcher(config)
        )
```

**Usage in CLI**:
```python
from shared.factory import SportFactory

nfl_sport = SportFactory.create("nfl")
nfl_sport.scraper.extract_rankings()
nfl_sport.predictor.generate_predictions(...)
```

**Benefits**: Sport-agnostic code, easy to add new sports

### Repository Pattern

**Location**: `shared/repositories/`

**Purpose**: Abstracts data access, enables easy migration from JSON to database

**Example**:
```python
# Old way (manual file operations)
with open(f"nfl/data/odds/{date}/{home}_{away}.json") as f:
    odds_data = json.load(f)

# New way (repository pattern)
from shared.repositories import OddsRepository

odds_repo = OddsRepository("nfl")
odds_data = odds_repo.load_odds(date, home_abbr, away_abbr)
```

**Repositories**:
- `OddsRepository`: Odds file operations
- `PredictionRepository`: Prediction file operations
- `ResultsRepository`: Results file operations
- `AnalysisRepository`: Analysis file operations

### Service Layer Pattern

**Location**: `shared/services/`

**Purpose**: Business logic separation, consistent error handling

**Example**:
```python
from shared.services import OddsService

odds_service = OddsService("nfl")
odds_data = odds_service.load_odds_for_game(date, team_a, team_b, home)
# Automatically tries multiple file combinations
# Returns None if not found (graceful handling)
```

**Services**:
- `OddsService`: Odds loading with automatic path construction
- `ProfileService`: Profile loading with auto-scraping
- `MetadataService`: Metadata load/save operations
- `TeamService`: Team selection and abbreviation conversion

---

## Metadata System

### Three Metadata Files

#### Rankings Metadata
**File**: `nfl/data/rankings/.metadata.json`
```json
{"last_scraped": "2025-11-02"}
```
- **Purpose**: Prevents multiple daily scrapes
- **Updated by**: `extract_rankings()`
- **Checked before**: Every prediction request

#### Profiles Metadata
**File**: `nfl/data/profiles/.metadata.json`
```json
{
  "cincinnati_bengals": "2025-11-02",
  "chicago_bears": "2025-11-02"
}
```
- **Purpose**: Tracks per-team scraping dates
- **Key format**: Team folder name (lowercase, underscores)
- **Updated by**: `extract_team_profile()`
- **Checked before**: Loading each team's profile

#### Predictions Metadata (Master Tracker)
**File**: `nfl/data/predictions/.metadata.json`
```json
{
  "2025-11-02_cin_chi": {
    "last_predicted": "2025-11-01",
    "results_fetched": true,
    "odds_used": true,
    "odds_source": "draftkings",
    "game_date": "2025-11-02",
    "teams": ["Chicago Bears", "Cincinnati Bengals"],
    "home_team": "Cincinnati Bengals",
    "home_team_abbr": "cin",
    "results_fetched_at": "2025-11-03 11:13:37",
    "analysis_generated": true,
    "analysis_generated_at": "2025-11-03 11:14:24"
  }
}
```
- **Purpose**: Tracks complete lifecycle of predictions
- **Key format**: `{game_date}_{home_abbr}_{away_abbr}`
- **Updated by**: Multiple commands (predict, fetch_results, analysis)
- **Fields**:
  - `last_predicted`: When prediction was generated
  - `results_fetched`: Boolean flag
  - `odds_used`: Whether odds were available
  - `odds_source`: Which sportsbook (e.g., "draftkings")
  - `results_fetched_at`: Timestamp
  - `analysis_generated`: Boolean flag
  - `analysis_generated_at`: Timestamp

### Game Lifecycle

```
1. Prediction Created
   └─ metadata[game_key] created with results_fetched=false

2. Results Fetched
   └─ metadata[game_key].results_fetched = true
   └─ metadata[game_key].results_fetched_at = timestamp

3. Analysis Generated
   └─ metadata[game_key].analysis_generated = true
   └─ metadata[game_key].analysis_generated_at = timestamp
```

---

## EV+ Analysis Methodology

### Minimum EV Threshold

**Hardcoded**: +3% minimum expected value
**Location**: `shared/base/prompt_builder.py:68`

```python
METHODOLOGY:
3. EXPECTED VALUE: EV = (True Prob × Decimal Odds) - 1 | MINIMUM: +3.0% to qualify
```

**This is the only EV constraint** - Claude AI determines actual EV values based on analysis

### Typical EV Ranges (from actual predictions)

```
Most games:         3-10% EV per bet
Good matchups:      10-15% EV per bet
Exceptional games:  15-33% EV per bet

Example distribution (11 games analyzed):
- 3.0-7.0%:  7 games (typical)
- 8.0-15.0%: 2 games (good)
- 13.9-33.1%: 2 games (exceptional)
```

### Kelly Criterion

**Formula**:
```
Kelly % = (True Prob × Decimal Odds - 1) / (Decimal Odds - 1)
```

**Full Kelly**: Maximum growth stake (aggressive)
**Half Kelly**: Conservative recommendation (used in predictions)

**Example**:
- Bet: Joe Burrow Over 250.5 Passing Yards
- Odds: +150 (2.50 decimal)
- True Probability: 58%
- EV: (0.58 × 2.50) - 1 = 8.5%
- Full Kelly: 29.3% of bankroll
- Half Kelly: 14.7% of bankroll (recommended)

---

## API Configuration

### Claude Sonnet 4.5

**Model ID**: `claude-sonnet-4-5-20250929`
**Context Window**: 200K tokens
**Pricing**:
- Input: $3.00 per 1M tokens
- Output: $15.00 per 1M tokens

**Typical Usage Per Prediction**:
- Input tokens: 36K-42K
- Output tokens: 600-800
- Cost: $0.10-$0.15

**Token Breakdown**:
- Rankings: ~3K tokens
- Profiles (2 teams): ~8K tokens each
- Odds: ~500-1500 tokens
- Prompt templates: ~2K tokens

**Rate Limiting**:
- Default: 1 second delay between requests
- Configurable in `shared/config/api_config.py`

---

## Adding New Sports

### Step-by-Step Guide

1. **Create sport configuration**
   ```python
   # {sport}/{sport}_config.py
   class NHLConfig(SportConfig):
       sport_name = "nhl"
       data_dir = "nhl/data"
       rankings_url = "https://..."
       # Define RANKING_TABLES, TEAM_PROFILE_TABLES, etc.
   ```

2. **Create prompt components**
   ```python
   # {sport}/prompt_components.py
   BET_TYPES = """
   - Player Points (Over/Under)
   - Team Total Goals (Over/Under)
   ...
   """
   ```

3. **Create analyzer (if custom P&L logic needed)**
   ```python
   # {sport}/{sport}_analyzer.py
   class NHLAnalyzer(BaseAnalyzer):
       # Customize if needed, or use base class
   ```

4. **Create teams file**
   ```python
   # {sport}/teams.py
   TEAMS = [
       {
           "name": "Boston Bruins",
           "abbreviation": "BOS",
           "pfr_abbr": "bos"
       },
       ...
   ]
   ```

5. **Register sport**
   ```python
   # shared/register_sports.py
   from nhl.nhl_config import NHLConfig
   SportFactory.register("nhl", NHLConfig)
   ```

6. **Create CLI utilities**
   ```python
   # {sport}/cli_utils/predict.py
   # {sport}/cli_utils/fetch_results.py
   # {sport}/cli_utils/fetch_odds.py
   ```

---

## Streamlit Dashboard

**Location**: `streamlit/app.py`

**Features**:
- View all predictions across dates
- Filter by date range and status
- Interactive profit charts (Plotly)
- Bet-by-bet analysis overlay
- Win rate and ROI metrics

**Component Architecture** (recent refactor):
```
streamlit/
├── components/
│   ├── filters.py           # Date/status filtering
│   ├── charts.py            # Profit visualizations
│   ├── predictions_table.py # Predictions display
│   └── analysis_overlay.py  # P&L details
├── app.py                   # Main dashboard
└── theme.py                 # Custom CSS
```

**Usage**:
```bash
streamlit run streamlit/app.py
```

---

## Key Technical Details

### Why PFR Abbreviations?

Pro-Football-Reference is the primary data source for:
- Rankings
- Team profiles
- Boxscores
- Player stats

Using PFR abbreviations internally:
- Simplifies URL construction
- Ensures consistency across all data
- Only convert at boundaries (DraftKings input)

### Token Optimization

**Average Prediction**:
- Total tokens: 36K-42K
- Well within 200K context window
- Cost: ~$0.10-$0.15 per prediction

**Breakdown**:
- 6 ranking tables: ~3K tokens
- 2 team profiles (8 tables each): ~16K tokens
- Odds data: ~500-1500 tokens
- Prompt templates: ~2K tokens

### Error Handling Strategy

1. **Odds Fetching**: Automatic abbreviation conversion, clear error messages
2. **Odds Loading**: Returns None if missing, prediction flow validates
3. **Metadata**: Auto-migration of old formats, adds missing fields
4. **Scraping**: Rate limiting, retry logic, timeout handling

### Backward Compatibility

**Old predictions metadata** (string format):
```json
{"2025-10-27_kan_was": "2025-10-27"}
```

**Auto-migrates to** (dict format):
```json
{
  "2025-10-27_kan_was": {
    "last_predicted": "2025-10-27",
    "results_fetched": false,
    "odds_used": false,
    "game_date": "2025-10-27",
    ...
  }
}
```

---

## Summary

This architecture provides:

✅ **EV+ Focus**: Mathematical edge identification with +3% minimum threshold
✅ **Kelly Criterion**: Optimal stake sizing for bankroll management
✅ **Complete Lifecycle**: Prediction → Results → P&L analysis
✅ **Clean Architecture**: Services, repositories, clean separation
✅ **Multi-Sport Ready**: Easy to add NHL, MLB, etc.
✅ **Database Ready**: Repository pattern enables easy migration
✅ **Cost Efficient**: ~$0.10-$0.15 per prediction with Claude Sonnet 4.5
✅ **Automated Pipeline**: Smart caching, auto-scraping, metadata tracking
✅ **Transparent**: All data and reasoning preserved in files

**File Organization**: Consistent naming across all data types
**Metadata System**: Complete lifecycle tracking for every game
**EV Analysis**: Rigorous methodology with market odds integration
**P&L Tracking**: Actual performance validation with ROI metrics
