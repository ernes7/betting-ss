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
        odds: dict | None = None,
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
            odds: Betting odds data from sportsbook (optional)

        Returns:
            Formatted prompt string for Claude API
        """
        # Optimize team profiles to reduce token usage
        optimized_profile_a = optimize_team_profile(profile_a)
        optimized_profile_b = optimize_team_profile(profile_b)

        # Build comprehensive data context
        data_context = f"""{team_a.upper()} RANKING STATS:
{json.dumps(team_a_stats)}

{team_b.upper()} RANKING STATS:
{json.dumps(team_b_stats)}"""

        # Add optimized profile data if available
        if optimized_profile_a:
            data_context += f"\n\n{team_a.upper()} DETAILED PROFILE:\n{json.dumps(optimized_profile_a)}"
        if optimized_profile_b:
            data_context += f"\n\n{team_b.upper()} DETAILED PROFILE:\n{json.dumps(optimized_profile_b)}"

        # Add betting odds if available
        if odds:
            data_context += f"\n\nCURRENT BETTING ODDS (DraftKings):\n{json.dumps(odds)}"

        # Get sport-specific parlay configuration (or use defaults)
        parlay_legs = getattr(sport_components, 'parlay_legs', '3-4')
        team_win_confidence = getattr(sport_components, 'team_win_confidence', '90')
        safe_picks_confidence = getattr(sport_components, 'safe_picks_confidence', '97')

        # Generate bet list format based on parlay_legs
        # If exact number (e.g., "3"), show that many lines; if range (e.g., "3-4"), show max
        if '-' in parlay_legs:
            # Range like "3-4" - extract max value
            max_legs = int(parlay_legs.split('-')[1])
        else:
            # Exact number like "3"
            max_legs = int(parlay_legs)

        # Create numbered bet list for format examples
        bet_list_with_ml = "\n".join([f"{i}. [Bet with line - can include moneyline/spread or any prop type]" for i in range(1, max_legs + 1)])
        bet_list_safe = "\n".join([f"{i}. [Safe bet - any prop type except moneyline/spread]" for i in range(1, max_legs + 1)])

        # Build the full prompt with shared template + injected components
        prompt = f"""You are an expert {sport_components.sport_name} betting analyst. Analyze this matchup and generate THREE single-game parlays:

MATCHUP: {team_a} @ {team_b}
HOME TEAM: {home_team}

OBJECTIVE:
- Parlay 1: Assumes {team_a} wins ({team_win_confidence}%+ confidence)
- Parlay 2: Assumes {team_b} wins ({team_win_confidence}%+ confidence)
- Parlay 3: SAFE parlay - {safe_picks_confidence}%+ confidence, NO moneylines, NO spread

REQUIREMENTS:
- Parlays 1 & 2: Include {parlay_legs} bets (can include ANY bet type including moneyline/spread)
- Parlay 3: Include {parlay_legs} VERY safe bets (NO moneyline, NO spread, but ANY other bet type allowed)
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
- If betting odds are provided, use them to inform your selections and identify value opportunities
- When odds include player prop lines/milestones, prioritize those players and compare odds to their actual stats

DATA:
{data_context}

{sport_components.important_notes}

{getattr(sport_components, 'conservative_line_rules', '')}

{getattr(sport_components, 'game_script_rules', '')}

Generate exactly this format:

## Parlay 1: {team_a} Wins
**Confidence**: [percentage]%

**Bets:**
{bet_list_with_ml}

**Reasoning**: [2-3 sentences on why this parlay has {team_win_confidence}%+ confidence based on the provided stats]

## Parlay 2: {team_b} Wins
**Confidence**: [percentage]%

**Bets:**
{bet_list_with_ml}

**Reasoning**: [2-3 sentences on why this parlay has {team_win_confidence}%+ confidence based on the provided stats]

## Parlay 3: Safe Picks (No Winner Required)
**Confidence**: {safe_picks_confidence}%+

**Bets:**
{bet_list_safe}

