"""Test script for NBA prediction without interactive prompts."""

from shared.factory import SportFactory
import shared.register_sports

# Create NBA sport instance
nba_sport = SportFactory.create("nba")

print("=" * 70)
print("TESTING NBA PREDICTION")
print("=" * 70)
print()

# Test parameters
team_a = "Milwaukee Bucks"
team_b = "Toronto Raptors"
home_team = "Toronto Raptors"
week = 2

print(f"Matchup: {team_a} @ {team_b}")
print(f"Home Team: {home_team}")
print(f"Week: {week}")
print()

# Step 1: Extract rankings if needed
print("Step 1: Checking/Extracting NBA rankings...")
rankings_result = nba_sport.scraper.extract_rankings()
print()

# Step 2: Extract team profiles if needed
print("Step 2: Extracting team profiles...")
print(f"  - Extracting {team_a}...")
profile_a = nba_sport.scraper.extract_team_profile(team_a)
print()
print(f"  - Extracting {team_b}...")
profile_b = nba_sport.scraper.extract_team_profile(team_b)
print()

# Step 3: Load data
print("Step 3: Loading ranking and profile data...")
rankings = nba_sport.predictor.load_ranking_tables()
if not profile_a:
    profile_a = nba_sport.predictor.load_team_profile(team_a)
if not profile_b:
    profile_b = nba_sport.predictor.load_team_profile(team_b)

print(f"  - Rankings tables loaded: {len(rankings)}")
print(f"  - {team_a} profile tables: {len(profile_a) if profile_a else 0}")
print(f"  - {team_b} profile tables: {len(profile_b) if profile_b else 0}")
print()

# Step 4: Generate prediction
print("Step 4: Generating AI-powered parlays...")
result = nba_sport.predictor.generate_parlays(
    team_a=team_a,
    team_b=team_b,
    home_team=home_team,
    rankings=rankings,
    profile_a=profile_a,
    profile_b=profile_b
)
print()

# Display result
print("=" * 70)
print("PREDICTION RESULT")
print("=" * 70)
print()
print(result)
print()
print("=" * 70)
