# Sports Betting Analytics Platform - Architecture Guide

## Quick Reference

### File Naming Conventions

All files follow the pattern: `{HOME_ABBR}_{AWAY_ABBR}.json` (home team first, lowercase PFR abbreviations)

```
Predictions:  sports/nfl/data/predictions/2025-11-02/cin_chi.json
Results:      sports/nfl/data/results/2025-11-02/cin_chi.json
Analysis:     sports/nfl/data/analysis/2025-11-02/cin_chi.json
Odds:         sports/nfl/data/odds/2025-11-02/cin_chi.json
```

### Team Abbreviations

**PFR (Pro-Football-Reference)**: Used throughout the system
- Format: 3 letters, lowercase
- Examples: `kan` (KC Chiefs), `was` (Washington), `rav` (Baltimore), `sdg` (LA Chargers)
- Source: `sports/nfl/teams.py` -> TEAMS dict -> `pfr_abbr` field

**DraftKings**: Only used during odds fetching
- Format: 2-3 uppercase letters
- Automatically converted to PFR abbreviations when saving

### Common Commands

```bash
# Start CLI
poetry run python cli.py

# Streamlit Dashboard
streamlit run frontend/app.py

# Run tests
poetry run pytest
```

---

## Project Structure

```
betting-ss/
├── services/                    # Backend services (OOP architecture)
│   ├── cli/                     # Workflow orchestration
│   │   ├── orchestrator.py      # CLIOrchestrator - coordinates all workflows
│   │   ├── config.py            # CLI service configuration
│   │   └── tests/
│   ├── odds/                    # Betting odds management
│   │   ├── service.py           # OddsService - fetch/load/manage odds
│   │   ├── scraper.py           # OddsScraper - DraftKings extraction
│   │   ├── parser.py            # Parse odds into Odds model
│   │   ├── config.py            # Odds service configuration
│   │   └── tests/
│   ├── prediction/              # Prediction generation
│   │   ├── service.py           # PredictionService - orchestrates predictions
│   │   ├── ev_predictor.py      # EVPredictor - statistical EV analysis
│   │   ├── ai_predictor.py      # AIPredictor - Claude API predictions
│   │   ├── config.py            # Prediction service configuration
│   │   └── tests/
│   ├── results/                 # Game results fetching
│   │   ├── service.py           # ResultsService - fetch/save results
│   │   ├── fetcher.py           # ResultsFetcher - scrapes boxscores
│   │   ├── parser.py            # Parse boxscore HTML into results
│   │   ├── config.py            # Results service configuration
│   │   └── tests/
│   └── analysis/                # P&L analysis
│       ├── service.py           # AnalysisService - compare predictions vs results
│       ├── bet_checker.py       # BetChecker - determine bet wins/losses
│       ├── config.py            # Analysis service configuration
│       └── tests/
│
├── shared/                      # Cross-sport infrastructure
│   ├── base/                    # Abstract interfaces
│   │   ├── sport_config.py      # SportConfig interface (abstract)
│   │   ├── predictor.py         # Base prediction logic
│   │   ├── analyzer.py          # Base analysis logic
│   │   └── prompt_builder.py    # Prompt template builder
│   ├── models/                  # Data models
│   │   ├── bet.py               # Bet dataclass with BetType, BetOutcome enums
│   │   ├── odds.py              # Odds dataclass
│   │   ├── prediction.py        # Prediction dataclass
│   │   ├── result.py            # Result dataclass
│   │   ├── ev_calculator.py     # EVCalculator - main EV computation engine
│   │   ├── stat_aggregator.py   # Aggregate team stats from profiles/rankings
│   │   └── probability_calculator.py  # Calculate probabilities from stats
│   ├── repositories/            # Data access layer (JSON -> DB ready)
│   │   ├── base_repository.py   # BaseRepository abstraction
│   │   ├── odds_repository.py   # Load/save odds JSON
│   │   ├── prediction_repository.py
│   │   ├── results_repository.py
│   │   └── analysis_repository.py
│   ├── config/                  # Configuration management
│   │   ├── api_config.py        # Claude API settings
│   │   ├── paths_config.py      # Path templates
│   │   └── scraping_config.py   # Rate limits, browser config
│   ├── utils/                   # Utilities
│   │   ├── console_utils.py     # CLI formatting (Rich panels, tables)
│   │   ├── validation_utils.py  # Input validation
│   │   ├── web_scraper.py       # Playwright web scraping
│   │   ├── bet_result_checker.py # Programmatic bet outcome checking
│   │   └── player_game_log.py   # Recent form (last 5 games)
│   ├── errors/                  # Error handling
│   │   └── exceptions.py        # Custom exception classes
│   └── logging/                 # Structured logging
│       └── logger.py
│
├── sports/                      # Sport-specific implementations
│   ├── nfl/
│   │   ├── nfl_config.py        # NFLConfig implements SportConfig
│   │   ├── teams.py             # 32 NFL teams with PFR abbreviations
│   │   ├── constants.py         # NFL URLs, table configs
│   │   ├── nfl_results_fetcher.py
│   │   ├── odds_scraper.py      # DraftKings parsing for NFL
│   │   ├── prompt_components.py # NFL-specific prompts
│   │   └── data/
│   │       ├── rankings/        # League-wide stats (6 tables)
│   │       ├── profiles/        # Team-specific data (8 tables/team)
│   │       ├── predictions/     # Game predictions
│   │       ├── predictions_ev/  # EV-only predictions
│   │       ├── odds/            # DraftKings odds by date
│   │       ├── results/         # Game results from boxscores
│   │       └── analysis/        # P&L analysis files
│   └── nba/
│       └── (parallel structure)
│
├── frontend/                    # Streamlit dashboard
│   ├── app.py                   # Main application
│   ├── config.py                # Dashboard configuration
│   ├── theme.py                 # Custom CSS styling
│   ├── components/
│   │   ├── header.py            # Header with title/branding
│   │   ├── filter_dock.py       # Date/status filtering
│   │   ├── prediction_card.py   # Individual prediction display
│   │   ├── metrics_section.py   # Performance metrics
│   │   └── charts.py            # Profit/loss visualizations
│   ├── utils/
│   │   ├── data_loader.py       # Load predictions and analyses
│   │   ├── analysis_helpers.py  # Compute metrics
│   │   └── colors.py            # Color utilities
│   └── tests/
│
├── config/                      # YAML configuration
│   └── settings.yaml            # Scraping, API, paths config
│
├── logs/                        # Service log files
├── cli.py                       # CLI entry point
└── pyproject.toml
```

