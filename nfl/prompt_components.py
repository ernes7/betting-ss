"""NFL-specific prompt components for betting analysis."""


class NFLPromptComponents:
    """NFL-specific prompt components that get injected into shared template."""

    sport_name = "NFL"

    bet_types_list = """  * QB passing yards O/U (e.g., "Justin Herbert Over 265.5 passing yards")
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
  * Field goals O/U (e.g., "Over 3.5 field goals")"""

    restrictions = """- DO NOT use combined props (combined passing attempts, combined rush attempts, etc.)
- DO NOT use game total touchdowns (not available on Hard Rock)
- DO NOT use team/combined sacks (only individual player sacks available)
- DO NOT use team/combined interceptions (only individual player interceptions available)
- DO NOT use penalty bets (team penalties, etc.)"""

    injury_instructions = """- CRITICAL: Check the injury_report table for BOTH teams before suggesting ANY player props
- DO NOT include any player with injury status (Out, Questionable, Doubtful, etc.) in prop bets
- Injured players should ONLY be mentioned in reasoning to explain team weaknesses/strengths"""

    stat_tables_to_analyze = "team_stats, passing, rushing_receiving, defense_fumbles, touchdown_log, scoring_summary, injury_report"

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

    important_notes = "IMPORTANT: Before generating parlays, check injury_report data to exclude all injured players from prop bets."
