"""NBA-specific prompt components for betting analysis."""


class NBAPromptComponents:
    """NBA-specific prompt components that get injected into shared template."""

    sport_name = "NBA"

    bet_types_list = """  * Player points O/U (e.g., "LeBron James Over 25.5 points")
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
  * Highest scoring quarter (e.g., "4th Quarter highest scoring")"""

    restrictions = """- DO NOT use combined props (combined assists, combined rebounds, etc.)
- DO NOT use team total steals/blocks (only individual player props available)
- DO NOT use team three-pointers made (use individual player 3PM instead)"""

    injury_instructions = """- CRITICAL: Check the injuries table for BOTH teams before suggesting ANY player props
- DO NOT include any player with injury status (Out, Questionable, Doubtful, etc.) in prop bets
- Injured players should ONLY be mentioned in reasoning to explain team weaknesses/strengths"""

    stat_tables_to_analyze = "per_game_stats, totals_stats, team_and_opponent, adj_shooting, shooting, injuries"

    important_notes = "IMPORTANT: Check injuries data to exclude all injured players from prop bets."
