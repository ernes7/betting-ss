# Sports Betting Prediction Project - Quick Reference

## File Organization at a Glance

### Data Directories

```
nfl/data/
├── rankings/              ← League-wide stats (6 JSON files)
│   └── .metadata.json     [last_scraped: "2025-10-26"]
├── profiles/{team}/       ← Per-team stats (8 JSON files each)
│   └── .metadata.json     [team_name: "YYYY-MM-DD"]
├── predictions/           ← AI-generated predictions
│   ├── 2025-10-27/
│   │   ├── kc_was.md
│   │   └── kc_was.json
│   └── .metadata.json     [game_key: {...full game tracking...}]
├── results/               ← Boxscore data (after games)
│   └── 2025-10-27/kc_was.json
├── analysis/              ← Prediction accuracy analysis
│   └── 2025-10-27/kc_was.json
└── odds/                  ← Betting odds (NEW)
    └── 2025-10-31/BAL_vs_MIA_full.json
```

## Metadata Files

### 1. Rankings Metadata
**File**: `nfl/data/rankings/.metadata.json`
```json
{"last_scraped": "2025-10-26"}
```
- **Tracks**: When rankings were last fetched from Pro-Football-Reference
- **Updated by**: `shared/base/scraper.py` → extract_rankings()
- **Used for**: Preventing multiple daily fetches (check before auto-fetch)

### 2. Profiles Metadata
**File**: `nfl/data/profiles/.metadata.json`
```json
{
  "kansas_city_chiefs": "2025-10-26",
  "washington_commanders": "2025-10-26"
}
```
- **Tracks**: Which teams were scraped today (per-team basis)
- **Key format**: team folder name (lowercase with underscores)
- **Value format**: ISO date string
- **Updated by**: `nfl/cli_utils/predict.py` after scraping each team
- **Used for**: Avoiding re-scraping same team multiple times per day

### 3. Predictions Metadata
**File**: `nfl/data/predictions/.metadata.json`
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
  }
}
```
- **Tracks**: Entire lifecycle of a prediction (generation → results → analysis)
- **Key format**: `{game_date}_{home_abbr}_{away_abbr}`
- **Purpose**: Prevents duplicate predictions, tracks results fetching, marks analysis completion
- **Updated by**: Multiple commands (predict, fetch_results, analysis)

## File Naming Conventions

### Predictions Files
```
Directory: nfl/data/predictions/{YYYY-MM-DD}/
Files:     {HOME_ABBR}_{AWAY_ABBR}.{md|json}
Example:   nfl/data/predictions/2025-10-27/kc_was.{md,json}
Metadata key: 2025-10-27_kc_was
```

### Results Files
```
Directory: nfl/data/results/{YYYY-MM-DD}/
File:      {HOME_ABBR}_{AWAY_ABBR}.json
Example:   nfl/data/results/2025-10-27/kc_was.json
```

### Analysis Files
```
Directory: nfl/data/analysis/{YYYY-MM-DD}/
File:      {HOME_ABBR}_{AWAY_ABBR}.json
Example:   nfl/data/analysis/2025-10-27/kc_was.json
```

### Odds Files
```
Directory: nfl/data/odds/{YYYY-MM-DD}/
File:      {AWAY_ABBR}_vs_{HOME_ABBR}.json
Example:   nfl/data/odds/2025-10-31/BAL_vs_MIA_full.json
Note:      Uses DraftKings abbreviations (BAL, MIA), not PFR (rav, mia)
```

## Data Flow Pipeline

### 1. Rankings (Happens automatically, once per day)
```
Pro-Football-Reference → shared/base/scraper.extract_rankings()
                      → Save 6 tables to nfl/data/rankings/
                      → Update rankings/.metadata.json
```

### 2. Team Profiles (On-demand, cached daily per team)
```
Pro-Football-Reference → shared/base/scraper.extract_team_profile()
                      → Save 8 tables to nfl/data/profiles/{team}/
                      → Update profiles/.metadata.json
```

### 3. Predict Game (Per-game request)
```
User inputs (Team A, B, Home, Date)
  → Load rankings + profiles
  → Claude AI (with all data)
  → nfl/data/predictions/{date}/{home}_{away}.{md,json}
  → Update predictions/.metadata.json
```

### 4. Fetch Odds (Ad-hoc, from DraftKings HTML)
```
DraftKings HTML file → NFLOddsScraper.extract_odds()
                    → nfl/data/odds/{date}/{away}_vs_{home}.json
```

### 5. Fetch Results (After games complete)
```
predictions/.metadata.json (finds games with results_fetched=false)
  → Pro-Football-Reference boxscores
  → nfl/data/results/{date}/{home}_{away}.json
  → Update predictions/.metadata.json (results_fetched=true)
