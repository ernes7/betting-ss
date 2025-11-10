"""NFL-specific prompt components for betting analysis."""


class NFLPromptComponents:
    """NFL-specific prompt components that get injected into shared template."""

    sport_name = "NFL"

    bet_types_list = """  * Moneyline - underdog wins with positive odds (e.g., "Panthers ML +625", "Bears ML +124")
  * Spread - underdog covers with positive odds (e.g., "Panthers +12.5 -102", "Vikings +8.5 -105")
  * QB passing yards O/U (e.g., "Justin Herbert Over 265.5 passing yards")
  * RB rushing yards O/U (e.g., "Aaron Jones Over 55.5 rushing yards")
  * WR receiving yards O/U (e.g., "Justin Jefferson Over 75.5 receiving yards")
  * Player receptions O/U (e.g., "Justin Jefferson Over 6.5 receptions")
  * QB pass completions O/U (e.g., "Justin Herbert Over 22.5 completions")
  * QB pass attempts O/U (e.g., "Justin Herbert Over 35.5 attempts")
  * Player rush attempts O/U (e.g., "Aaron Jones Over 18.5 rush attempts")
  * Player anytime TD / touchdown scorers (e.g., "Justin Jefferson anytime TD", "Cole Kmet anytime TD +340")
  * Individual defensive player sacks O/U (PLAYER SPECIFIC ONLY - e.g., "Joey Bosa Over 0.5 sacks")
  * Defensive player tackles + assists O/U (e.g., "Roquan Smith Over 8.5 tackles+assists")
  * Individual defensive player interceptions O/U (PLAYER SPECIFIC ONLY - e.g., "Sauce Gardner Over 0.5 interceptions")
  * Game total points O/U (e.g., "Over 45.5 total points")
  * Field goals O/U (e.g., "Over 3.5 field goals")"""

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
    afc_standings, nfc_standings, passing_offense, rushing_offense, scoring_offense,
  team_offense

  TEAM PROFILE TABLES (per team, optimized):
    - Full tables: team_stats, schedule_results, injury_report
    - Filtered tables: passing (top 2 QBs), top_rushers (top 5), top_receivers (top 5),
  defense_fumbles (top 10)
  """

    conservative_line_rules = """CONSERVATIVE LINE SELECTION (CRITICAL):
- Yardage props (passing/rushing/receiving yards): Pick lines 30% BELOW player's season average
  Example: Player averages 100 yards → Target line at 70.5 or lower
- Volume props (completions, attempts, receptions, targets, rush attempts): Pick lines 25% BELOW player's average
  Example: Player averages 20 completions → Target line at 15.5 or lower
- Game totals: Pick numbers with 15+ point cushion from expected total
  Example: Expected 48 points → Pick Over 33.5 or Under 63.5
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