---

## Services Architecture

The platform uses a **service-oriented architecture** with 5 specialized services:

### CLIOrchestrator

**Location**: `services/cli/orchestrator.py`

Master workflow coordinator that lazy-loads and orchestrates all other services.

```python
CLIOrchestrator
├── sport (nfl/nba)
├── config (WorkflowConfig + DisplayConfig)
├── Lazy-loaded services:
│   ├── odds_service (OddsService)
│   ├── prediction_service (PredictionService)
│   ├── results_service (ResultsService)
│   └── analysis_service (AnalysisService)
└── Methods:
    ├── fetch_odds_workflow()
    ├── prediction_workflow()
    ├── fetch_results_workflow()
    └── analysis_workflow()
```

### OddsService

**Location**: `services/odds/service.py`

Fetches betting odds from DraftKings, validates and saves odds data.

- Fetches HTML from DraftKings game pages via Playwright
- Extracts game lines (moneyline, spread, total)
- Extracts player props with multiple milestones
- Converts DraftKings abbreviations to PFR format

### PredictionService

**Location**: `services/prediction/service.py`

Orchestrates the dual prediction system (EV Calculator + AI).

- Runs both prediction systems for each game
- Compares results and selects best predictions
- Saves predictions to disk

### ResultsService

**Location**: `services/results/service.py`

Fetches game results from Pro-Football-Reference boxscores.

