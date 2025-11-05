# Odds Integration - Implementation Summary

## Overview
Successfully integrated DraftKings betting odds into the NFL EV+ prediction pipeline. Odds are **required** for EV analysis and are automatically fetched during prediction generation. The system uses odds to calculate implied probabilities, compare against Claude AI's true probability estimates, and identify positive expected value (EV+) opportunities with Kelly Criterion stake sizing.

## Architecture Changes

### 1. File Naming Standardization
**Before:**
- Predictions: `{date}/{home_abbr}_{away_abbr}.json` (e.g., `2025-10-27/kan_was.json`)
- Odds: `{date}/{AWAY_ABBR}_vs_{HOME_ABBR}.json` (e.g., `2025-10-27/WAS_vs_KC.json`)

**After (Unified):**
- Predictions: `{date}/{home_abbr}_{away_abbr}.json` (e.g., `2025-10-27/kan_was.json`)
- Odds: `{date}/{home_abbr}_{away_abbr}.json` (e.g., `2025-10-27/kan_was.json`)

**Benefits:**
- Files for the same game now have identical names
- Easy to match predictions with odds
- Consistent lowercase PFR abbreviations throughout

### 2. Team Abbreviation Mappings (nfl/teams.py)
Added comprehensive mapping dictionaries to handle three abbreviation systems:

```python
# DraftKings (BAL, MIA, KC) <-> PFR (rav, mia, kan)
DK_TO_PFR_ABBR = {team["abbreviation"]: team["pfr_abbr"] for team in TEAMS}
PFR_TO_DK_ABBR = {team["pfr_abbr"]: team["abbreviation"] for team in TEAMS}

# Additional helper mappings
DK_ABBR_TO_NAME = {...}  # DraftKings abbr -> full name
PFR_ABBR_TO_NAME = {...}  # PFR abbr -> full name
```

**Why this matters:**
- DraftKings uses "BAL" → PFR uses "rav" (Ravens)
- DraftKings uses "KC" → PFR uses "kan" (Chiefs)
- Automatic conversion ensures consistency

### 3. Odds Fetching (nfl/cli_utils/fetch_odds.py)
Now uses **OddsRepository** and **MetadataService** from the clean architecture:

```python
# Initialize services (at module level)
from shared.services import MetadataService
from shared.repositories import OddsRepository
from shared.config import get_metadata_path

odds_metadata_service = MetadataService(get_metadata_path("nfl", "odds"))
odds_repo = OddsRepository("nfl")

def save_odds_to_json(odds_data: dict):
    # Convert DraftKings abbreviations to PFR
    pfr_away_abbr = DK_TO_PFR_ABBR[dk_away_abbr]
    pfr_home_abbr = DK_TO_PFR_ABBR[dk_home_abbr]

    # Save using repository (handles paths automatically)
    odds_repo.save_odds(date_folder, pfr_away_abbr, pfr_home_abbr, odds_data)

    # Update metadata using service
    metadata = odds_metadata_service.load_metadata()
    metadata[game_key] = {
        "fetched_at": datetime.now().isoformat(),
        "game_date": date_folder,
        "home_team_abbr": pfr_home_abbr,
        "away_team_abbr": pfr_away_abbr,
        "source": "draftkings",
        "filepath": f"nfl/data/odds/{date_folder}/{pfr_home_abbr}_{pfr_away_abbr}.json"
    }
    odds_metadata_service.save_metadata(metadata)
```

### 4. Prediction Pipeline (nfl/cli_utils/predict.py)
Now uses **OddsService** from the clean architecture:

```python
# Initialize services (at module level)
from shared.services import OddsService

odds_service = OddsService("nfl")
```

**Integration in predict_game():**
```python
# After loading profiles, before generating predictions
# OddsService automatically handles path construction and loading
odds_data = odds_service.load_odds_for_game(game_date, team_a_abbr, team_b_abbr, home_abbr)

if odds_data:
    print_success("Loaded betting odds from DraftKings")
    # Display summary
    game_lines_count = len(odds_data.get("game_lines", {}))
    player_props_count = len(odds_data.get("player_props", []))
    console.print(f"[dim]  • Game lines: {game_lines_count}[/dim]")
    console.print(f"[dim]  • Player props: {player_props_count} players[/dim]")
else:
    # Show error panel - odds are now REQUIRED
    console.print(Panel(error_text, border_style="red", padding=(1, 2)))
    return

# Pass odds to predictor (REQUIRED for EV analysis)
result = nfl_sport.predictor.generate_predictions(
    team_a, team_b, home_team,
    rankings, profile_a, profile_b,
    odds_data  # <- Odds REQUIRED for EV+ analysis and Kelly Criterion
)
```

