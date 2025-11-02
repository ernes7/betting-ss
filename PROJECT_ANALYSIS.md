# Sports Betting Prediction Project - Comprehensive Analysis

## 1. PROJECT STRUCTURE OVERVIEW

### Directory Architecture

```
betting-ss/
├── nfl/                          # NFL-specific implementation
│   ├── cli_utils/
│   │   ├── predict.py           # NFL prediction CLI command
│   │   ├── fetch_results.py     # NFL results fetching CLI command
│   │   └── fetch_odds.py        # NEW: NFL odds scraping CLI command
│   ├── nfl_config.py            # NFL-specific configuration
│   ├── nfl_analyzer.py          # NFL-specific analysis
│   ├── nfl_results_fetcher.py   # NFL results extraction implementation
│   ├── odds_scraper.py          # NFL odds extraction from DraftKings HTML
│   ├── constants.py             # NFL constants
│   ├── teams.py                 # NFL team metadata
│   ├── prompt_components.py     # NFL prompt templates
│   └── data/
│       ├── rankings/            # Pro-Football-Reference rankings (team offense, etc)
│       ├── profiles/            # Team-specific profile data (injury reports, schedule, stats)
│       ├── predictions/         # Generated predictions (markdown + JSON)
│       ├── results/             # Game results (final scores, stats tables)
│       ├── analysis/            # Prediction accuracy analysis (AI-generated)
│       └── odds/                # Betting odds (DraftKings HTML extracted to JSON)
│
├── nba/                          # NBA-specific implementation (similar structure)
│   ├── cli_utils/
│   │   ├── predict.py
│   │   └── fetch_results.py
│   ├── nba_config.py
│   ├── nba_analyzer.py
│   ├── nba_results_fetcher.py
│   ├── constants.py
│   ├── teams.py
│   └── data/ (same structure as NFL)
│
├── shared/                       # Shared code for all sports
│   ├── base/
│   │   ├── predictor.py         # Base prediction logic (loads rankings/profiles, calls Claude)
│   │   ├── scraper.py           # Base scraping logic (rankings + profiles)
│   │   ├── analyzer.py          # Base analysis logic (prediction vs results)
│   │   ├── results_fetcher.py   # Base results fetching logic
│   │   ├── sport_config.py      # Abstract sport configuration interface
│   │   ├── prompt_builder.py    # Prompt template building
│   │   └── scraper.py
│   ├── utils/
│   │   ├── metadata_manager.py  # Metadata file tracking (.metadata.json)
│   │   ├── file_manager.py      # JSON file I/O utilities
│   │   ├── web_scraper.py       # Web scraping utilities
│   │   ├── table_extractor.py   # HTML table extraction
│   │   └── data_optimizer.py    # Data optimization utilities
│   ├── factory.py               # SportFactory for creating sport instances
│   └── register_sports.py       # Sport registration
│
├── cli.py                        # Main CLI entry point (sport selection menu)
├── streamlit_app.py            # Streamlit dashboard for viewing results
└── global_constants.py          # Global constants (rate limits, etc)
```

### NBA vs NFL Structure
- **Similar parallel structure**: NBA has equivalent directories and files as NFL
- **Shared base classes**: Both inherit from common base classes in `shared/base/`
- **Sport-specific configuration**: Each implements the `SportConfig` interface
- **Independent data directories**: Completely separate data flows and storage

### Clean Architecture Layers

The project now follows **Clean Architecture** principles with distinct layers:

```
shared/
├── config/                    # Configuration Layer
│   ├── api_config.py         # Claude API settings & cost calculation
│   ├── scraping_config.py    # Rate limits & browser config
│   └── paths_config.py       # Path templates & builders
│
├── services/                  # Service Layer (Business Logic)
│   ├── team_service.py       # Team operations (select, abbreviate)
│   ├── metadata_service.py   # Metadata load/save operations
│   ├── profile_service.py    # Profile loading with auto-scraping
│   └── odds_service.py       # Odds loading operations
│
├── repositories/              # Repository Layer (Data Access)
│   ├── base_repository.py    # Abstract JSON operations
│   ├── prediction_repository.py  # Prediction data access
│   ├── results_repository.py     # Results data access
│   ├── odds_repository.py        # Odds data access
│   └── analysis_repository.py    # Analysis data access
│
└── utils/                     # Utility Layer
    ├── console_utils.py      # 16 reusable CLI formatting functions
    └── validation_utils.py   # 9 validation functions
```

