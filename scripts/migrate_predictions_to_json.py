"""One-time migration script to convert existing .md predictions to .json format."""

import json
import os
import re
from pathlib import Path


def parse_prediction_markdown(md_content: str, sport: str, date: str) -> dict:
    """Parse markdown prediction file and extract structured data.

    Args:
        md_content: Raw markdown file content
        sport: Sport type (nfl or nba)
        date: Date/week identifier from path

    Returns:
        Dictionary with structured prediction data
    """
    # Extract title and teams
    title_match = re.search(r'^# (.+?) vs (.+?) - (.+?)$', md_content, re.MULTILINE)
    if not title_match:
        raise ValueError("Could not parse title")

    team_a = title_match.group(1).strip()
    team_b = title_match.group(2).strip()

    # Extract home team
    home_team_match = re.search(r'\*\*Home Team\*\*: (.+?)$', md_content, re.MULTILINE)
    home_team = home_team_match.group(1).strip() if home_team_match else None

    # Extract generated timestamp
    generated_match = re.search(r'\*\*Generated\*\*: (.+?)$', md_content, re.MULTILINE)
    generated_at = generated_match.group(1).strip() if generated_match else None

    # Extract model name
    model_match = re.search(r'\*\*Model\*\*: (.+?)$', md_content, re.MULTILINE)
    model = model_match.group(1).strip() if model_match else "unknown"

    # Extract API cost
    api_cost_match = re.search(r'\*\*API Cost\*\*: \$?([0-9.]+)', md_content)
    api_cost = float(api_cost_match.group(1)) if api_cost_match else 0.0

    # Extract parlays
    parlays = []

    # Find all parlay sections
    parlay_pattern = r'## (Parlay \d+: .+?)\n\*\*Confidence\*\*: (\d+)%\n\n\*\*Bets:\*\*\n(.+?)\n\n\*\*Reasoning\*\*: (.+?)(?=\n##|\n---|\Z)'

    for match in re.finditer(parlay_pattern, md_content, re.DOTALL):
        parlay_name = match.group(1).strip()
        confidence = int(match.group(2))
        bets_text = match.group(3).strip()
        reasoning = match.group(4).strip()

        # Parse bets list (numbered items)
        bets = []
        for bet_match in re.finditer(r'^\d+\.\s+(.+?)$', bets_text, re.MULTILINE):
            bets.append(bet_match.group(1).strip())

        # Try to find odds for this parlay
        parlay_num = re.search(r'Parlay (\d+)', parlay_name).group(1)
        odds_pattern = rf'\*\*PARLAY {parlay_num} ODDS:\*\*\s*([+\-]?\d+)?'
        odds_match = re.search(odds_pattern, md_content)
        odds = odds_match.group(1) if odds_match and odds_match.group(1) else None

        parlays.append({
            "name": parlay_name,
            "confidence": confidence,
            "bets": bets,
            "reasoning": reasoning,
            "odds": odds
        })

    # Build structured data
    prediction_data = {
        "sport": sport,
        "teams": [team_a, team_b],
        "home_team": home_team,
        "date": date,
        "generated_at": generated_at,
        "model": model,
        "api_cost": api_cost,
        "tokens": None,  # Not available in old predictions
        "parlays": parlays
    }

    return prediction_data


def migrate_predictions():
    """Migrate all existing .md predictions to .json format."""
    base_dir = Path(__file__).parent.parent

    # Define prediction directories
    prediction_dirs = [
        (base_dir / "nfl" / "predictions", "nfl"),
        (base_dir / "nba" / "predictions", "nba"),
    ]

    total_migrated = 0

    for pred_dir, sport in prediction_dirs:
        if not pred_dir.exists():
            print(f"⚠️  Directory not found: {pred_dir}")
            continue

        # Find all .md files
        md_files = list(pred_dir.rglob("*.md"))

        print(f"\n🏈 Processing {sport.upper()} predictions...")
        print(f"   Found {len(md_files)} markdown file(s)")

        for md_file in md_files:
            # Get date/week from parent directory name
            date = md_file.parent.name

            # Read markdown content
            with open(md_file, 'r', encoding='utf-8') as f:
                md_content = f.read()

            try:
                # Parse markdown to structured data
                prediction_data = parse_prediction_markdown(md_content, sport, date)

                # Create .json file path (same location, different extension)
                json_file = md_file.with_suffix('.json')

                # Save JSON
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(prediction_data, f, indent=2, ensure_ascii=False)

                print(f"   ✅ {md_file.name} → {json_file.name}")
                total_migrated += 1

            except Exception as e:
                print(f"   ❌ Failed to migrate {md_file.name}: {e}")

    print(f"\n✨ Migration complete! {total_migrated} prediction(s) converted to JSON")


if __name__ == "__main__":
    print("=" * 60)
    print("📦 Prediction Migration: Markdown → JSON")
    print("=" * 60)
    migrate_predictions()
