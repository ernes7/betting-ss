"""Prompt generation for AI-powered NBA predictions."""

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
    prompt = f"""You are an expert NBA betting analyst. Analyze this matchup and generate THREE single-game parlays:

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
  * Player points O/U (e.g., "LeBron James Over 25.5 points")
  * Player rebounds O/U (e.g., "Anthony Davis Over 10.5 rebounds")
  * Player assists O/U (e.g., "Chris Paul Over 8.5 assists")
  * Player 3-pointers made O/U (e.g., "Stephen Curry Over 4.5 threes")
  * Player steals O/U (e.g., "Kawhi Leonard Over 1.5 steals")
  * Player blocks O/U (e.g., "Rudy Gobert Over 1.5 blocks")
  * Player points + rebounds O/U (e.g., "Giannis Antetokounmpo Over 40.5 pts+reb")
  * Player points + assists O/U (e.g., "Luka Doncic Over 42.5 pts+ast")
  * Player rebounds + assists O/U (e.g., "Nikola Jokic Over 18.5 reb+ast")
  * Player double-double (e.g., "Domantas Sabonis double-double Yes")
  * Player triple-double (e.g., "Russell Westbrook triple-double Yes")
  * Player anytime first basket (e.g., "Jayson Tatum first basket")
  * Game total points O/U (e.g., "Over 225.5 total points")
  * Team total points O/U (e.g., "Lakers Over 112.5 points")
  * Quarter/Half totals O/U (e.g., "1st Quarter Over 55.5 points")
  * Highest scoring quarter (e.g., "4th Quarter highest scoring")
- DO NOT use combined props (combined assists, combined rebounds, etc.)
- DO NOT use team total steals/blocks (only individual player props available)
- DO NOT use team three-pointers made (use individual player 3PM instead)
- CRITICAL: Check the injuries table for BOTH teams before suggesting ANY player props
- DO NOT include any player with injury status (Out, Questionable, Doubtful, etc.) in prop bets
- Injured players should ONLY be mentioned in reasoning to explain team weaknesses/strengths
- Only use healthy players with consistent stats for all player props (points, rebounds, assists, 3PM, etc.)
- Analyze ALL available stats INCLUDING injuries (per_game_stats, totals_stats, team_and_opponent, adj_shooting, shooting, injuries) to identify the best betting opportunities
- Focus on conservative lines for healthy star players with consistent production

DATA:
{data_context}

IMPORTANT: Before generating parlays, check injuries data to exclude all injured players from prop bets.

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
1. [Safe bet - any prop type except moneyline/spread, e.g., player points, rebounds, assists, 3PM, steals, blocks, double-double, pts+reb, pts+ast, game total, etc.]
2. [Safe bet - any prop type except moneyline/spread]
3. [Safe bet - any prop type except moneyline/spread]
4. [Safe bet - any prop type except moneyline/spread]

**Reasoning**: [2-3 sentences on why these are extremely safe bets that should hit regardless of game outcome. Focus on consistent producers with conservative lines based on their season averages from the stats provided.]"""

    return prompt