**Key Benefits:**
- **No Code Duplication**: All CLI files use shared services
- **Easy to Test**: Services are mockable, repositories are injectable
- **Database-Ready**: Repository pattern enables easy migration from JSON to DB
- **Sport-Agnostic**: Same services work for NFL, NBA, and future sports
- **Consistent UX**: Unified console output and error handling

**Example Usage in CLI Files:**
```python
# Old way (manual, duplicated everywhere)
with open(f"nfl/data/odds/{date}/{home}_{away}.json") as f:
    odds_data = json.load(f)

# New way (service layer)
from shared.services import OddsService
odds_service = OddsService("nfl")
odds_data = odds_service.load_odds_for_game(date, team_a, team_b, home)
```

---

## 2. PREDICTION PIPELINE - DATA FLOW

### Complete Flow: From Setup to Prediction

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. FETCH RANKINGS (One-time daily, happens automatically)           │
├─────────────────────────────────────────────────────────────────────┤
│ Source: Pro-Football-Reference (PFR)                                │
│ Scraper: shared/base/scraper.py → extract_rankings()               │
│ Config: nfl/nfl_config.py → RANKING_TABLES                          │
│ Output: nfl/data/rankings/{table_name}.json                         │
│ - team_offense.json                                                 │
│ - passing_offense.json                                              │
│ - rushing_offense.json                                              │
│ - scoring_offense.json                                              │
│ - afc_standings.json                                                │
│ - nfc_standings.json                                                │
│ Metadata: nfl/data/rankings/.metadata.json (tracks "last_scraped")  │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 2. FETCH TEAM PROFILES (On demand, one per team, cached if today)  │
├─────────────────────────────────────────────────────────────────────┤
│ Source: Pro-Football-Reference (PFR) team pages                     │
│ Scraper: shared/base/scraper.py → extract_team_profile()           │
│ Input: Team name (e.g., "Kansas City Chiefs")                       │
│ Config: nfl/nfl_config.py → TEAM_PROFILE_TABLES                     │
│ Output: nfl/data/profiles/{team_name}/                              │
│ - injury_report.json                                                │
│ - team_stats.json                                                   │
│ - schedule_results.json                                             │
│ - passing.json                                                      │
│ - rushing_receiving.json                                            │
│ - defense_fumbles.json                                              │
│ - scoring_summary.json                                              │
│ - touchdown_log.json                                                │
│ Metadata: nfl/data/profiles/.metadata.json (tracks team scrape date)│
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 3. GENERATE PREDICTION (Claude AI)                                  │
├─────────────────────────────────────────────────────────────────────┤
│ User Input: Team A, Team B, Home Team, Game Date                    │
│ Loader: nfl/cli_utils/predict.py → load_team_profiles()            │
│         + load_ranking_tables()                                     │
│ Processor: shared/base/predictor.py → generate_parlays()            │
│ Action:                                                             │
│   1. Load rankings data (all 6 ranking tables)                      │
│   2. Load both team profiles (all 8 profile tables each)            │
│   3. Extract team stats from rankings using team name lookup        │
│   4. Build prompt with:                                             │
│      - Sport-specific components (prompt_components.py)             │
│      - Team stats from rankings                                     │
│      - Team profile data                                            │
│      - Game context (home/away, date)                               │
│   5. Call Claude API (claude-sonnet-4-5-20250929)                   │
│   6. Return prediction text, cost, tokens                           │
│ Output: Prediction markdown + JSON files                            │
│   - nfl/data/predictions/{game_date}/{home_abbr}_{away_abbr}.md    │
│   - nfl/data/predictions/{game_date}/{home_abbr}_{away_abbr}.json  │
│ Metadata: nfl/data/predictions/.metadata.json                       │
│   Key format: "{game_date}_{home_abbr}_{away_abbr}"                │
│   Tracks: last_predicted, results_fetched, game_date, teams, etc   │
└─────────────────────────────────────────────────────────────────────┘
```

### Predict Game Function (nfl/cli_utils/predict.py)
Main entry point: `predict_game()`

```python
predict_game()
  ├─ 1. Prompt for game details:
  │    ├─ game_date (default: today)
  │    ├─ team_a (arrow key selection from TEAMS)
  │    └─ team_b, home_team
  │
  ├─ 2. Check if game was already predicted today:
  │    ├─ Load predictions metadata (.metadata.json)
  │    ├─ If found, display existing prediction and return
  │    └─ Else, continue to generate new prediction
  │
  ├─ 3. Auto-fetch fresh ranking data:
  │    ├─ Check if rankings scraped today
  │    ├─ If not, call nfl_sport.scraper.extract_rankings()
  │    └─ Load all ranking tables
  │
  ├─ 4. Load team profiles:
  │    ├─ For each team:
  │    │  ├─ Check if team was scraped today (metadata)
  │    │  ├─ If not, call nfl_sport.scraper.extract_team_profile()
  │    │  └─ Load all profile tables from directory
  │    └─ Validate both profiles loaded successfully
  │
  ├─ 5. Generate parlays:
  │    ├─ Call nfl_sport.predictor.generate_parlays()
  │    └─ This invokes Claude API with all data
  │
  ├─ 6. Save results:
  │    ├─ save_prediction_to_markdown() → .md file
  │    ├─ save_prediction_to_markdown() → .json file (also)
  │    └─ Update predictions metadata
  │
  └─ 7. Display to user with markdown rendering