- Scrapes boxscore tables
- Extracts final scores and player stats
- Parses into structured Result objects

### AnalysisService

**Location**: `services/analysis/service.py`

Compares predictions against actual results for P&L calculation.

- Uses `bet_result_checker.py` to programmatically check bet outcomes
- Calculates profit/loss per bet
- Generates summary metrics (ROI, win rate)

---

## Data Flow Pipeline

```
User Input (CLI)
    │
    v
CLIOrchestrator
    │
    ├──> OddsService.fetch_from_url()
    │    └──> Save: sports/{sport}/data/odds/{date}/{home}_{away}.json
    │
    ├──> PredictionService.predict_game()
    │    ├──> EVPredictor (statistical analysis, free)
    │    │    ├──> StatAggregator (load profiles/rankings)
    │    │    ├──> ProbabilityCalculator (compute true probabilities)
    │    │    ├──> EVCalculator (compute expected value)
    │    │    └──> Save: sports/{sport}/data/predictions_ev/{date}/...
    │    │
    │    └──> AIPredictor (Claude API, paid, optional)
    │         ├──> Build comprehensive prompt
    │         ├──> Call Claude Sonnet 4.5
    │         └──> Save: sports/{sport}/data/predictions/{date}/...
    │
    ├──> ResultsService.fetch_game_result()
    │    └──> Save: sports/{sport}/data/results/{date}/{home}_{away}.json
    │
    └──> AnalysisService.analyze_game()
         ├──> BetResultChecker (programmatic bet checking)
         └──> Save: sports/{sport}/data/analysis/{date}/{home}_{away}.json
```

---

## Dual Prediction System

### EV Calculator (Fast, Free)

**Location**: `services/prediction/ev_predictor.py` + `shared/models/ev_calculator.py`

Statistical prediction engine using team/player data.

**Process**:
1. Load team profiles and rankings from disk
2. Aggregate player stats (averages, recent form)
3. Apply defense adjustments (opponent strength)
4. Calculate true probability for each bet
5. Compute EV = (True Prob × Decimal Odds) - 1
6. Filter to +3% EV minimum threshold
7. Return top N bets

**Performance**: ~500ms per game, no API cost

### AI Predictor (Slow, Paid)

**Location**: `services/prediction/ai_predictor.py`

Claude Sonnet 4.5-powered analysis.

**Process**:
1. Build comprehensive prompt with:
   - Team rankings (6 tables)
   - Team profiles (8 tables per team)
   - Betting odds
   - EV methodology instructions
2. Call Claude API
3. Parse structured bet recommendations
4. Calculate cost from token usage

**Performance**: ~30 seconds per game, ~$0.10-0.15 cost

### Dual Mode

When running dual predictions:
1. Run both systems for the same game
2. Compare outputs (EV vs AI)
3. Save both separately with `_ev` and `_ai` suffixes
4. Generate comparison file

---

## Models & Repositories

### Data Models (`shared/models/`)

| Model | Purpose |
|-------|---------|
| `Bet` | Single betting opportunity with odds, line, EV edge |
| `Odds` | Game odds from DraftKings (lines + player props) |
| `Prediction` | Collection of bets for a game |
| `Result` | Game result with final score and stats |
| `Analysis` | P&L analysis comparing predictions to results |

### Repositories (`shared/repositories/`)

Abstract data access layer enabling future database migration.

```python
# Example usage
from shared.repositories import OddsRepository

odds_repo = OddsRepository("nfl")
odds_data = odds_repo.load(date="2025-11-02", home="cin", away="chi")
odds_repo.save(odds_data, date="2025-11-02", home="cin", away="chi")
```

---

## Frontend Dashboard

**Location**: `frontend/app.py`

Streamlit-based web UI for viewing predictions and analysis.

### Components

| Component | Purpose |
|-----------|---------|
| `header.py` | App title and branding |
| `filter_dock.py` | Date range and status filters |
| `prediction_card.py` | Display individual predictions |
| `metrics_section.py` | ROI, win rate, avg EV metrics |
| `charts.py` | Profit/loss visualizations (Plotly) |