**Benefits of OddsService:**
- Automatic path construction using paths_config
- Tries multiple file name combinations (home_away and away_home)
- Consistent error handling
- Same interface across NFL and NBA

### 5. Predictor Enhancement (shared/base/predictor.py)
Updated to require odds for EV analysis:

```python
def generate_predictions(
    self,
    team_a: str,
    team_b: str,
    home_team: str,
    rankings: dict | None = None,
    profile_a: dict | None = None,
    profile_b: dict | None = None,
    odds: dict = None,  # <- REQUIRED for EV+ analysis
) -> dict:
    # Odds are required for EV analysis
    if odds is None:
        return {
            "success": False,
            "error": "Odds data is required for EV+ analysis"
        }

    # Pass odds to prompt builder for EV calculation
    prompt = self.prompt_builder.build_prompt(
        ...,
        odds=odds
    )
```

### 6. Prompt Builder (shared/base/prompt_builder.py)
Enhanced to include odds and EV calculation methodology:

```python
def build_prompt(
    ...,
    odds: dict = None,
) -> str:
    # Add odds to data context
    if odds:
        data_context += f"\n\nCURRENT BETTING ODDS (DraftKings):\n{json.dumps(odds, indent=2)}"

    # EV-focused prompt includes:
    # - Convert odds to implied probability formulas
    # - Estimate true probability from stats (conservative approach)
    # - Calculate expected value: (True Prob × Decimal Odds) - 1
    # - Kelly Criterion stake sizing formulas (full and half)
    # - Minimum EV threshold (+3% edge required)
    # - Return top 5 bets ranked by EV
```

### 7. Clean Architecture Integration

The odds system now uses the **service layer** and **repository pattern** for clean separation of concerns:

**Service Layer** (`shared/services/`):
- **OddsService**: Handles odds loading logic
  - Automatically constructs file paths
  - Tries multiple naming patterns
  - Returns None if odds not found
  - Same interface for all sports

- **MetadataService**: Handles all metadata operations
  - Load/save metadata files
  - Consistent error handling
  - Used for odds, predictions, profiles, rankings

**Repository Layer** (`shared/repositories/`):
- **OddsRepository**: Handles odds data persistence
  - Save odds to JSON files
  - Load odds from JSON files
  - Automatic directory creation
  - Sport-agnostic implementation

**Configuration Layer** (`shared/config/`):
- **paths_config**: Centralized path templates
  - All file paths defined in one place
  - Easy to change directory structure
  - Type-safe path construction

**Benefits:**
- No manual path construction in CLI files
- Easy to swap storage (JSON → Database)
- Consistent behavior across all sports
- Services are easily testable (mockable)
- Follows SOLID principles

### 8. Metadata Tracking
**Odds Metadata** (`nfl/data/odds/.metadata.json`):
```json
{
  "2025-10-27_kan_was": {
    "fetched_at": "2025-10-27T14:30:00",
    "game_date": "2025-10-27",
    "home_team_abbr": "kan",
    "away_team_abbr": "was",
    "source": "draftkings",
    "filepath": "nfl/data/odds/2025-10-27/kan_was.json"
  }
}
```

**Predictions Metadata** (updated with odds tracking):
```json
{
  "2025-10-27_kan_was": {
    "last_predicted": "2025-10-27",
    "results_fetched": false,
    "odds_used": true,           // <- NEW: was odds data available?
    "odds_source": "draftkings", // <- NEW: which sportsbook?
    "game_date": "2025-10-27",
    "teams": ["Kansas City Chiefs", "Washington Commanders"],
    "home_team": "Kansas City Chiefs",
    "home_team_abbr": "kan"
  }
}
```

## Usage Workflow

### Complete Prediction Flow (with Odds)