```

---

## 3. METADATA FILES - TRACKING AND COORDINATION

### Three Metadata Files

#### A. Rankings Metadata (`nfl/data/rankings/.metadata.json`)
```json
{
  "last_scraped": "2025-10-26"
}
```
- **Purpose**: Prevent multiple daily scrapes of rankings
- **Updated by**: `shared/base/scraper.py` → `extract_rankings()`
- **Used by**: `nfl/cli_utils/predict.py` → checks if needs fresh data
- **Format**: Simple date string

#### B. Profiles Metadata (`nfl/data/profiles/.metadata.json`)
```json
{
  "team_folder_name": "2025-10-26",
  "another_team": "2025-10-26",
  ...
}
```
- **Purpose**: Track which teams were scraped today (per-team tracking)
- **Updated by**: `nfl/cli_utils/predict.py` → `save_metadata()` after extraction
- **Used by**: `nfl/cli_utils/predict.py` → `was_scraped_today()` check
- **Format**: Key = team folder name (lowercase with underscores), Value = date string

#### C. Predictions Metadata (`nfl/data/predictions/.metadata.json`)
```json
{
  "2025-10-27_kc_was": {
    "last_predicted": "2025-10-26",
    "results_fetched": true,
    "game_date": "2025-10-27",
    "teams": ["Washington Commanders", "Kansas City Chiefs"],
    "home_team": "Kansas City Chiefs",
    "home_team_abbr": "kan",
    "results_fetched_at": "2025-10-28 11:13:37",
    "analysis_generated": true,
    "analysis_generated_at": "2025-10-28 11:14:24"
  },
  ...
}
```
- **Purpose**: Track predictions, results fetching, and analysis status
- **Updated by**: 
  - `nfl/cli_utils/predict.py` → after saving prediction
  - `nfl/cli_utils/fetch_results.py` → after fetching results
  - Analysis generation (future)
- **Game Key Format**: `{game_date}_{home_team_abbr}_{away_team_abbr}`
  - Example: `2025-10-27_kc_was`
  - Home team FIRST in key
- **Field Meanings**:
  - `last_predicted`: When prediction was generated
  - `results_fetched`: Boolean flag - true if results have been fetched
  - `game_date`: YYYY-MM-DD format
  - `teams`: [away_team, home_team] - full names
  - `home_team`: Full name of home team
  - `home_team_abbr`: PFR abbreviation (for building boxscore URL)
  - `results_fetched_at`: Timestamp when results were fetched
  - `analysis_generated`: Boolean flag
  - `analysis_generated_at`: Timestamp when analysis was generated

---

## 4. ODDS FILES - NAMING AND STORAGE (NEW FEATURE)

### Odds Scraper (nfl/odds_scraper.py)
- **Source**: DraftKings HTML files
- **Input**: Local path to HTML file (downloaded from DraftKings)
- **Process**: `NFLOddsScraper.extract_odds(html_path)`
  - Parses JavaScript data from HTML
  - Extracts game lines (moneyline, spread, total)
  - Extracts player props (all milestone formats)
  - Fixes team references (AWAY/HOME → actual abbreviations)

### Odds File Naming and Storage (nfl/cli_utils/fetch_odds.py)
```
Directory: nfl/data/odds/{YYYY-MM-DD}/
Filename: {AWAY_ABBR}_vs_{HOME_ABBR}.json

