"""Test script to verify data optimization reduces token usage."""

import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.utils.data_optimizer import optimize_team_profile
from shared.utils import FileManager


def estimate_tokens(data):
    """Rough token estimate (1 token ≈ 4 characters)."""
    json_str = json.dumps(data, indent=2)
    return len(json_str) // 4


def main():
    # Load a sample team profile
    team_name = "baltimore_ravens"
    profile_dir = f"nfl/data/profiles/{team_name}"

    print(f"\n{'='*60}")
    print(f"Testing Data Optimization for: {team_name.replace('_', ' ').title()}")
    print(f"{'='*60}\n")

    # Load full profile
    full_profile = FileManager.load_all_json_in_dir(profile_dir)

    # Show original size
    print("ORIGINAL PROFILE:")
    print(f"  Tables included: {list(full_profile.keys())}")
    original_tokens = estimate_tokens(full_profile)
    print(f"  Estimated tokens: {original_tokens:,}\n")

    # Show table sizes
    print("  Table breakdown:")
    for table_name, table_data in full_profile.items():
        tokens = estimate_tokens(table_data)
        rows = len(table_data.get("data", [])) if isinstance(table_data, dict) else 0
        print(f"    - {table_name}: {tokens:,} tokens ({rows} rows)")

    # Optimize profile
    optimized_profile = optimize_team_profile(full_profile)

    # Show optimized size
    print(f"\n{'='*60}\n")
    print("OPTIMIZED PROFILE:")
    print(f"  Tables included: {list(optimized_profile.keys())}")
    optimized_tokens = estimate_tokens(optimized_profile)
    print(f"  Estimated tokens: {optimized_tokens:,}\n")

    # Show optimized table sizes
    print("  Table breakdown:")
    for table_name, table_data in optimized_profile.items():
        tokens = estimate_tokens(table_data)
        rows = len(table_data.get("data", [])) if isinstance(table_data, dict) else 0
        print(f"    - {table_name}: {tokens:,} tokens ({rows} rows)")

    # Calculate savings
    print(f"\n{'='*60}\n")
    tokens_saved = original_tokens - optimized_tokens
    percent_saved = (tokens_saved / original_tokens) * 100
    print(f"TOKEN SAVINGS:")
    print(f"  Original:  {original_tokens:,} tokens")
    print(f"  Optimized: {optimized_tokens:,} tokens")
    print(f"  Saved:     {tokens_saved:,} tokens ({percent_saved:.1f}%)\n")

    # Projection for full prediction (2 teams + rankings)
    print(f"FULL PREDICTION PROJECTION (2 teams + rankings):")
    full_prediction_original = original_tokens * 2 + 500  # +500 for rankings
    full_prediction_optimized = optimized_tokens * 2 + 500
    print(f"  Before optimization: ~{full_prediction_original:,} tokens")
    print(f"  After optimization:  ~{full_prediction_optimized:,} tokens")
    print(f"  Savings:             ~{full_prediction_original - full_prediction_optimized:,} tokens")
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
