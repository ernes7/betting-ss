"""Bundesliga-specific prompt builder for AI predictions."""

import os
from pathlib import Path


def load_csv_files(directory: str) -> dict[str, str]:
    """Load all CSV files from a directory.

    Args:
        directory: Path to directory containing CSV files

    Returns:
        Dict mapping filename (without .csv) to file content
    """
    result = {}
    dir_path = Path(directory)

    if not dir_path.exists():
        return result

    for csv_file in sorted(dir_path.glob("*.csv")):
        name = csv_file.stem  # filename without extension
        result[name] = csv_file.read_text()

    return result


def get_latest_date_folder(base_dir: str) -> str | None:
    """Get the most recent date folder in a directory.

    Args:
        base_dir: Base directory containing date folders (YYYY-MM-DD)

    Returns:
        Path to latest date folder, or None if none exist
    """
    dir_path = Path(base_dir)
    if not dir_path.exists():
        return None

    date_folders = sorted(
        [d for d in dir_path.iterdir() if d.is_dir()],
        reverse=True
    )

    return str(date_folders[0]) if date_folders else None


def build_bundesliga_prompt(
    home_team: str,
    away_team: str,
    rankings_dir: str,
    home_profile_dir: str,
    away_profile_dir: str,
    odds_dir: str,
) -> str:
    """Build Bundesliga prediction prompt by loading raw CSV files.

    Args:
        home_team: Home team name
        away_team: Away team name
        rankings_dir: Path to rankings directory (e.g., sports/futbol/bundesliga/data/rankings)
        home_profile_dir: Path to home team profile directory
        away_profile_dir: Path to away team profile directory
        odds_dir: Path to odds directory for this game

    Returns:
        Prompt string for Claude API
    """
    # Load rankings (flat structure - no date folders)
    rankings = load_csv_files(rankings_dir)

    # Load fixtures
    home_fixtures = ""
    away_fixtures = ""

    home_fixtures_file = Path(home_profile_dir) / "fixtures.csv"
    if home_fixtures_file.exists():
        home_fixtures = home_fixtures_file.read_text()

    away_fixtures_file = Path(away_profile_dir) / "fixtures.csv"
    if away_fixtures_file.exists():
        away_fixtures = away_fixtures_file.read_text()

    # Load odds
    odds = load_csv_files(odds_dir)

    # Debug: Print what's being passed to the prompt
    print(f"\n{'='*60}")
    print("DEBUG: build_bundesliga_prompt() - Data Loading")
    print(f"{'='*60}")
    print(f"\n[1] MATCHUP:")
    print(f"    {away_team} @ {home_team}")

    print(f"\n[2] RANKINGS (flat structure):")
    print(f"    Dir:  '{rankings_dir}'")
    if rankings:
        print(f"    Tables loaded: {len(rankings)}")
        for name, content in rankings.items():
            lines = content.strip().split('\n')
            print(f"      - {name}: {len(lines)} rows, {len(content)} chars")
            if lines:
                print(f"        Header: {lines[0][:80]}{'...' if len(lines[0]) > 80 else ''}")
    else:
        print(f"    Tables loaded: NONE (directory missing or empty)")

    print(f"\n[3] HOME PROFILE ({home_team}):")
    print(f"    Dir: '{home_profile_dir}'")
    print(f"    Exists: {Path(home_profile_dir).exists()}")
    if Path(home_profile_dir).exists():
        all_files = list(Path(home_profile_dir).glob("*"))
        print(f"    Files in dir: {[f.name for f in all_files]}")
    print(f"    Fixtures file: '{home_fixtures_file}'")
    print(f"    Fixtures exists: {home_fixtures_file.exists()}")
    if home_fixtures:
        lines = home_fixtures.strip().split('\n')
        print(f"    Fixtures loaded: {len(lines)} rows, {len(home_fixtures)} chars")
        if lines:
            print(f"      Header: {lines[0][:80]}{'...' if len(lines[0]) > 80 else ''}")
            if len(lines) > 1:
                print(f"      Row 1:  {lines[1][:80]}{'...' if len(lines[1]) > 80 else ''}")
    else:
        print(f"    Fixtures loaded: EMPTY!")

    print(f"\n[4] AWAY PROFILE ({away_team}):")
    print(f"    Dir: '{away_profile_dir}'")
    print(f"    Exists: {Path(away_profile_dir).exists()}")
    if Path(away_profile_dir).exists():
        all_files = list(Path(away_profile_dir).glob("*"))
        print(f"    Files in dir: {[f.name for f in all_files]}")
    print(f"    Fixtures file: '{away_fixtures_file}'")
    print(f"    Fixtures exists: {away_fixtures_file.exists()}")
    if away_fixtures:
        lines = away_fixtures.strip().split('\n')
        print(f"    Fixtures loaded: {len(lines)} rows, {len(away_fixtures)} chars")
        if lines:
            print(f"      Header: {lines[0][:80]}{'...' if len(lines[0]) > 80 else ''}")
            if len(lines) > 1:
                print(f"      Row 1:  {lines[1][:80]}{'...' if len(lines[1]) > 80 else ''}")
    else:
        print(f"    Fixtures loaded: EMPTY!")

    print(f"\n[5] ODDS:")
    print(f"    Dir: '{odds_dir}'")
    print(f"    Exists: {Path(odds_dir).exists() if odds_dir else False}")
    if odds:
        print(f"    Files loaded: {len(odds)}")
        for name, content in odds.items():
            lines = content.strip().split('\n')
            print(f"      - {name}: {len(lines)} rows, {len(content)} chars")
    else:
        print(f"    Files loaded: NONE")

    print(f"\n[6] PROMPT SUMMARY:")
    prompt_data_status = []
    if rankings:
        prompt_data_status.append(f"rankings({len(rankings)} tables)")
    if home_fixtures:
        prompt_data_status.append("home_fixtures")
    if away_fixtures:
        prompt_data_status.append("away_fixtures")
    if odds:
        prompt_data_status.append(f"odds({len(odds)} files)")
    print(f"    Data included: {', '.join(prompt_data_status) if prompt_data_status else 'NONE!'}")
    print(f"{'='*60}\n")

    # Build rankings section
    rankings_section = "\n\n".join(
        f"### {name}\n{csv}" for name, csv in rankings.items()
    )

    # Build odds section
    odds_section = "\n\n".join(
        f"### {name}\n{csv}" for name, csv in odds.items()
    )

    prompt = f"""You are a Bundesliga betting analyst. Temperature 0.0 - be deterministic.

Game: {away_team} @ {home_team}

## Data
{rankings_section}

## {home_team} Fixtures
{home_fixtures}

## {away_team} Fixtures
{away_fixtures}

## Odds
{odds_section}

## Required Analysis (do this BEFORE picking lines)

### Step 1: Venue Form
- Extract {home_team} HOME record from standings_home_away (W-D-L, GF, GA, xG, xGA)
- Extract {away_team} AWAY record from standings_home_away
- Note: Home/away splits often differ dramatically from overall form

### Step 2: Recent Form
- Last 5 results from fixtures (note venue for each)
- Goal scoring/conceding trends

### Step 3: Efficiency Metrics
- Compare xG vs actual goals (overperforming teams regress)
- SOT/90 and goals/shot from squad_shooting
- Defensive solidity from squad_shooting_against

### Step 4: Key Matchup Factors
- Which team creates more chances? (GCA from squad_gca)
- Which defense is leakier at their venue?

## Output
First, write a 3-4 sentence summary of the key edge.
Then output 5 picks as JSON:
[
  {{"market": "...", "pick": "...", "odds": ..., "ev_reasoning": "...", "key_stat": "..."}}
]

Constraints:
- Odds between -150 and +500 only
- No overlapping markets
- No Asian Handicaps
- Each pick must cite a specific stat
"""
    return prompt