Example: nfl/data/odds/2025-10-31/BAL_vs_MIA_full.json
```

- **Date Extraction**: Parsed from odds data's `game_date` field
- **Team Abbreviations**: From DraftKings data (not PFR abbreviations)
  - Example: BAL (Ravens), MIA (Dolphins)
- **Naming Convention**: Away team abbreviation first

### Odds File Structure
```json
{
  "sport": "nfl",
  "teams": {
    "away": {"name": "BAL Ravens", "abbr": "BAL"},
    "home": {"name": "MIA Dolphins", "abbr": "MIA"}
  },
  "game_date": "2025-10-31T00:15:00.0000000Z",
  "fetched_at": "2025-10-30T01:17:00.125866",
  "source": "draftkings",
  
  "game_lines": {
    "moneyline": {"away": -440, "home": 340},
    "spread": {
      "away": -7.5, "away_odds": -110,
      "home": 7.5, "home_odds": -110
    },
    "total": {
      "line": 51.5,
      "over": -108,
      "under": -112
    }
  },
  
  "player_props": [
    {
      "player": "Zay Flowers",
      "team": "BAL",
      "position": null,
      "props": [
        {
          "market": "receiving_yards",
          "milestones": [
            {"line": 15, "odds": -3600},
            {"line": 25, "odds": -1220},
            ...
          ]
        }
      ]
    },
    ...
  ]
}
```

### Command: Fetch Odds
```python
fetch_odds_command()  # nfl/cli_utils/fetch_odds.py
  ├─ Prompt user for DraftKings HTML file path
  ├─ Create NFLOddsScraper instance
  ├─ Call scraper.extract_odds(html_path)
  ├─ Display summary (game lines, player props count, sample milestones)
  └─ Save to nfl/data/odds/{date}/{teams}.json
```

---

## 5. PREDICTIONS FILES - NAMING AND USAGE

### Predictions File Naming
```
Directory: nfl/data/predictions/{YYYY-MM-DD}/
Markdown: {HOME_ABBR}_{AWAY_ABBR}.md
JSON: {HOME_ABBR}_{AWAY_ABBR}.json

Example: 
  - nfl/data/predictions/2025-10-27/kc_was.md
  - nfl/data/predictions/2025-10-27/kc_was.json
```

- **Abbreviation Format**: Lowercase (e.g., `kc`, `was`)
- **Home Team First**: Filename reflects home team as first abbreviation
- **Metadata Tracking**: Game key in metadata matches: `2025-10-27_kc_was`

### Predictions JSON Structure
```json
{
  "sport": "nfl",
  "teams": ["Washington Commanders", "Kansas City Chiefs"],
  "home_team": "Kansas City Chiefs",
  "date": "2025-10-27",
  "generated_at": "2025-10-26 20:32:32",
  "model": "claude-sonnet-4-5-20250929",
  "api_cost": 0.119,
  "tokens": {
    "input": 36181,
    "output": 698,
    "total": 36879
  },
  "parlays": [
    {
      "name": "Parlay 1: Washington Commanders Wins",
      "confidence": 92,
      "bets": [
        "Washington Commanders Moneyline",
        "Marcus Mariota Over 185.5 passing yards",
        ...
      ],
      "reasoning": "If Washington pulls the upset...",
      "odds": null
    },
    ...
  ]
}
```

### Load Predictions Flow
1. **Game Key Generation** (metadata.json key):
   - Format: `{game_date}_{home_abbr}_{away_abbr}`
   - Example: `2025-10-27_kc_was`
   
2. **File Path Construction**:
   - Given: game_key `2025-10-27_kc_was`, game_date `2025-10-27`
   - Filename: `kc_was.json` (remove date prefix from key)
   - Path: `nfl/data/predictions/2025-10-27/kc_was.json`

3. **Reuse Detection**:
   - Check metadata for today's predictions
   - If found and exists, load and display from file
   - Prevents redundant API calls same day

---

## 6. RANKINGS AND PROFILES LOADING

### Rankings Loading (shared/base/predictor.py)
```python
load_ranking_tables()
  └─ FileManager.load_all_json_in_dir(config.data_rankings_dir)
     └─ Returns: {
          "team_offense": {...},
          "passing_offense": {...},
          "rushing_offense": {...},
          "scoring_offense": {...},
          "afc_standings": {...},
          "nfc_standings": {...}
        }