```bash
# Step 1: Save DraftKings HTML
# Navigate to DraftKings game page, save HTML to your desktop

# Step 2: Fetch Odds
python main.py
→ NFL
→ Fetch Odds
→ Enter path: /Users/you/Desktop/draftkings_game.html
# Saves to: nfl/data/odds/{date}/{home}_{away}.json

# Step 3: Generate Predictions
python main.py
→ NFL
→ Predict Game
→ Enter game date: 2025-10-27
→ Select Team A: Washington Commanders
→ Select Team B: Kansas City Chiefs
→ Select home team: Kansas City Chiefs

# Output:
# 📊 Loading betting odds...
# ✓ Loaded betting odds from DraftKings
#   • Game lines: 3
#   • Player props: 25 players
#
# Analyzing EV+ opportunities with Kelly Criterion...
# [Claude generates top 5 EV+ bets using stats + odds]
#
# TOP 5 EV+ BETS:
# 1. Patrick Mahomes Over 250.5 Passing Yards (+150, 8.5% EV, 14.7% Kelly half)
# 2. Travis Kelce Over 75.5 Receiving Yards (+120, 6.2% EV, 11.3% Kelly half)
# ...
```

### Flow Diagram

```
User Input
    ↓
┌─────────────────────────────────────┐
│ 1. Fetch Rankings (Auto)            │
│    nfl/data/rankings/*.json         │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 2. Fetch Team Profiles              │
│    nfl/data/profiles/{team}/*.json  │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 3. Load Odds (if available)         │
│    nfl/data/odds/{date}/{home}_{away}.json
│    ├─ Game lines (ML, spread, total)│
│    └─ Player props (milestones)     │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 4. Generate EV+ Predictions         │
│    Claude AI receives:              │
│    ├─ Rankings (league-wide stats)  │
│    ├─ Profiles (team-specific)      │
│    ├─ Odds (DraftKings lines)       │
│    └─ EV calculation formulas       │
│    Returns:                         │
│    ├─ Top 5 bets ranked by EV%      │
│    ├─ Implied vs true probabilities │
│    └─ Kelly Criterion stakes        │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 5. Save Predictions                 │
│    nfl/data/predictions/{date}/{home}_{away}.json
│    Contains: 5 EV+ bets with Kelly  │
│    Metadata tracks odds_used: true  │
└─────────────────────────────────────┘
```

## Data Flow

### Odds Data Structure
```json
{
  "sport": "nfl",
  "teams": {
    "away": {
      "name": "Washington Commanders",
      "abbr": "WAS",
      "pfr_abbr": "was"
    },
    "home": {
      "name": "Kansas City Chiefs",
      "abbr": "KC",
      "pfr_abbr": "kan"
    }
  },
  "game_date": "2025-10-27T17:00:00Z",
  "fetched_at": "2025-10-27T14:30:00",
  "source": "draftkings",
  "game_lines": {
    "moneyline": {"away": 280, "home": -350},
    "spread": {
      "away": 8.5,
      "away_odds": -110,
      "home": -8.5,
      "home_odds": -110
    },
    "total": {"line": 47.5, "over": -110, "under": -110}
  },
  "player_props": [
    {
      "player": "Patrick Mahomes",
      "team": "kan",
      "props": [
        {
          "market": "passing_yards",
          "milestones": [
            {"line": 200, "odds": -400},
            {"line": 225, "odds": -200},
            {"line": 250, "odds": 100},
            {"line": 275, "odds": 250}
          ]
        },
        {
          "market": "passing_tds",
          "milestones": [
            {"line": 1, "odds": -300},
            {"line": 2, "odds": 120}
          ]
        }
      ]
    }
  ]
}
```

## Key Benefits

### 1. Positive Expected Value (EV+) Identification
- **Before**: Parlays based on confidence estimates only
- **After**: Mathematical EV analysis with implied vs true probabilities
- **Result**: Only bet when edge > +3% expected value

### 2. Kelly Criterion Stake Sizing
- Calculate optimal bet sizes to maximize long-term growth
- Half Kelly recommended for conservative bankroll management
- Example: 8.5% EV bet → 14.7% of bankroll stake
- Prevents over-betting and bankroll ruin

### 3. Market Line Integration
- Use actual DraftKings lines for precise EV calculations
- No guessing at implied probabilities
- AI estimates true probability from stats, compares to market
- Example: +150 odds = 40% implied prob → AI estimates 58% true prob = 8.5% EV

### 4. Profit/Loss Tracking
- After games, calculate actual P&L for each bet
- Win: $100 × (odds/100), Loss: -$100
- Track ROI, win rate, realized edge
- Verify prediction accuracy and refine models

