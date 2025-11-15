"""Test script for EV Calculator - Jets vs Patriots Nov 13, 2025"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from shared.models.ev_calculator import EVCalculator
from nfl.nfl_config import NFLConfig

def main():
    # Load odds file
    odds_file = project_root / "nfl/data/odds/2025-11-13/nwe_nyj.json"

    print("=" * 80)
    print("EV CALCULATOR TEST: Jets @ Patriots - November 13, 2025")
    print("=" * 80)
    print()

    with open(odds_file, 'r') as f:
        odds_data = json.load(f)

    # Show game info
    teams = odds_data.get("teams", {})
    away = teams.get("away", {}).get("name", "")
    home = teams.get("home", {}).get("name", "")

    print(f"Matchup: {away} @ {home}")
    print()

    game_lines = odds_data.get("game_lines", {})
    print("Game Lines:")
    print(f"  Moneyline: {away} {game_lines.get('moneyline', {}).get('away')} | {home} {game_lines.get('moneyline', {}).get('home')}")
    print(f"  Spread: {away} {game_lines.get('spread', {}).get('away')} ({game_lines.get('spread', {}).get('away_odds')}) | {home} {game_lines.get('spread', {}).get('home')} ({game_lines.get('spread', {}).get('home_odds')})")
    print(f"  Total: {game_lines.get('total', {}).get('line')} (O: {game_lines.get('total', {}).get('over')}, U: {game_lines.get('total', {}).get('under')})")
    print()

    # Count total betting options
    player_props = odds_data.get("player_props", [])
    total_bets = 6  # Game lines
    for player in player_props:
        for prop in player.get("props", []):
            if "milestones" in prop:
                total_bets += len(prop["milestones"])
            elif "odds" in prop:
                total_bets += 1

    print(f"Total betting options available: {total_bets}")
    print()
    print("=" * 80)
    print()

    # Initialize EV Calculator
    print("Initializing EV Calculator...")
    calculator = EVCalculator(
        odds_data=odds_data,
        sport_config=NFLConfig(),
        base_dir=str(project_root),
        conservative_adjustment=0.85  # 15% reduction
    )

    print("Calculating EV for all bets...")
    print()

    # Get top 10 bets
    top_bets = calculator.get_top_n(n=10, min_ev_threshold=0.0)

    print("=" * 80)
    print("TOP 10 EV+ BETS (Minimum 0.0% EV)")
    print("=" * 80)
    print()

    if not top_bets:
        print("No bets found with EV >= 0.0%")
        print()
        print("Showing all bets with positive EV instead...")
        top_bets = calculator.get_top_n(n=10, min_ev_threshold=0.0)

    for i, bet in enumerate(top_bets, 1):
        print(f"## BET {i}: {bet['description']}")
        print(f"**Odds**: {bet['odds']:+d} (Decimal: {bet['decimal_odds']:.2f})")
        print(f"**Implied Probability**: {bet['implied_prob']:.1f}%")
        print(f"**True Probability**: {bet['true_prob']:.1f}%")
        print(f"**Adjusted Probability** (Conservative -15%): {bet['adjusted_prob']:.1f}%")
        print(f"**Expected Value**: {bet['ev_percent']:+.2f}%")
        print()
        print(f"**Reasoning**: {bet['reasoning']}")
        print()
        print("-" * 80)
        print()

    # Summary statistics
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total bets analyzed: {total_bets}")
    print(f"Bets with EV >= 3.0%: {len([b for b in calculator.calculate_all_ev(3.0)])} ")
    print(f"Bets with EV >= 0.0%: {len([b for b in calculator.calculate_all_ev(0.0)])}")
    print(f"Top 10 shown above")
    print()

if __name__ == "__main__":
    main()