```

**File Format**: Each table has structure:
```json
{
  "table_name": "Team Offensive Statistics",
  "headers": ["rank", "team", "games", "points", "yards", ...],
  "data": [
    {"team": "Kansas City Chiefs", "rank": 1, "points": 234, ...},
    {"team": "Buffalo Bills", "rank": 2, ...},
    ...
  ]
}
```

### Team Extraction from Rankings
```python
get_team_from_rankings(rankings, team_name)
  └─ Searches all ranking tables for matching team
  └─ Returns: {
       "team_offense": {...row for this team...},
       "passing_offense": {...row for this team...},
       "rushing_offense": {...},
       ...
     }
```

### Team Profiles Loading (nfl/cli_utils/predict.py)
```python
load_team_profiles(team_a, team_b)
  ├─ For each team:
  │  ├─ Check metadata for today's scrape
  │  ├─ If not scraped: call scraper.extract_team_profile()
  │  ├─ Load all JSON files from profile directory
  │  └─ Return: {
  │       "team_folder": {
  │         "injury_report": {...},
  │         "team_stats": {...},
  │         "schedule_results": {...},
  │         "passing": {...},
  │         "rushing_receiving": {...},
  │         "defense_fumbles": {...},
  │         "scoring_summary": {...},
  │         "touchdown_log": {...}
  │       }
  │     }
  └─ Validates both profiles loaded successfully
```

### Combined Data to Claude

The prediction flow combines:
1. **Ranking tables**: League-wide statistics (all teams ranked)
2. **Team profiles**: Detailed team-specific data
3. **Team stats from rankings**: Extracted rows for the two teams
4. **Sport-specific prompts**: Templates with analysis instructions

Example prompt building (shared/base/predictor.py):
```python
generate_parlays(team_a, team_b, home_team, rankings, profile_a, profile_b)
  ├─ Get team_a_stats from rankings (find row by team_a name)
  ├─ Get team_b_stats from rankings (find row by team_b name)
  ├─ Load profile_a data
  ├─ Load profile_b data
  ├─ Build prompt using:
  │  ├─ Sport-specific components (nfl/prompt_components.py)
  │  ├─ Team A stats and profile
  │  ├─ Team B stats and profile
  │  └─ Game context (home/away, date)
  ├─ Call Claude API
  └─ Return: {
       "success": true,
       "prediction": "## Parlay 1: ...",
       "cost": 0.119,
       "model": "claude-sonnet-4-5-20250929",
       "tokens": {"input": 36181, "output": 698, "total": 36879}
     }
```

---

## 7. RESULTS FETCHING FLOW

### Results File Naming
```
Directory: nfl/data/results/{YYYY-MM-DD}/
Filename: {HOME_ABBR}_{AWAY_ABBR}.json

Example: nfl/data/results/2025-10-27/kc_was.json
```

### Results Fetching (nfl/cli_utils/fetch_results.py)
```
fetch_results()
  ├─ 1. Load predictions metadata
  ├─ 2. Prompt user for game date
  ├─ 3. Find all games for that date with results_fetched = false
  ├─ 4. For each game:
  │    ├─ Get home_team_abbr from metadata
  │    ├─ Build boxscore URL: config.build_boxscore_url(date, home_abbr)
  │    │  Format: https://pro-football-reference.com/boxscores/YYYYMMDD0{abbr}.htm
  │    ├─ Extract result: nfl_sport.results_fetcher.extract_game_result()
  │    ├─ Save to file: save_result_to_json()
  │    └─ Update metadata: results_fetched = true
  │
  └─ 5. Display summary: X fetched, Y failed, Z skipped
