# Odds Integration - Implementation Summary

## Overview
Successfully integrated DraftKings betting odds into the NFL prediction pipeline. Odds are now automatically loaded during prediction generation and passed to Claude AI for more informed betting recommendations.

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
Updated to use new naming convention and track metadata:

```python
def save_odds_to_json(odds_data: dict):
    # Convert DraftKings abbreviations to PFR
    pfr_away_abbr = DK_TO_PFR_ABBR[dk_away_abbr].lower()
    pfr_home_abbr = DK_TO_PFR_ABBR[dk_home_abbr].lower()

    # Save with home_away format (matches predictions)
    filename = f"{pfr_home_abbr}_{pfr_away_abbr}.json"

    # Update metadata for tracking
    metadata[game_key] = {
        "fetched_at": datetime.now().isoformat(),
        "game_date": date_folder,
        "home_team_abbr": pfr_home_abbr,
        "away_team_abbr": pfr_away_abbr,
        "source": "draftkings",
        "filepath": str(filepath)
    }
```

### 4. Prediction Pipeline (nfl/cli_utils/predict.py)
Added odds loading and display:

```python
def load_odds_file(game_date, team_a, team_b, home_team) -> dict | None:
    """Load odds file using same naming convention as predictions."""
    # Build filename with home team first
    filename = f"{home_abbr}_{away_abbr}.json"
    odds_filepath = os.path.join("nfl/data/odds", game_date, filename)
    # Load and return odds data
```

**Integration in predict_game():**
```python
# After loading profiles, before generating predictions
odds_data = load_odds_file(game_date, team_a, team_b, home_team)

if odds_data:
    console.print("✓ Loaded betting odds from DraftKings")
    # Display summary
else:
    console.print("⚠ No odds file found - predictions will be based on stats only")

# Pass odds to predictor
result = nfl_sport.predictor.generate_parlays(
    team_a, team_b, home_team,
    rankings, profile_a, profile_b,
    odds_data  # <- NEW: odds passed to AI
)
```

### 5. Predictor Enhancement (shared/base/predictor.py)
Updated to accept and forward odds:

```python
def generate_parlays(
    self,
    team_a: str,
    team_b: str,
    home_team: str,
    rankings: dict | None = None,
    profile_a: dict | None = None,
    profile_b: dict | None = None,
    odds: dict | None = None,  # <- NEW parameter
) -> dict:
    # Pass odds to prompt builder
    prompt = self.prompt_builder.build_prompt(
        ...,
        odds=odds
    )
```

### 6. Prompt Builder (shared/base/prompt_builder.py)
Enhanced to include odds in AI context:

```python
def build_prompt(
    ...,
    odds: dict | None = None,
) -> str:
    # Add odds to data context
    if odds:
        data_context += f"\n\nCURRENT BETTING ODDS (DraftKings):\n{json.dumps(odds, indent=2)}"

    # Add instructions for using odds
    # - If betting odds are provided, use them to inform your selections
    # - When odds include player prop lines/milestones, prioritize those players
    # - Compare odds to actual stats to identify value opportunities
```

### 7. Metadata Tracking
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
# Generating AI parlays with 80%+ confidence...
# [Claude generates parlays using stats + odds]
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
│ 4. Generate Predictions             │
│    Claude AI receives:              │
│    ├─ Rankings (league-wide stats)  │
│    ├─ Profiles (team-specific)      │
│    └─ Odds (DraftKings lines)       │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 5. Save Predictions                 │
│    nfl/data/predictions/{date}/{home}_{away}.json
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

### 1. Enhanced Prediction Quality
- **Before**: Claude analyzes rankings + profiles only
- **After**: Claude sees actual betting lines and player prop milestones
- **Result**: More realistic bets aligned with market expectations

### 2. Value Identification
- AI can spot discrepancies between stats and odds
- Example: Player averaging 280 passing yards but 250+ line at +100
- Better EV+ opportunity identification

### 3. Line Precision
- No more guessing at "conservative lines"
- AI sees actual DraftKings milestones (200+, 225+, 250+, etc.)
- Can pick specific lines with known odds

### 4. Automated Workflow
- Odds automatically loaded if available
- Graceful degradation if odds missing (stats-only mode)
- Clear feedback to user about odds status

### 5. Data Consistency
- Unified file naming across predictions and odds
- Metadata tracks complete lifecycle
- Easy to match predictions with odds for analysis

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

### Graceful Degradation
- If odds file missing: prediction works with stats only
- If odds malformed: warning shown, prediction continues
- No breaking changes to existing functionality

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
