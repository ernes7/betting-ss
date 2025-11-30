"""Shared prompt template with sport-specific component injection."""

import json

from shared.utils.data_optimizer import optimize_team_profile, calculate_recent_form


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

        # Calculate recent form for both teams (last 5 games)
        recent_form_a = calculate_recent_form(profile_a, last_n_games=5)
        recent_form_b = calculate_recent_form(profile_b, last_n_games=5)

        # Get game spread if available (for blowout awareness)
        spread_line = None
        if odds and "spreads" in odds:
            spreads = odds.get("spreads", [])
            if spreads:
                # Get the spread for home team
                home_spread = spreads[0].get("point", 0) if spreads else 0
                spread_line = abs(float(home_spread)) if home_spread else 0

        # Build data context with recent form
        data_context = f"""{team_a.upper()} RANKING STATS (Full Season):
{json.dumps(team_a_stats)}

{team_b.upper()} RANKING STATS (Full Season):
{json.dumps(team_b_stats)}

{team_a.upper()} RECENT FORM (Last 5 Games):
{json.dumps(recent_form_a, indent=2)}

{team_b.upper()} RECENT FORM (Last 5 Games):
{json.dumps(recent_form_b, indent=2)}"""

        # Add blowout awareness if spread is significant
        if spread_line and spread_line >= 14:
            blowout_warning = f"""

⚠️ GAME SCRIPT AWARENESS:
This game has a {spread_line}-point spread. Be aware that blowouts can significantly
impact player props due to:
- Teams running clock in 2nd half
- Backup players getting more snaps
- Game flow limiting certain position production

Note: NFL is unpredictable - use your judgment. This is awareness, not a rule."""
            data_context += blowout_warning

        if optimized_profile_a:
            data_context += f"\n\n{team_a.upper()} DETAILED PROFILE:\n{json.dumps(optimized_profile_a)}"
        if optimized_profile_b:
            data_context += f"\n\n{team_b.upper()} DETAILED PROFILE:\n{json.dumps(optimized_profile_b)}"

        if odds:
            data_context += f"\n\nCURRENT BETTING ODDS (DraftKings):\n{json.dumps(odds)}"

        # EV-focused prompt
        prompt = f"""You are an expert {sport_components.sport_name} Expected Value (EV+) betting analyst that never misses, focused in hit rate. Identify the TOP 5 individual bets with highest positive expected value.

MATCHUP: {team_a} @ {team_b} | HOME: {home_team}

METHODOLOGY:
1. IMPLIED PROBABILITY: Positive odds: 100/(odds+100), Negative: |odds|/(|odds|+100)
2. TRUE PROBABILITY ESTIMATION (context-specific):
   - Player Props: Start with season average, adjust for recent form (±10%), apply matchup context (±5-10%)
   - Moneylines/Spreads: Use recent form heavily (60% weight), season stats (40% weight)
   - Totals: Balance both teams' offensive trends + recent scoring patterns
   - BE CONSERVATIVE: Reduce all estimates by 10-15% to account for variance and uncertainty
   - For high-variance props (TDs, receiving yards), reduce by 15-20%
3. EXPECTED VALUE: EV = (True Prob × Decimal Odds) - 1 | MINIMUM: +0.0% (any positive EV qualifies)

CRITICAL DATA USAGE RULES (MUST FOLLOW):
1. ⛔ NEVER use statistics, rankings, or data that are NOT explicitly provided in the DATA section below
2. ⛔ NEVER estimate, approximate, or make up any defensive stats (rush yards allowed, pass yards allowed, YPC allowed, rankings, etc.)
3. ⛔ NEVER reference rankings, percentages, or league positions unless they appear in the provided JSON data
4. ⛔ NEVER suggest bets that are NOT in the "CURRENT BETTING ODDS" section - ONLY use bets with exact odds from the provided DraftKings data
5. ⛔ NEVER invent bet lines, odds values, or bet types that do not appear in the odds JSON (e.g., no team totals unless explicitly provided)
6. ✅ ONLY use statistics that are directly visible in the RANKING STATS or DETAILED PROFILE sections
7. ✅ If defensive data is missing for a team, DO NOT mention defensive matchups for that team
8. ✅ Every statistical claim MUST be traceable to a specific field in the provided JSON data
9. ✅ Every bet MUST have corresponding odds data in the CURRENT BETTING ODDS JSON - verify the line and odds exist before suggesting
10. ✅ When citing stats in reasoning, reference the exact source (e.g., "rushing_offense shows 117.7 rush_yds_per_g")
11. ✅ For rankings: Use fields ending in "_rank" (e.g., "points_per_g_rank": 5 means 5th in league). Lower rank = better (1 = best, 32 = worst)

ADVANCED PLAYER PROP ANALYSIS (use provided data intelligently):

1. SCHEDULE_RESULTS TABLE - Identify recent trends:
   - Check last 3-5 games in schedule_results for scoring patterns
   - High-scoring games (30+ pts) suggest offensive usage trends
   - Low-scoring games (<17 pts) indicate struggles or game script issues
   - Example: "Last 3 games averaged 28 PPG vs season 22.1 PPG = hot offense"

2. INJURY_REPORT TABLE - Opportunity analysis:
   - OUT/QUESTIONABLE players = increased target share for healthy players
   - Example: "WR1 listed OUT → WR2 sees 25-30% target increase"
   - Missing RB1 = RB2 becomes bell cow (2-3x normal workload)
   - Missing linemen (OL/OT) = QB pressure increases, rushing YPC decreases

3. PLAYER TABLES CROSS-REFERENCE:
   - Compare player stats across passing/top_rushers/top_receivers tables
   - Identify volume leaders: receptions, rush attempts, targets
   - Example: "5.2 rec/g ranks 2nd on team → clear WR2 role with stable floor"

4. RECENT FORM + GAME SCRIPT CORRELATION:
   - Recent form shows 4-1 record → likely positive game scripts
   - Winning teams = more rushing attempts, fewer garbage-time yards
   - Losing teams = pass-heavy (trailing), RBs phased out, WR volume increases

REQUIREMENTS:
- Exactly 5 bets (NO parlays, duplicates, or replacements)
- All bet types: Moneyline, Spread, Totals, {sport_components.bet_types_list}
- DO NOT include both moneyline AND spread for the same team (pick one or the other)
- Max 3 yardage props (prefer diversity)
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
- Focus analysis in GAME ANALYSIS section, not per-bet"""

        return prompt