```

### Results File Structure
```json
{
  "sport": "nfl",
  "game_date": "2025-10-27",
  "teams": {"away": "Commanders", "home": "Chiefs"},
  "final_score": {"away": 7, "home": 28},
  "winner": "Chiefs",
  "boxscore_url": "https://...",
  "fetched_at": "2025-10-28 11:13:34",
  
  "tables": {
    "scoring": {
      "table_name": "Scoring Table",
      "headers": ["quarter", "time", "team", "description", ...],
      "data": [
        {"quarter": "2", "time": "5:46", "team": "Chiefs", ...},
        ...
      ]
    },
    "game_info": {...},
    "team_stats": {...},
    "player_offense": {...},
    "defense": {...},
    "home_starters": {...},
    "away_starters": {...}
  }
}
```

---

## 8. ANALYSIS FLOW

### Analysis File Naming
```
Directory: nfl/data/analysis/{YYYY-MM-DD}/
Filename: {HOME_ABBR}_{AWAY_ABBR}.json

Example: nfl/data/analysis/2025-10-27/kc_was.json
```

### Analysis Generation (shared/base/analyzer.py)
```
generate_analysis(game_key, game_meta)
  ├─ 1. Load prediction JSON (has parlays/bets)
  ├─ 2. Load result JSON (has final score/stats)
  ├─ 3. Build sport-specific analysis prompt
  ├─ 4. Call Claude API with both prediction and result data
  ├─ 5. Parse Claude's JSON response (parlay results, leg accuracy)
  ├─ 6. Add metadata (dates, costs, tokens)
  ├─ 7. Save analysis JSON
  └─ 8. Update predictions metadata: analysis_generated = true
```

### Analysis Output Structure
```json
{
  "parlay_results": [
    {
      "parlay_name": "Parlay 1: Washington Commanders Wins",
      "original_confidence": 92,
      "hit": false,
      "legs_hit": 2,
      "legs_total": 4,
      "hit_rate": 50.0,
      "parlay_reasoning": "This parlay was built around...",
      "legs": [
        {
          "bet": "Washington Commanders Moneyline",
          "hit": false,
          "actual_value": "...",
          "margin": null,
          "reasoning": "..."
        },
        ...
      ]
    }
  ],
  "summary": {
    "parlays_hit": 0,
    "parlays_total": 3,
    "parlay_hit_rate": 0.0,
    "legs_hit": 2,
    "legs_total": 12,
    "legs_hit_rate": 16.7,
    "avg_confidence_hit_parlays": 0.0,
    "avg_confidence_miss_parlays": 94.3,
    "close_misses": 1
  },
  "insights": ["...", "..."]
}
```

---

## 9. ARCHITECTURE PATTERNS

### Factory Pattern (shared/factory.py)
```
SportFactory
  ├─ register(sport_name, config_class)
  │  └─ Registers sport configurations
  ├─ create(sport_name) → Sport instance
  │  └─ Returns Sport with .scraper and .predictor
  └─ available_sports() → list of sports

Sport class (Facade)
  ├─ config: SportConfig
  ├─ scraper: Scraper instance
  └─ predictor: Predictor instance
```

Usage in CLI:
```python
nfl_sport = SportFactory.create("nfl")
nfl_sport.scraper.extract_rankings()
nfl_sport.scraper.extract_team_profile(team_name)
nfl_sport.predictor.generate_parlays(...)
```

### Template Method Pattern (shared/base/scraper.py)
- Base `Scraper` class defines extraction algorithm
- Sport configs provide table mappings and URLs
- Same scraping code works for NFL, NBA, etc.

### Configuration Pattern (SportConfig interface)
- Abstract base defines sport properties
- Each sport implements: NFLConfig, NBAConfig, etc.
- Predictor, Analyzer, ResultsFetcher all use config

---

## 10. KEY DATA RELATIONSHIPS

### Game Key Lifecycle
```
User selects: Team A, Team B, Home Team, Date
    ↓
