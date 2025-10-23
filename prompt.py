"""Prompt generation for AI-powered NFL predictions."""

import json


def build_prediction_prompt(
    team_a: str,
    team_b: str,
    home_team: str,
    team_a_stats: dict,
    team_b_stats: dict,
    profile_a: dict | None = None,
    profile_b: dict | None = None,
) -> str:
    """
    Build comprehensive prompt for Claude API to generate dual parlays.

    Args:
        team_a: First team name
        team_b: Second team name
        home_team: Which team is playing at home
        team_a_stats: Team A's ranking stats
        team_b_stats: Team B's ranking stats
        profile_a: Team A's detailed profile (optional)
        profile_b: Team B's detailed profile (optional)

    Returns:
        Formatted prompt string for Claude API
    """
    # Build comprehensive data context
    data_context = f"""{team_a.upper()} RANKING STATS:
{json.dumps(team_a_stats, indent=2)}

{team_b.upper()} RANKING STATS:
{json.dumps(team_b_stats, indent=2)}"""

    # Add profile data if available
    if profile_a:
        data_context += (
            f"\n\n{team_a.upper()} DETAILED PROFILE:\n{json.dumps(profile_a, indent=2)}"
        )
    if profile_b:
        data_context += (
            f"\n\n{team_b.upper()} DETAILED PROFILE:\n{json.dumps(profile_b, indent=2)}"
        )

    # Build the full prompt
    prompt = f"""You are an expert NFL betting analyst. Analyze this matchup and generate THREE single-game parlays:

MATCHUP: {team_a} @ {team_b}
HOME TEAM: {home_team}

OBJECTIVE:
- Parlay 1: Assumes {team_a} wins (75%+ confidence)
- Parlay 2: Assumes {team_b} wins (75%+ confidence)
- Parlay 3: SAFE parlay - 90%+ confidence, NO moneylines, NO spread

REQUIREMENTS:
- Parlays 1 & 2: Include 3-4 bets (can include moneyline/spread)
- Parlay 3: Include 3-4 VERY safe INDIVIDUAL player props only (NO winner prediction, NO spread, NO combined props)
- Parlay 3 should work regardless of who wins
- Parlay 3 must use ONLY individual player props available on Hard Rock:
  * Individual QB passing yards (e.g., "Justin Herbert Over 265.5 passing yards")
  * Individual RB rushing yards (e.g., "Aaron Jones Over 55.5 rushing yards")
  * Individual WR receiving yards (e.g., "Justin Jefferson Over 75.5 receiving yards")
  * Game total points Over/Under (e.g., "Over 45.5 total points")
  * Field goals Over/Under 3.5 ONLY (not 1.5 or other values)
- DO NOT use combined props (combined passing attempts, combined rush attempts, etc.)
- DO NOT use penalty bets (team penalties, etc.)
- Focus on conservative lines for star players with consistent production

DATA:
{data_context}

Generate exactly this format:

## Parlay 1: {team_a} Wins
**Confidence**: [percentage]%

**Bets:**
1. [Specific bet with line]
2. [Specific bet with line]
3. [Specific bet with line]
4. [Specific bet with line]

**Reasoning**: [2-3 sentences on why this parlay has 75%+ confidence]

## Parlay 2: {team_b} Wins
**Confidence**: [percentage]%

**Bets:**
1. [Specific bet with line]
2. [Specific bet with line]
3. [Specific bet with line]
4. [Specific bet with line]

**Reasoning**: [2-3 sentences on why this parlay has 75%+ confidence]

## Parlay 3: Safe Picks (No Winner Required)
**Confidence**: 90%+

**Bets:**
1. [Individual player prop - e.g., QB passing yards, RB rushing yards, WR receiving yards]
2. [Individual player prop - e.g., QB passing yards, RB rushing yards, WR receiving yards]
3. [Individual player prop - e.g., QB passing yards, RB rushing yards, WR receiving yards]
4. [Game total O/U OR field goals O/U 3.5]

**Reasoning**: [2-3 sentences on why these are extremely safe individual player props that should hit regardless of game outcome. Focus on consistent producers with conservative lines.]"""

    return prompt
