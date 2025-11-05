"""Shared prompt template with sport-specific component injection."""

import json

from shared.utils.data_optimizer import optimize_team_profile


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
        odds: dict = None
    ) -> str:
        """Build prediction prompt with EV+ analysis and Kelly Criterion stake sizing.

        Generates 5 individual bets ranked by Expected Value.

        Args:
            sport_components: Sport-specific prompt components object
            team_a: First team name
            team_b: Second team name
            home_team: Which team is playing at home
            team_a_stats: Team A's ranking stats
            team_b_stats: Team B's ranking stats
            profile_a: Team A's detailed profile (optional)
            profile_b: Team B's detailed profile (optional)
            odds: Betting odds data from sportsbook (required)

        Returns:
            Formatted prompt string for Claude API
        """
        # Optimize profiles (same as regular prompt)
        optimized_profile_a = optimize_team_profile(profile_a)
        optimized_profile_b = optimize_team_profile(profile_b)

        # Build data context (identical to regular parlays)
        data_context = f"""{team_a.upper()} RANKING STATS:
{json.dumps(team_a_stats)}

{team_b.upper()} RANKING STATS:
{json.dumps(team_b_stats)}"""

        if optimized_profile_a:
            data_context += f"\n\n{team_a.upper()} DETAILED PROFILE:\n{json.dumps(optimized_profile_a)}"
        if optimized_profile_b:
            data_context += f"\n\n{team_b.upper()} DETAILED PROFILE:\n{json.dumps(optimized_profile_b)}"

        if odds:
            data_context += f"\n\nCURRENT BETTING ODDS (DraftKings):\n{json.dumps(odds)}"

        # EV-focused prompt with Kelly Criterion
        prompt = f"""You are an expert {sport_components.sport_name} Expected Value (EV+) betting analyst. Identify the TOP 5 individual bets with highest positive expected value.

MATCHUP: {team_a} @ {team_b} | HOME: {home_team}

METHODOLOGY:
1. IMPLIED PROBABILITY: Positive odds: 100/(odds+100), Negative: |odds|/(|odds|+100)
2. TRUE PROBABILITY: Analyze stats (season avg, last 3 games, matchup) → BE CONSERVATIVE (reduce by 10-15%)
3. EXPECTED VALUE: EV = (True Prob × Decimal Odds) - 1 | MINIMUM: +3.0% to qualify
4. KELLY CRITERION: Full Kelly = (TP × DO - 1)/(DO - 1) | Recommend HALF KELLY

REQUIREMENTS:
- Exactly 5 bets (NO parlays, duplicates, or replacements)
- All bet types: Moneyline, Spread, Totals, {sport_components.bet_types_list}
- Max 3 yardage props (prefer diversity)
- Only healthy players, 8+ games data
{sport_components.injury_instructions}
- Both teams analyzed

DATA:
{data_context}

OUTPUT FORMAT (ranked by EV, highest first):

## Bet 1: [Descriptive title]
**Bet**: [Full description with line, e.g. "Patrick Mahomes Over 250.5 Passing Yards"]
**Odds**: [American odds, e.g. "+150" or "-110"]
**Implied Probability**: [X.X%]
**True Probability**: [Y.Y%]
**Expected Value**: [+Z.Z%]
**Kelly Criterion**: [K.K%] full Kelly (recommend half: [H.H%] of bankroll)

**Calculation**:
- Decimal odds: [odds] → [decimal value]
- EV = ([true_prob] × [decimal]) - 1 = [+EV%]
- Full Kelly = ([true_prob] × [decimal] - 1) / ([decimal] - 1) = [K.K%]
- Half Kelly = [H.H%]

[Repeat format for Bets 2-5 with same structure]

## GAME ANALYSIS & REASONING
[Exactly 50 words: Key matchup dynamics, why these 5 bets have edge, common factors across selections]

CRITICAL RULES:
- MUST include **Calculation**: section after each bet with explicit math
- Show all work (decimal conversion, EV formula, Kelly formula)
- Reference specific stats ("averages 78.5 yards last 5 games")
- Conservative probabilities (account for variance)
- Never exceed half Kelly recommendation"""

        return prompt
