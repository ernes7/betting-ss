#!/usr/bin/env python3
"""Regenerate prediction JSON files from existing markdown files.

This script fixes the bug where Parlay 3 with confidence "97%+" was not being
parsed correctly due to the regex pattern not accepting the "+" sign.
"""

import json
import re
import os
from pathlib import Path
from datetime import datetime


def parse_prediction_text(prediction_text: str) -> list[dict]:
    """Parse prediction text to extract structured parlay data.

    Args:
        prediction_text: Raw prediction text from Claude API

    Returns:
        List of parlay dictionaries with name, confidence, bets, reasoning
    """
    parlays = []
    # Updated pattern to handle confidence like "97%+" (with optional +)
    parlay_pattern = r'## (Parlay \d+: .+?)\n\*\*Confidence\*\*: (\d+)%\+?\n\n\*\*Bets:\*\*\n(.+?)\n\n\*\*Reasoning\*\*: (.+?)(?=\n##|\Z)'

    for match in re.finditer(parlay_pattern, prediction_text, re.DOTALL):
        parlay_name = match.group(1).strip()
        confidence = int(match.group(2))
        bets_text = match.group(3).strip()
        reasoning = match.group(4).strip()

        # Parse bets list (numbered items)
        bets = []
        for bet_match in re.finditer(r'^\d+\.\s+(.+?)$', bets_text, re.MULTILINE):
            bets.append(bet_match.group(1).strip())

        parlays.append({
            "name": parlay_name,
            "confidence": confidence,
            "bets": bets,
            "reasoning": reasoning,
            "odds": None  # To be filled in later
        })

    return parlays


def parse_markdown_header(content: str) -> dict:
    """Parse metadata from markdown header.

    Args:
        content: Full markdown content

    Returns:
        Dictionary with metadata
    """
    metadata = {}

    # Extract title line (e.g., "# Chicago Bears vs Baltimore Ravens - 2025-10-26")
    title_match = re.search(r'^# (.+?) vs (.+?) - (.+?)$', content, re.MULTILINE)
    if title_match:
        metadata['team_a'] = title_match.group(1).strip()
        metadata['team_b'] = title_match.group(2).strip()
        metadata['date'] = title_match.group(3).strip()

    # Extract home team
    home_match = re.search(r'\*\*Home Team\*\*: (.+?)$', content, re.MULTILINE)
    if home_match:
        metadata['home_team'] = home_match.group(1).strip()

    # Extract generated timestamp
    gen_match = re.search(r'\*\*Generated\*\*: (.+?)$', content, re.MULTILINE)
    if gen_match:
        metadata['generated_at'] = gen_match.group(1).strip()

    # Extract model
    model_match = re.search(r'\*\*Model\*\*: (.+?)$', content, re.MULTILINE)
    if model_match:
        metadata['model'] = model_match.group(1).strip()

    # Extract API cost
    cost_match = re.search(r'\*\*API Cost\*\*: \$(.+?)$', content, re.MULTILINE)
    if cost_match:
        metadata['api_cost'] = float(cost_match.group(1).strip())

    return metadata


def regenerate_json_from_markdown(md_path: Path, sport: str):
    """Regenerate JSON file from markdown file.

    Args:
        md_path: Path to markdown file
        sport: Sport name (nfl or nba)
    """
    # Read markdown
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse header metadata
    metadata = parse_markdown_header(content)

    if not metadata:
        print(f"  ⚠️  Could not parse metadata from {md_path.name}")
        return False

    # Extract prediction text (between first --- and second ---)
    parts = content.split('---\n')
    if len(parts) < 2:
        print(f"  ⚠️  Could not find prediction text in {md_path.name}")
        return False

    prediction_text = parts[1].strip()

    # Parse parlays
    parlays = parse_prediction_text(prediction_text)

    if not parlays:
        print(f"  ⚠️  Could not parse parlays from {md_path.name}")
        return False

    # Load existing JSON to get tokens (if available)
    json_path = md_path.with_suffix('.json')
    tokens = {"input": 0, "output": 0, "total": 0}

    if json_path.exists():
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                tokens = existing_data.get('tokens', tokens)
                # Update cost from existing if not in markdown
                if 'api_cost' not in metadata and 'api_cost' in existing_data:
                    metadata['api_cost'] = existing_data['api_cost']
        except Exception:
            pass

    # Build JSON structure
    prediction_data = {
        "sport": sport,
        "teams": [metadata.get('team_a', 'Unknown'), metadata.get('team_b', 'Unknown')],
        "home_team": metadata.get('home_team', 'Unknown'),
        "date": metadata.get('date', 'Unknown'),
        "generated_at": metadata.get('generated_at', 'Unknown'),
        "model": metadata.get('model', 'unknown'),
        "api_cost": metadata.get('api_cost', 0.0),
        "tokens": tokens,
        "parlays": parlays
    }

    # Check if this is an update (parlay count changed)
    old_parlay_count = 0
    if json_path.exists():
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
                old_parlay_count = len(old_data.get('parlays', []))
        except Exception:
            pass

    # Save JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(prediction_data, f, indent=2, ensure_ascii=False)

    new_parlay_count = len(parlays)
    if old_parlay_count != new_parlay_count and old_parlay_count > 0:
        print(f"  ✅ {md_path.name}: {old_parlay_count} → {new_parlay_count} parlays")
        return True
    else:
        print(f"  ✓  {md_path.name}: {new_parlay_count} parlays")
        return False


def main():
    """Main function to regenerate all prediction JSONs."""
    print("🔄 Regenerating prediction JSON files from markdown...\n")

    base_dir = Path(__file__).parent.parent
    updated_count = 0
    total_count = 0

    # Process NFL predictions
    nfl_dir = base_dir / "nfl" / "data" / "predictions"
    if nfl_dir.exists():
        print("📊 Processing NFL predictions...")
        for md_file in sorted(nfl_dir.rglob("*.md")):
            total_count += 1
            if regenerate_json_from_markdown(md_file, "nfl"):
                updated_count += 1
        print()

    # Process NBA predictions
    nba_dir = base_dir / "nba" / "data" / "predictions"
    if nba_dir.exists():
        print("🏀 Processing NBA predictions...")
        for md_file in sorted(nba_dir.rglob("*.md")):
            total_count += 1
            if regenerate_json_from_markdown(md_file, "nba"):
                updated_count += 1
        print()

    print(f"✨ Done! Updated {updated_count}/{total_count} files")


if __name__ == "__main__":
    main()