**Reasoning**: [2-3 sentences on why these are extremely safe bets that should hit regardless of game outcome. Focus on consistent producers with conservative lines based on their season averages from the stats provided.]"""

        return prompt

    @staticmethod
    def build_ev_singles_prompt(
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
        """Build EV+ singles prompt with Kelly Criterion stake sizing.

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
        prompt = f"""You are an expert {sport_components.sport_name} Expected Value (EV+) betting analyst specializing in finding mispriced lines.

MATCHUP: {team_a} @ {team_b}
HOME TEAM: {home_team}

OBJECTIVE:
Identify the TOP 5 individual bets with the highest positive expected value (EV+). Use only given data and context, no outside sources.
Calculate optimal stake sizing using Kelly Criterion.

METHODOLOGY:

1. CONVERT ODDS TO IMPLIED PROBABILITY:
   - Positive odds: 100 / (odds + 100)
     Example: +150 = 100 / (150 + 100) = 40.0%

2. ESTIMATE TRUE PROBABILITY (from stats):
   - Analyze: season averages, recent trends (last 3 games), matchup history
   - Consider: home/away splits, opponent defense rank, weather, injuries
   - BE CONSERVATIVE: Account for variance and regression to mean
   - Reduce raw estimates by 10-15% for safety
   - Example: Player averages 285 pass yards, favorable matchup → estimate 58% (not 70%)

3. CALCULATE EXPECTED VALUE:
   - Convert to decimal odds: Negative: (100 / |odds|) + 1, Positive: (odds / 100) + 1
   - EV = (True Prob × Decimal Odds) - 1
   - Convert to percentage: EV% = EV × 100
   - MINIMUM THRESHOLD: +3.0% EV to qualify

4. KELLY CRITERION (stake sizing):
   - Full Kelly = (True Prob × Decimal Odds - 1) / (Decimal Odds - 1)
   - Recommend HALF KELLY for bankroll safety
   - Example: True prob 58%, odds +150 (2.50 decimal)
     * Full Kelly = (0.58 × 2.50 - 1) / (2.50 - 1) = 0.2933 = 29.3%
     * Half Kelly = 14.7% of bankroll (recommended)

REQUIREMENTS:
- Exactly 5 individual bets (NO parlays, NO duplicates, NO replacements)
- Consider ALL bet types: Moneyline, Spread, Game Totals, {sport_components.bet_types_list}
- Bet type diversity: Maximum 3 yardage props (prefer different categories when possible)
- Conservative probability estimates (reduce raw estimates by 10-15% for safety)
- Only healthy players with consistent stats (8+ games preferred)
{sport_components.injury_instructions}
- Analyze opportunities from BOTH teams

EVALUATING DIFFERENT BET TYPES:
- Moneyline/Spread: Estimate team win probability from power ratings, scoring differential, home/away splits, injury impact
- Anytime TD: Use TD rate per game, red zone touches, goal-line role, opponent red zone defense rank
- Receptions/Attempts: Volume-based (more predictable than yardage), check target share, carry share, usage rate
- Game Totals: Estimate team totals based on offensive/defensive efficiency, pace of play, weather conditions

DATA:
{data_context}

VALIDATION REQUIREMENTS:
- You MUST return exactly 5 bets - no more, no less
- NO "NOTE" sections, NO self-corrections, NO replacement bets
- If you cannot find 5 qualifying bets, return fewer and explain why in GAME ANALYSIS

OUTPUT FORMAT (exactly 5 bets, ranked by EV highest to lowest):

## Bet 1: [Highest EV+]
**Bet**: [Full description with exact line, e.g., "Patrick Mahomes Over 250.5 Passing Yards"]
**Odds**: [American odds, must be positive e.g., "+150"]
**Implied Probability**: [X.X%]
**True Probability**: [Y.Y%]
**Expected Value**: [+Z.Z%]
**Kelly Criterion**: [K.K%] full Kelly (recommend half: [H.H%] of bankroll)

## Bet 2: [Second Highest EV+]
**Bet**: [Full description with line]
**Odds**: [Positive American odds]
**Implied Probability**: [X.X%]
**True Probability**: [Y.Y%]
**Expected Value**: [+Z.Z%]
**Kelly Criterion**: [K.K%] full Kelly (recommend half: [H.H%])

## Bet 3: [Third Highest EV+]
**Bet**: [Full description with line]
**Odds**: [Positive American odds]
**Implied Probability**: [X.X%]
**True Probability**: [Y.Y%]
**Expected Value**: [+Z.Z%]
**Kelly Criterion**: [K.K%] full Kelly (recommend half: [H.H%])

## Bet 4: [Fourth Highest EV+]
**Bet**: [Full description with line]
**Odds**: [Positive American odds]
**Implied Probability**: [X.X%]
**True Probability**: [Y.Y%]
**Expected Value**: [+Z.Z%]
**Kelly Criterion**: [K.K%] full Kelly (recommend half: [H.H%])

## Bet 5: [Fifth Highest EV+]
**Bet**: [Full description with line]
**Odds**: [Positive American odds]
**Implied Probability**: [X.X%]
**True Probability**: [Y.Y%]
**Expected Value**: [+Z.Z%]
**Kelly Criterion**: [K.K%] full Kelly (recommend half: [H.H%])

## GAME ANALYSIS & REASONING
[2-3 paragraphs explaining:
1. Overall matchup dynamics and key statistical edges for this game
2. Why these specific 5 bets represent the highest EV opportunities (reference specific stats)
3. Common factors across the selected bets (game script expectations, defensive weaknesses, weather, etc.)
4. Any important context: injuries, trends, or why certain popular bets were excluded]

FINAL REMINDERS:
- Show ALL calculations explicitly
- Be conservative with true probabilities (account for variance and small samples)
- Reference SPECIFIC stats (e.g., "averages 78.5 yards last 5 games")
- Never recommend more than half Kelly for any single bet"""

        return prompt
