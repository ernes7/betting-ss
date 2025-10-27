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
        # Optimize team profiles to reduce token usage
        optimized_profile_a = optimize_team_profile(profile_a)
        optimized_profile_b = optimize_team_profile(profile_b)

        # Build comprehensive data context
        data_context = f"""{team_a.upper()} RANKING STATS:
{json.dumps(team_a_stats, indent=2)}

{team_b.upper()} RANKING STATS:
{json.dumps(team_b_stats, indent=2)}"""

        # Add optimized profile data if available
        if optimized_profile_a:
            data_context += f"\n\n{team_a.upper()} DETAILED PROFILE:\n{json.dumps(optimized_profile_a, indent=2)}"
        if optimized_profile_b:
            data_context += f"\n\n{team_b.upper()} DETAILED PROFILE:\n{json.dumps(optimized_profile_b, indent=2)}"

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