### Features

- View all predictions across dates
- Filter by date range, status (Analyzed, Pending)
- Interactive profit charts
- Bet-by-bet analysis overlay
- Performance metrics dashboard

---

## Configuration

### settings.yaml

```yaml
api:
  model: "claude-sonnet-4-5-20250929"
  max_tokens: 2048

paths:
  data_root: "sports/{sport}/data"
  predictions: "{data_root}/predictions"
  results: "{data_root}/results"
  analysis: "{data_root}/analysis"
  odds: "{data_root}/odds"

scraping:
  rate_limit_ms: 1000
  timeout_ms: 30000
```

### Per-Service Configs

Each service has its own `config.py` with dataclass configuration:

```python
@dataclass
class OddsConfig:
    """Configuration for OddsService."""
    sport: str = "nfl"
    source: str = "draftkings"
    timeout: int = 30000
```

---

## Adding New Sports

1. **Create sport configuration**
   ```python
   # sports/{sport}/{sport}_config.py
   class NHLConfig(SportConfig):
       sport_name = "nhl"
       data_dir = "sports/nhl/data"
       # Define RANKING_TABLES, TEAM_PROFILE_TABLES, etc.
   ```

2. **Create teams file**
   ```python
   # sports/{sport}/teams.py
   TEAMS = [
       {"name": "Boston Bruins", "abbreviation": "BOS", "pfr_abbr": "bos"},
       ...
   ]
   ```

3. **Create prompt components**
   ```python
   # sports/{sport}/prompt_components.py
   BET_TYPES = """
   - Player Points (Over/Under)
   - Team Total Goals (Over/Under)
   ...
   """
   ```

4. **Register sport**
   ```python
   # shared/register_sports.py
   from sports.nhl.nhl_config import NHLConfig
   SportFactory.register("nhl", NHLConfig)
   ```

---

## EV+ Analysis Methodology

### Minimum EV Threshold

**Hardcoded**: +3% minimum expected value

Only bets with EV >= 3% are included in predictions.

### EV Calculation

```
EV = (True Probability × Decimal Odds) - 1

Example:
- Bet: Player Over 250.5 Passing Yards
- Odds: +150 (2.50 decimal)
- True Probability: 58%
- EV: (0.58 × 2.50) - 1 = 0.45 = 45%
```

### Probability Calculation

True probabilities are calculated from:
- Player averages (season stats)
- Recent form (last 5 games)
- Opponent defense ranking
- Home/away adjustment
- Injury impact

---

## API Configuration

### Claude Sonnet 4.5

- **Model ID**: `claude-sonnet-4-5-20250929`
- **Context Window**: 200K tokens
- **Pricing**: $3.00/MTok input, $15.00/MTok output

**Typical Usage Per Prediction**:
- Input tokens: 36K-42K
- Output tokens: 600-800
- Cost: $0.10-$0.15

---

## Technical Debt / Future Work

### Large Files (>500 lines)

| File | Lines | Notes |
|------|-------|-------|
| `frontend/theme.py` | 851 | CSS configuration, consider extracting |
| `shared/utils/bet_result_checker.py` | 704 | Mixed concerns |
| `shared/models/stat_aggregator.py` | 641 | Multiple responsibilities |
| `shared/base/analyzer.py` | 612 | Dual-system logic could be separated |
| `shared/models/probability_calculator.py` | 604 | Multiple models bundled |
| `shared/models/ev_calculator.py` | 603 | Complex orchestration |

---

## Summary

This architecture provides:

- **EV+ Focus**: Mathematical edge identification with +3% minimum
- **Dual Predictions**: Statistical (free) + AI (paid) systems
- **Complete Lifecycle**: Odds -> Predictions -> Results -> Analysis
- **Service Architecture**: 5 independent, testable services
- **Multi-Sport Ready**: Easy to add NHL, MLB, etc.
- **Database Ready**: Repository pattern enables easy migration
- **294 Tests**: Comprehensive test coverage