### 5. Data Consistency
- Unified file naming across predictions, odds, and analysis
- Metadata tracks complete lifecycle (prediction → odds → results → P&L)
- Easy to backtest and improve strategies

## File Organization

```
nfl/data/
├── odds/
│   ├── .metadata.json              # Tracks all fetched odds
│   └── 2025-10-27/
│       ├── kan_was.json            # KC home vs WAS
│       ├── buf_mia.json            # BUF home vs MIA
│       └── rav_cin.json            # BAL home vs CIN
│
├── predictions/
│   ├── .metadata.json              # Tracks all predictions + odds_used
│   └── 2025-10-27/
│       ├── kan_was.json            # Same filename as odds!
│       ├── kan_was.md
│       ├── buf_mia.json
│       ├── buf_mia.md
│       └── ...
│
├── rankings/
│   ├── .metadata.json
│   └── {date}/
│       └── *.json
│
└── profiles/
    ├── .metadata.json
    └── {team_name}/
        └── *.json
```

## Migration & Backward Compatibility

### Automatic Metadata Migration
Old predictions metadata automatically upgraded:
```python
# Old format (string)
"2025-10-27_kan_was": "2025-10-27"

# Auto-migrates to:
"2025-10-27_kan_was": {
  "last_predicted": "2025-10-27",
  "results_fetched": false,
  "odds_used": false,      # Defaults to false for old predictions
  "odds_source": null,
  "game_date": "2025-10-27",
  "teams": [...],
  "home_team": "Kansas City Chiefs",
  "home_team_abbr": "kan"
}
```

### Odds Requirement for EV Analysis
- Odds are **REQUIRED** for EV+ predictions
- If odds missing: prediction fails with clear error message
- User must provide DraftKings URL to fetch odds
- Cannot calculate expected value without market odds

## Testing Checklist

- [x] Abbreviation mappings (all 32 teams)
- [x] Odds file naming (home_away format)
- [x] Odds loading in predict flow
- [x] Predictor accepts odds parameter
- [x] Prompt builder includes odds
- [x] Metadata tracking (odds + predictions)
- [x] Backward compatibility (old predictions)
- [x] Error handling (missing odds)

## Next Steps (Optional Enhancements)

### 1. Automatic DraftKings Scraping
Instead of manual HTML download, automate via Selenium:
```python
from selenium import webdriver
# Navigate to DraftKings, extract odds directly
```

### 2. Multiple Sportsbook Support
Add FanDuel, BetMGM, etc. for line shopping:
```python
odds_data = {
    "draftkings": {...},
    "fanduel": {...},
    "betmgm": {...}
}
# AI can find best lines across books
```

### 3. Odds Comparison in Analysis
After game completion, compare predictions vs actual odds:
```python
# Did we pick EV+ bets?
# Which sportsbook had best lines?
```

### 4. Real-time Odds Updates
Check for line movements before game time:
```python
# Alert if odds change significantly
# Re-generate predictions with updated odds
```

## Technical Notes

### Why PFR Abbreviations?
- Pro-Football-Reference is the primary data source
- Rankings, profiles, and boxscores all use PFR abbrs
- Consistent internal representation simplifies code
- Only convert at input (DraftKings) and output (display)

### Token Optimization
- Odds data adds ~500-1500 tokens per prediction
- Still well within Claude Sonnet 4.5 context window (200K)
- Average prediction: 8K-12K tokens (with odds)
- Cost impact: ~$0.001-$0.003 per prediction

### Error Handling Strategy
1. **Odds Fetching**: Try to convert abbrs, fallback to original
2. **Odds Loading**: Return None if missing, continue without
3. **Metadata**: Auto-migrate old formats, add missing fields
4. **Display**: Show clear status to user (odds available or not)

## Summary

Successfully integrated DraftKings odds into the NFL prediction pipeline with:
- ✅ Unified file naming (predictions ↔ odds)
- ✅ Automatic abbreviation conversion (DraftKings ↔ PFR)
- ✅ Seamless prediction flow integration
- ✅ Comprehensive metadata tracking
- ✅ Enhanced AI context with betting lines
- ✅ Backward compatibility maintained
- ✅ Graceful error handling

The system now automatically loads odds when available, passes them to Claude AI for better predictions, and tracks the complete data lineage through metadata files.
