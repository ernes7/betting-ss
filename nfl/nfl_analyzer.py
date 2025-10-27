"""NFL-specific prediction analyzer implementation."""

import json

from shared.base.analyzer import BaseAnalyzer


class NFLAnalyzer(BaseAnalyzer):
    """NFL prediction analyzer using Claude AI.

    Analyzes NFL game predictions against actual results to determine:
    - Which parlays hit or missed
    - Which individual bets/legs hit or missed
    - Margin of error for close misses
    - Summary statistics and insights

    Uses Claude Sonnet 4.5 by default for high-accuracy analysis.
    """

    def _build_analysis_prompt(self, prediction_data: dict, result_data: dict) -> str:
        """Build NFL-specific analysis prompt for Claude.

        Args:
            prediction_data: Prediction JSON with parlays and bets
            result_data: Result JSON with final score and stats tables

        Returns:
            Formatted prompt string for Claude AI
        """
        prompt = f"""You are an expert sports betting analyst specializing in NFL games. Your task is to analyze prediction accuracy by comparing predicted bets against actual game results.

**PREDICTION DATA:**
```json
{json.dumps(prediction_data, indent=2)}
```

**ACTUAL GAME RESULTS:**
```json
{json.dumps(result_data, indent=2)}
```

**YOUR ANALYSIS TASK:**

For each parlay and each individual bet within that parlay, determine if it HIT or MISSED based on the actual game data.

**CRITICAL PARLAY RULE:**
- A parlay ONLY hits if ALL legs hit
- If even ONE leg misses, the ENTIRE parlay misses
- Example: 3/4 legs hit = PARLAY MISSED (not hit)

**BET TYPES AND EVALUATION RULES:**

1. **Moneyline Bets**
   - Check which team won based on final score
   - Example: "Los Angeles Chargers Moneyline" hits if Chargers won

2. **Spread Bets**
   - Check if team covered the spread
   - Example: "Chargers -3.5" hits if Chargers won by 4+ points

3. **Player Prop Bets (Over/Under)**
   - Extract player name, stat type, and line from bet text
   - Find player's actual stats in the results tables
   - Compare actual value to the line
   - Example: "Justin Herbert Over 265.5 passing yards"
     - Look for Justin Herbert in passing stats table
     - Check if pass_yds > 265.5

4. **Team/Game Total Bets**
   - Sum appropriate stats from team_stats or scoring tables
   - Example: "Over 45.5 total points" → Check if (away_score + home_score) > 45.5

5. **Other Prop Bets**
   - Use your intelligence to interpret the bet and find relevant stats
   - Examples: "Over 1.5 field goals", "Over 0.5 sacks", etc.

**MARGIN CALCULATION:**
- For numeric props, calculate: actual_value - predicted_line
- For percentage margin: ((actual_value - predicted_line) / predicted_line) * 100
- Mark bets with margin within ±5% as "close miss/hit"

**PARLAY-LEVEL REASONING:**
For each parlay, provide overall strategic analysis:
- How did game flow/script affect the parlay?
- Did the legs work together or conflict?
- Was the original confidence justified?
- What was the key factor that made it hit/miss?
- Strategic insights about the bet construction

**OUTPUT FORMAT:**

Return a valid JSON object with this exact structure:

```json
{{
  "parlay_results": [
    {{
      "parlay_name": "Parlay 1: Los Angeles Chargers Wins",
      "original_confidence": 82,
      "hit": false,
      "legs_hit": 2,
      "legs_total": 4,
      "hit_rate": 50.0,
      "potential_payout_odds": null,
      "parlay_reasoning": "This parlay was built around a Chargers victory, which materialized as predicted. However, the blowout game script (37-10) created a conflict between the moneyline/total points legs (which benefited from the scoring) and the passing volume prop (Herbert Over 265.5 yards). Once the Chargers established a commanding lead, they shifted to a run-heavy attack with 43 rush attempts, limiting Herbert's passing opportunities. The parlay failed because the very success of the moneyline prediction (dominant win) undermined the passing prop. This demonstrates the importance of considering how different legs interact under various game scripts.",
      "legs": [
        {{
          "bet": "Los Angeles Chargers Moneyline",
          "hit": true,
          "actual_value": "Chargers won 37-10",
          "margin": null,
          "margin_pct": null,
          "reasoning": "Chargers won convincingly with 27-point victory"
        }},
        {{
          "bet": "Justin Herbert Over 265.5 passing yards",
          "hit": false,
          "actual_value": "227 passing yards",
          "margin": -38.5,
          "margin_pct": -14.5,
          "reasoning": "Herbert completed 18/25 for 227 yards, fell short by 38.5 yards. Game script favored running (blowout)."
        }},
        {{
          "bet": "Ladd McConkey Over 5.5 receptions",
          "hit": true,
          "actual_value": "6 receptions",
          "margin": 0.5,
          "margin_pct": 9.1,
          "reasoning": "McConkey had 6 catches on 10 targets for 88 yards and 1 TD"
        }},
        {{
          "bet": "Over 45.5 total points",
          "hit": true,
          "actual_value": "47 total points",
          "margin": 1.5,
          "margin_pct": 3.3,
          "reasoning": "Final score 37-10 = 47 points, just barely exceeded the line"
        }}
      ]
    }}
  ],
  "summary": {{
    "parlays_hit": 1,
    "parlays_total": 3,
    "parlay_hit_rate": 33.3,
    "total_legs": 12,
    "legs_hit": 8,
    "legs_hit_rate": 66.7,
    "avg_confidence_hit_parlays": 95.0,
    "avg_confidence_miss_parlays": 82.5,
    "close_misses": 2
  }},
  "insights": [
    "High confidence parlays (95%+) had 100% hit rate (1/1)",
    "Player passing yardage props underperformed due to blowout game script",
    "Moneyline and spread bets were highly accurate (3/3)",
    "Team total overs hit at 67% rate (2/3)"
  ]
}}
```

**IMPORTANT INSTRUCTIONS:**
1. Return ONLY the JSON object, no markdown code blocks, no extra text
2. Ensure all JSON is valid and properly formatted
3. Be thorough in checking all stats tables for player data
4. Provide clear, specific reasoning for EACH BET (leg-level reasoning)
5. Provide strategic reasoning for EACH PARLAY (parlay-level reasoning about game flow, leg interactions, confidence justification)
6. Calculate margins accurately for close calls
7. Generate 3-5 actionable insights about prediction performance

Now analyze the predictions:"""

        return prompt
