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
- Parlay 1: Assumes {team_a} wins (80%+ confidence)
- Parlay 2: Assumes {team_b} wins (80%+ confidence)
- Parlay 3: SAFE parlay - 95%+ confidence, NO moneylines, NO spread

REQUIREMENTS:
- Parlays 1 & 2: Include 3-4 bets (can include ANY bet type including moneyline/spread)
- Parlay 3: Include 3-4 VERY safe bets (NO moneyline, NO spread, but ANY other bet type allowed)
- Parlay 3 should work regardless of who wins
- ALL bet types available on Hard Rock (use any combination):
  * Moneyline (Parlays 1 & 2 only)
  * Spread (Parlays 1 & 2 only)
  * QB passing yards O/U (e.g., "Justin Herbert Over 265.5 passing yards")
  * RB rushing yards O/U (e.g., "Aaron Jones Over 55.5 rushing yards")
  * WR receiving yards O/U (e.g., "Justin Jefferson Over 75.5 receiving yards")
  * Player receptions O/U (e.g., "Justin Jefferson Over 6.5 receptions")
  * QB pass completions O/U (e.g., "Justin Herbert Over 22.5 completions")
  * QB pass attempts O/U (e.g., "Justin Herbert Over 35.5 attempts")
  * Player rush attempts O/U (e.g., "Aaron Jones Over 18.5 rush attempts")
  * Player anytime TD / touchdown scorers (e.g., "Justin Jefferson anytime TD")
  * Individual defensive player sacks O/U (PLAYER SPECIFIC ONLY - e.g., "Joey Bosa Over 0.5 sacks")
  * Defensive player tackles + assists O/U (e.g., "Roquan Smith Over 8.5 tackles+assists")
  * Individual defensive player interceptions O/U (PLAYER SPECIFIC ONLY - e.g., "Sauce Gardner Over 0.5 interceptions")
  * Game total points O/U (e.g., "Over 45.5 total points")
  * Field goals O/U (e.g., "Over 3.5 field goals")
- DO NOT use combined props (combined passing attempts, combined rush attempts, etc.)
- DO NOT use game total touchdowns (not available on Hard Rock)
- DO NOT use team/combined sacks (only individual player sacks available)
- DO NOT use team/combined interceptions (only individual player interceptions available)
- DO NOT use penalty bets (team penalties, etc.)
- CRITICAL: Check the injury_report table for BOTH teams before suggesting ANY player props
- DO NOT include any player with injury status (Out, Questionable, Doubtful, etc.) in prop bets
- Injured players should ONLY be mentioned in reasoning to explain team weaknesses/strengths
- Only use healthy players with consistent stats for all player props (passing yards, receiving yards, receptions, TDs, etc.)
- Analyze ALL available stats INCLUDING injury_report (team_stats, passing, rushing_receiving, defense_fumbles, touchdown_log, scoring_summary, injury_report) to identify the best betting opportunities
- Focus on conservative lines for healthy star players with consistent production

DATA:
{data_context}

IMPORTANT: Before generating parlays, check injury_report data to exclude all injured players from prop bets.

Generate exactly this format:

## Parlay 1: {team_a} Wins
**Confidence**: [percentage]%

**Bets:**
1. [Bet with line - can include moneyline/spread or any prop type]
2. [Bet with line - can include moneyline/spread or any prop type]
3. [Bet with line - can include moneyline/spread or any prop type]
4. [Bet with line - can include moneyline/spread or any prop type]

**Reasoning**: [2-3 sentences on why this parlay has 75%+ confidence based on the provided stats]

## Parlay 2: {team_b} Wins
**Confidence**: [percentage]%

**Bets:**
1. [Bet with line - can include moneyline/spread or any prop type]
2. [Bet with line - can include moneyline/spread or any prop type]
3. [Bet with line - can include moneyline/spread or any prop type]
4. [Bet with line - can include moneyline/spread or any prop type]

**Reasoning**: [2-3 sentences on why this parlay has 75%+ confidence based on the provided stats]

## Parlay 3: Safe Picks (No Winner Required)
**Confidence**: 90%+

**Bets:**
1. [Safe bet - any prop type except moneyline/spread, e.g., passing yards, receptions, completions, rush attempts, anytime TD, sacks, tackles, etc.]
2. [Safe bet - any prop type except moneyline/spread]
3. [Safe bet - any prop type except moneyline/spread]
4. [Safe bet - any prop type except moneyline/spread]

**Reasoning**: [2-3 sentences on why these are extremely safe bets that should hit regardless of game outcome. Focus on consistent producers with conservative lines based on their season averages from the stats provided.]"""

    return prompt
