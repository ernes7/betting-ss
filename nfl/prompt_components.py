"""NFL-specific prompt components for betting analysis."""


class NFLPromptComponents:
    """NFL-specific prompt components that get injected into shared template."""

    sport_name = "NFL"

    bet_types_list = """  * Moneyline - underdog wins with positive odds (e.g., "Panthers ML +625", "Bears ML +124")
  * Spread - underdog covers with positive odds (e.g., "Panthers +12.5 -102", "Vikings +8.5 -105")
  * QB passing yards Over/Uunder
  * RB rushing yards Over/Uunder
  * WR receiving yards Oover/Under
  * Player receptions Over/Under
  * QB pass completions Over/Under
  * QB pass attempts Over/Under
  * Player rush attempts Over/Under
  * Player anytime TD / touchdown scorers
  * Individual defensive player sacks Over/Under
  * Defensive player tackles + assists Over/Under
  * Game total points Over/Under"""

    restrictions = """- DO NOT use combined props (combined passing attempts, combined rush attempts, etc.)
- DO NOT use game total touchdowns (not available on Hard Rock)
- DO NOT use team/combined sacks (only individual player sacks available)
- DO NOT use team/combined interceptions (only individual player interceptions available)
- DO NOT use penalty bets (team penalties, etc.)"""

    injury_instructions = """- CRITICAL: Check the injury_report table for BOTH teams before suggesting ANY player props
- DO NOT include any player with injury status (Out, Questionable, Doubtful, etc.) in prop bets
- Injured players should ONLY be mentioned in reasoning to explain team weaknesses/strengths"""

    stat_tables_to_analyze = """
  RANKING TABLES (league-wide, 2 teams extracted with rank/percentile):
    OFFENSE: afc_standings, nfc_standings, passing_offense, rushing_offense, scoring_offense, team_offense
    DEFENSE: team_defense, passing_defense, rushing_defense, advanced_defense

  TEAM PROFILE TABLES (per team, optimized):
    - Full tables: team_stats, schedule_results, injury_report
    - Filtered tables: passing (top 2 QBs), top_rushers (top 5), top_receivers (top 5),
  defense_fumbles (top 10)
  """

    conservative_line_rules = """CONSERVATIVE LINE SELECTION (CRITICAL):
- Yardage props (passing/rushing/receiving yards): Pick lines 30% BELOW player's season average
- Volume props (completions, attempts, receptions, targets, rush attempts): Pick lines 25% BELOW player's average
- AVOID tight lines even if "likely" - we need CERTAINTY not likelihood
- Better to have ultra-safe props than risky ones"""

    game_script_rules = """GAME SCRIPT AWARENESS - AVOID CONFLICTING CORRELATIONS:
❌ NEVER combine:
  - "Favorite wins big" + "Favorite QB high passing yards" (blowouts = run clock = fewer passes)
  - "Underdog wins" + "Underdog player props assuming they're losing" (contradiction)
  - "High total points" + "Under on player yards" (high scoring = more yards)

✅ SAFE combinations:
  - "Favorite wins" + "Favorite RB rushing yards/attempts" (winning teams run more)
  - "Favorite wins" + "Underdog QB passing yards/attempts" (losing teams pass more)
  - Volume stats (attempts, receptions, targets) work with ANY game outcome
  - Defensive props (sacks, tackles) work with ANY game outcome

RULE: If betting on a blowout win, favor the WINNER's rushing props and LOSER's passing props"""

    important_notes = """IMPORTANT PRE-GAME VERIFICATION CHECKLIST:
 1. Check injury_report: Exclude all injured players from prop bets
 2. Respect elite defenses: Top 5 defenses suppress featured player production"""
