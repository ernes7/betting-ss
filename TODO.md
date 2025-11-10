# TODO: Schedule.json for Batch Prediction Support

## Problem Statement
Currently, to predict multiple games, users must manually input team names for each game. This is inefficient. We need to generate a schedule file when fetching odds, enabling a future "predict all games for a date" feature.

## Solution Architecture

### 1. Schedule.json Structure

**Location:** `/nfl/data/odds/{YYYY-MM-DD}/schedule.json`
- Co-located with odds files for that date
- Easy discovery and cleanup

**Schema:**
```json
{
  "date": "2025-11-09",
  "fetched_at": "2025-11-09T11:26:08.731595",
  "source": "draftkings",
  "games": [
    {
      "event_id": "32225651",
      "slug": "buf-bills-%40-mia-dolphins",
      "teams": {
        "away": {
          "name": "Buffalo Bills",
          "dk_abbr": "BUF",
          "pfr_abbr": "buf"
        },
        "home": {
          "name": "Miami Dolphins",
          "dk_abbr": "MIA",
          "pfr_abbr": "mia"
        }
      },
      "game_time": "2025-11-09T18:00:00.0000000Z",
      "game_time_display": "Today 1:00 PM",
      "has_started": false,
      "odds_file": "mia_buf.json",
      "odds_fetched": true
    }
  ],
  "summary": {
    "total_games": 4,
    "upcoming_games": 4,
    "started_games": 0,
    "odds_fetched": 4,
    "odds_missing": 0
  }
}
```

**Key Design Choices:**
- Both DK and PFR abbreviations (critical for compatibility)
- ISO timestamp + human-readable display time
- `has_started` flag (filter live games)
- `odds_file` path (direct reference, no guessing)
- `odds_fetched` status (track failures)

### 2. Implementation Plan

**A. Add new function to `nfl/cli_utils/fetch_odds.py`:**

```python
def generate_schedule_file(
    games: list[dict],
    date_folder: str,
    fetched_games_info: dict
) -> None:
    """Generate schedule.json for batch predictions.

    Creates a schedule file with game metadata to enable
    batch prediction workflows.

    Args:
        games: List of game dicts from parse_todays_game_links()
        date_folder: Date string (YYYY-MM-DD)
        fetched_games_info: Dict mapping event_id to fetch status
    """
```

**Logic:**
1. Build schedule structure with games array
2. For each game, map DK abbreviations to team names using teams.py
3. Determine if odds were fetched (check fetched_games_info)
4. Build odds_file path using PFR abbreviations
5. Calculate summary statistics
6. Save to `nfl/data/odds/{date_folder}/schedule.json`

**B. Update `fetch_odds_command()` in `fetch_odds.py`:**

After the summary display (around line 468), add:

```python
# Step 5: Generate schedule file for batch predictions
if upcoming_games or started_games:
    try:
        console.print()
        print_info("📅 Generating schedule file for batch predictions...")
        generate_schedule_file(
            all_games=upcoming_games + started_games,
            date_folder=today_str,
            fetched_info=fetched_tracking
        )
        print_success("Schedule file created for future batch predictions")
    except Exception as e:
        print_warning(f"Could not generate schedule: {str(e)}")
```

**C. Track fetch results during the loop:**

Update the fetch loop to track which games were successfully fetched:

```python
fetched_tracking = {}  # event_id -> bool

for game in upcoming_games:
    result = fetch_single_game_odds(...)
    fetched_tracking[game['event_id']] = (result['status'] == 'success')
```

### 3. Team Name Mapping

**Challenge:** DraftKings provides abbreviations, but predictions need full team names.

**Solution:** Use existing `nfl/teams.py` TEAMS array:

```python
from nfl.teams import TEAMS

# Build reverse lookup: DK abbr -> team info
DK_ABBR_TO_TEAM = {team["abbreviation"]: team for team in TEAMS}

# In generate_schedule_file():
away_dk_abbr, home_dk_abbr = parse_team_abbrs_from_slug(game['slug'])
away_team_info = DK_ABBR_TO_TEAM.get(away_dk_abbr)
home_team_info = DK_ABBR_TO_TEAM.get(home_dk_abbr)

game_entry = {
    "teams": {
        "away": {
            "name": away_team_info["name"],
            "dk_abbr": away_team_info["abbreviation"],
            "pfr_abbr": away_team_info["pfr_abbr"]
        },
        ...
    }
}
```

### 4. Future Batch Prediction Integration

**New CLI command** (future implementation):
```
NFL Menu:
1. Predict Game
2. Predict All Games (Batch)  ← NEW
3. Fetch Odds
4. Fetch Results
```

**Flow:**
```python
def predict_all_games_command():
    """Predict all upcoming games for a date."""

    # 1. Prompt for date (default: today)
    # 2. Load schedule.json from nfl/data/odds/{date}/
    # 3. Filter: not has_started AND odds_fetched == true
    # 4. For each game:
    #      - Check if already predicted (metadata)
    #      - Load odds from schedule.odds_file
    #      - Load profiles for both teams
    #      - Generate prediction
    #      - Save results
    # 5. Display summary
```

### 5. Error Handling

**Edge Cases:**
1. **No games**: Create schedule with empty games array
2. **All games started**: Still create schedule (for historical reference)
3. **Odds fetch failures**: Mark as `odds_fetched: false`
4. **Team abbreviation not found**: Log warning, use "Unknown Team"
5. **Schedule already exists**: Overwrite (odds may be updated)

### 6. Testing Strategy

**Test Cases:**
1. Fetch odds for multiple games → verify schedule.json created
2. Check all team abbreviations map correctly
3. Verify has_started flag accuracy
4. Confirm odds_file paths are correct
5. Test with mix of fetched/failed odds
6. Test with all games already started

## Files to Create/Modify

**MODIFY:** `nfl/cli_utils/fetch_odds.py`
- Add `generate_schedule_file()` function (~80 lines)
- Add team lookup dictionary
- Update `fetch_odds_command()` to call schedule generation
- Track fetch results in the loop

## Benefits

1. **Automation**: Enables "predict all games" with one command
2. **Self-documenting**: Schedule shows what games are available
3. **Maintainable**: Follows existing date-folder pattern
4. **Extensible**: Easy to add fields (betting limits, injury reports, etc.)
5. **Idempotent**: Safe to regenerate
6. **Consistent**: Uses same abbreviation system as existing code

## Future Enhancements (Not in this PR)

- Add `predict_all_games_command()` to predict.py
- Auto-refresh schedule if re-running fetch odds
- Include game status updates (in-progress, final score)
- Add schedule validation utility

---

## Prerequisites (Complete First!)

- [ ] Ensure "Fetch All Odds" works perfectly for a given date
- [ ] Verify "Predict Game" can correctly find odds files using PFR abbreviations
- [ ] Test with all 14 teams that have different DK vs PFR abbreviations