```

### 6. Analyze Predictions (After results available)
```
predictions/{date}/{file}.json + results/{date}/{file}.json
  → Claude AI comparison
  → nfl/data/analysis/{date}/{file}.json
  → Update predictions/.metadata.json (analysis_generated=true)
```

## Key Functions and Their File Operations

### nfl/cli_utils/predict.py
```
predict_game()
  ├─ load_predictions_metadata()         (reads predictions/.metadata.json)
  ├─ was_game_predicted_today()          (checks metadata for reuse)
  ├─ load_team_profiles()                (reads from profiles/{team}/)
  ├─ nfl_sport.scraper.extract_rankings() (reads from rankings/)
  ├─ nfl_sport.predictor.generate_parlays() (calls Claude API)
  ├─ save_prediction_to_markdown()       (writes .md file)
  ├─ save_prediction_to_markdown()       (also writes .json file)
  └─ save_predictions_metadata()         (updates metadata)
```

### nfl/cli_utils/fetch_odds.py
```
fetch_odds_command()
  ├─ Prompt for HTML file path
  ├─ NFLOddsScraper.extract_odds()
  ├─ save_odds_to_json()                 (writes to odds/{date}/)
  └─ Display summary
```

### nfl/cli_utils/fetch_results.py
```
fetch_results()
  ├─ load_predictions_metadata()         (reads predictions/.metadata.json)
  ├─ Filter games with results_fetched = false
  ├─ For each game:
  │  ├─ extract_game_result()            (scrapes PFR boxscore)
  │  ├─ save_result_to_json()            (writes to results/{date}/)
  │  └─ Update metadata (results_fetched = true)
  └─ save_predictions_metadata()         (updates metadata)
```

## Team Abbreviation Types

### PFR Abbreviations (Pro-Football-Reference)
- Used for: Building team profile URLs and boxscore URLs
- Format: 3 letters, lowercase
- Examples: `kan` (KC Chiefs), `was` (Washington), `sdg` (LA Chargers)
- Stored in: `nfl/teams.py` → TEAMS dict → `pfr_abbr` field

### DraftKings Abbreviations
- Used for: Odds file naming
- Format: Usually 2-3 uppercase letters
- Examples: `KC`, `WAS`, `BAL`
- Source: DraftKings HTML data directly

### Short Form Abbreviations (File naming)
- Used for: Prediction/results/analysis file naming
- Format: 2 lowercase letters
- Examples: `kc`, `was`, `bal`
- Derived from: Team name abbreviations

## Important Patterns

### Game Key Format
```
Game Key = {game_date}_{home_abbr}_{away_abbr}
Example = 2025-10-27_kc_was

This is the KEY in predictions/.metadata.json
The VALUE contains all game tracking info
```

### File Path from Game Key
```
Given metadata key: 2025-10-27_kc_was
Game date: 2025-10-27
Filename: kc_was.json

Path construction:
  predictions: nfl/data/predictions/{game_date}/{filename}.json
  results:     nfl/data/results/{game_date}/{filename}.json
  analysis:    nfl/data/analysis/{game_date}/{filename}.json
```

### Metadata Updates
```
Prediction saved → predictions/.metadata.json updated with:
  - last_predicted: today's date
  - results_fetched: false (waiting for game to complete)
  - game_date, teams, home_team, home_team_abbr (for later URL building)

Results fetched → predictions/.metadata.json updated with:
  - results_fetched: true
  - results_fetched_at: timestamp

Analysis generated → predictions/.metadata.json updated with:
  - analysis_generated: true
  - analysis_generated_at: timestamp
```

## Data Loading for Predictions

### Rankings
```
shared/base/predictor.load_ranking_tables()
  → FileManager.load_all_json_in_dir("nfl/data/rankings/")
  → Returns dict with 6 tables: {team_offense, passing_offense, ...}
  → Each table has: {table_name, headers, data: [{team, rank, ...}, ...]}
```

### Profiles
```
nfl/cli_utils/predict.load_team_profiles(team_a, team_b)
  → For each team:
     - Check if scraped today in profiles/.metadata.json
     - If not, call scraper.extract_team_profile()
     - Load all 8 JSON files from profiles/{team}/
  → Return dict: {team: {table_name: data, ...}}
```

### To Claude
```
Prompt includes:
  1. Sport-specific components (from nfl/prompt_components.py)
  2. Team A stats extracted from rankings
  3. Team B stats extracted from rankings
  4. Team A detailed profile data
  5. Team B detailed profile data
  6. Game context (home/away, date)
```

## Accessing the Analysis

**File saved at**: `/Users/ernestomartinez/Desktop/Projects/betting-ss/PROJECT_ANALYSIS.md`

This comprehensive document covers:
- Complete project structure
- Detailed data flows with diagrams
- Metadata file structures and usage
- File naming conventions
- Architecture patterns (Factory, Template Method, Config)
- Data relationships and lifecycle
- All 6 major flows: Rankings → Profiles → Predictions → Odds → Results → Analysis