Generate key: "{date}_{home_abbr}_{away_abbr}"
    ↓
Store in metadata with prediction status
    ↓
Fetch results → update metadata: results_fetched = true
    ↓
Generate analysis → update metadata: analysis_generated = true
    ↓
Metadata now tracks full lifecycle of this game
```

### File Naming Consistency
```
Metadata key:      2025-10-27_kc_was
Prediction files:  nfl/data/predictions/2025-10-27/kc_was.{md,json}
Results file:      nfl/data/results/2025-10-27/kc_was.json
Analysis file:     nfl/data/analysis/2025-10-27/kc_was.json
```

### Team Abbreviation Sources
- **PFR abbreviations** (Pro-Football-Reference): Used for building scraping URLs
  - Example: `kan` (Kansas City), `sdg` (San Diego in 2025), `rav` (Baltimore)
  - Stored in: `nfl/teams.py` → TEAMS → `pfr_abbr`
  
- **DraftKings abbreviations**: Used in odds files
  - Example: `KC` (Kansas City), `BAL` (Baltimore)
  - Comes from odds HTML directly
  
- **Short abbreviations**: Used in file naming
  - Example: `kc`, `was`, `bal`
  - Derived from team names in predictions CLI

---

## 11. DATA FLOW SUMMARY

```
┌──────────────────────────────────────────────────────────────┐
│ STEP 1: INITIALIZE DATA (Happens once or daily)              │
├──────────────────────────────────────────────────────────────┤
│ Rankings    → nfl/data/rankings/.metadata.json               │
│             → nfl/data/rankings/{table}.json (6 files)       │
│                                                               │
│ Profiles    → nfl/data/profiles/.metadata.json               │
│             → nfl/data/profiles/{team}/{table}.json (8 files)│
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│ STEP 2: PREDICT GAME (Per-game, once per day)               │
├──────────────────────────────────────────────────────────────┤
│ Input: Rankings (loaded) + Profiles (loaded)                 │
│ Process: Claude API combines all data                        │
│ Output: nfl/data/predictions/{date}/{home}_{away}.{md,json} │
│         nfl/data/predictions/.metadata.json (updated)        │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│ STEP 3: FETCH ODDS (Ad-hoc, from DraftKings HTML)           │
├──────────────────────────────────────────────────────────────┤
│ Input: DraftKings HTML file                                  │
│ Process: Extract odds, game lines, player props              │
│ Output: nfl/data/odds/{date}/{away}_vs_{home}.json          │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│ STEP 4: FETCH RESULTS (After games complete)                │
├──────────────────────────────────────────────────────────────┤
│ Input: Prediction metadata (finds games needing results)     │
│ Process: Scrape boxscores from PFR                           │
│ Output: nfl/data/results/{date}/{home}_{away}.json           │
│         nfl/data/predictions/.metadata.json (results_fetched)│
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│ STEP 5: ANALYZE ACCURACY (After results fetched)            │
├──────────────────────────────────────────────────────────────┤
│ Input: Prediction JSON + Result JSON                         │
│ Process: Claude API evaluates each bet/leg                   │
│ Output: nfl/data/analysis/{date}/{home}_{away}.json          │
│         nfl/data/predictions/.metadata.json (analysis_gen)   │
└──────────────────────────────────────────────────────────────┘
```

---

## 12. METADATA STRUCTURE SUMMARY

```json
{
  "nfl/data/rankings/.metadata.json": {
    "last_scraped": "2025-10-26"
  },
  
  "nfl/data/profiles/.metadata.json": {
    "kansas_city_chiefs": "2025-10-26",
    "washington_commanders": "2025-10-27"
  },
  
  "nfl/data/predictions/.metadata.json": {
    "2025-10-27_kc_was": {
      "last_predicted": "2025-10-26",
      "results_fetched": true,
      "game_date": "2025-10-27",
      "teams": ["Washington Commanders", "Kansas City Chiefs"],
      "home_team": "Kansas City Chiefs",
      "home_team_abbr": "kan",
      "results_fetched_at": "2025-10-28 11:13:37",
      "analysis_generated": true,
      "analysis_generated_at": "2025-10-28 11:14:24"
    }
  }
}
```

