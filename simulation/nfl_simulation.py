"""NFL Simulation - Fetch stats for random matchups.

Simple simulation that selects 2 random NFL teams and fetches
all their stats (rankings, defensive stats, team profiles).
"""

import random
from datetime import datetime

from sports.nfl.teams import TEAMS, DK_TO_PFR_ABBR
from sports.nfl.nfl_config import get_nfl_stats_config
from services.stats import StatsService


def select_random_teams(count: int = 2) -> list[dict]:
    """Select random teams from the NFL roster.

    Args:
        count: Number of teams to select (default 2)

    Returns:
        List of team dictionaries
    """
    return random.sample(TEAMS, count)


def run_simulation():
    """Run a simulation by selecting 2 random teams and fetching their stats."""
    print("=" * 60)
    print("NFL SIMULATION - Random Matchup Stats Fetcher")
    print("=" * 60)

    # Select 2 random teams
    teams = select_random_teams(2)
    away_team = teams[0]
    home_team = teams[1]

    print(f"\nSimulated Matchup:")
    print(f"  {away_team['name']} @ {home_team['name']}")
    print(f"  ({away_team['abbreviation']} vs {home_team['abbreviation']})")

    # Initialize stats service
    config = get_nfl_stats_config()
    stats_service = StatsService(sport="nfl", config=config)

    today = datetime.now().strftime("%Y-%m-%d")

    # Fetch rankings (league-wide stats)
    print(f"\n[1/3] Fetching league rankings...")
    try:
        rankings = stats_service.fetch_rankings(skip_if_exists=True, date=today)
        tables = rankings.get("tables", {})
        print(f"  Loaded {len(tables)} ranking tables: {list(tables.keys())}")
    except Exception as e:
        print(f"  Error fetching rankings: {e}")
        rankings = None

    # Fetch defensive stats
    print(f"\n[2/3] Fetching defensive stats...")
    try:
        defensive = stats_service.fetch_defensive_stats(skip_if_exists=True, date=today)
        tables = defensive.get("tables", {})
        print(f"  Loaded {len(tables)} defensive tables: {list(tables.keys())}")
    except Exception as e:
        print(f"  Error fetching defensive stats: {e}")
        defensive = None

    # Fetch team profiles for both teams
    print(f"\n[3/3] Fetching team profiles...")
    profiles = {}

    for team in [away_team, home_team]:
        pfr_abbr = team["pfr_abbr"]
        print(f"  Fetching {team['name']} ({pfr_abbr})...")

        try:
            profile = stats_service.fetch_team_profile(
                team_abbr=pfr_abbr,
                skip_if_exists=True,
                date=today
            )
            tables = profile.get("tables", {})
            profiles[team["abbreviation"]] = profile
            print(f"    Loaded {len(tables)} profile tables: {list(tables.keys())}")
        except Exception as e:
            print(f"    Error: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("SIMULATION COMPLETE")
    print("=" * 60)
    print(f"\nMatchup: {away_team['name']} @ {home_team['name']}")
    print(f"Date: {today}")
    print(f"\nData loaded:")
    print(f"  - Rankings: {'Yes' if rankings else 'No'}")
    print(f"  - Defensive: {'Yes' if defensive else 'No'}")
    print(f"  - {away_team['abbreviation']} profile: {'Yes' if away_team['abbreviation'] in profiles else 'No'}")
    print(f"  - {home_team['abbreviation']} profile: {'Yes' if home_team['abbreviation'] in profiles else 'No'}")

    return {
        "matchup": f"{away_team['abbreviation']} @ {home_team['abbreviation']}",
        "away_team": away_team,
        "home_team": home_team,
        "rankings": rankings,
        "defensive": defensive,
        "profiles": profiles,
    }


if __name__ == "__main__":
    run_simulation()
