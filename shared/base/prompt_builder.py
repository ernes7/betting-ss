"""Shared prompt template with sport-specific component injection."""

import json


class PromptBuilder:
    """Builds prediction prompts using shared template + sport-specific components."""

    @staticmethod
    def build_prompt(
        sport_components,
        team_a: str,
        team_b: str,
        home_team: str,
        team_a_stats: dict,
        team_b_stats: dict,
        profile_a: dict | None = None,
        profile_b: dict | None = None,
    ) -> str:
        """Build comprehensive prompt for AI prediction.

        Uses shared template structure with injected sport-specific components.

        Args:
            sport_components: Sport-specific prompt components object
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
            data_context += f"\n\n{team_a.upper()} DETAILED PROFILE:\n{json.dumps(profile_a, indent=2)}"
        if profile_b:
            data_context += f"\n\n{team_b.upper()} DETAILED PROFILE:\n{json.dumps(profile_b, indent=2)}"

        # Build the full prompt with shared template + injected components
        prompt = f"""You are an expert {sport_components.sport_name} betting analyst. Analyze this matchup and generate THREE single-game parlays:

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
{sport_components.bet_types_list}
{sport_components.restrictions}
{sport_components.injury_instructions}
- Only use healthy players with consistent stats for all player props
- Analyze ALL available stats INCLUDING {sport_components.stat_tables_to_analyze} to identify the best betting opportunities
- Focus on conservative lines for healthy star players with consistent production

DATA:
{data_context}

{sport_components.important_notes}

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
1. [Safe bet - any prop type except moneyline/spread]
2. [Safe bet - any prop type except moneyline/spread]
3. [Safe bet - any prop type except moneyline/spread]
4. [Safe bet - any prop type except moneyline/spread]

**Reasoning**: [2-3 sentences on why these are extremely safe bets that should hit regardless of game outcome. Focus on consistent producers with conservative lines based on their season averages from the stats provided.]"""

        return prompt
