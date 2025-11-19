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
        """Build prediction prompt with EV+ analysis.

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

        # EV-focused prompt
        prompt = f"""You are an expert {sport_components.sport_name} Expected Value (EV+) betting analyst. Identify the TOP 5 individual bets with highest positive expected value.

MATCHUP: {team_a} @ {team_b} | HOME: {home_team}

METHODOLOGY:
1. IMPLIED PROBABILITY: Positive odds: 100/(odds+100), Negative: |odds|/(|odds|+100)
2. TRUE PROBABILITY: Analyze stats (season avg, last 3 games, matchup) → BE CONSERVATIVE (reduce by 10-15%)
3. EXPECTED VALUE: EV = (True Prob × Decimal Odds) - 1 | MINIMUM: +0.0% (any positive EV qualifies)

CRITICAL DATA USAGE RULES (MUST FOLLOW):
1. ⛔ NEVER use statistics, rankings, or data that are NOT explicitly provided in the DATA section below
2. ⛔ NEVER estimate, approximate, or make up any defensive stats (rush yards allowed, pass yards allowed, YPC allowed, rankings, etc.)
3. ⛔ NEVER reference rankings, percentages, or league positions unless they appear in the provided JSON data
4. ✅ ONLY use statistics that are directly visible in the RANKING STATS or DETAILED PROFILE sections
5. ✅ If defensive data is missing for a team, DO NOT mention defensive matchups for that team
6. ✅ Every statistical claim MUST be traceable to a specific field in the provided JSON data
7. ✅ When citing stats in reasoning, reference the exact source (e.g., "rushing_offense shows 117.7 rush_yds_per_g")
8. ✅ For rankings: Use fields ending in "_rank" (e.g., "points_per_g_rank": 5 means 5th in league). Lower rank = better (1 = best, 32 = worst)

EXAMPLES OF FORBIDDEN STATEMENTS (DO NOT USE):
❌ "Patriots allow 4.5 YPC and 155.5 rush yards/game" (if not in provided data)
❌ "This defense ranks 25th against the run" (if ranking not in provided data)
❌ "Team X has allowed..." (if defensive stats not provided)
❌ Any defensive statistics not explicitly in the DATA section

ALLOWED STATEMENTS (ONLY USE THESE):
✅ "Patriots average 117.7 rushing yards per game (rushing_offense: rush_yds_per_g)"
✅ "Based on injury_report table, Player X is listed as OUT"
✅ "According to passing table, QB averages 253.9 yards (pass_yds column)"
✅ Only cite stats that exist verbatim in the provided JSON

REQUIREMENTS:
- Exactly 5 bets (NO parlays, duplicates, or replacements)
- All bet types: Moneyline, Spread, Totals, {sport_components.bet_types_list}
- DO NOT include both moneyline AND spread for the same team (pick one or the other)
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

[Repeat format for Bets 2-5 with same structure]

## GAME ANALYSIS & REASONING
[Exactly 50 words: Key matchup dynamics, why these 5 bets have edge, common factors across selections. Reference specific stats from the provided data to explain the betting edge.]

CRITICAL RULES:
- Conservative probabilities (account for variance)
- Reference specific stats when available ("averages 78.5 yards last 5 games")
- Focus analysis in GAME ANALYSIS section, not per-bet"""

        return prompt
