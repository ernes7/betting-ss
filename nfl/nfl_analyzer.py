"""NFL prediction analyzer implementation - EV+ betting analysis with repositories."""

import json

from shared.base.analyzer import BaseAnalyzer
from shared.base.sport_config import SportConfig
from shared.repositories import PredictionRepository, ResultsRepository, AnalysisRepository
from nfl.constants import FIXED_BET_AMOUNT


class NFLAnalyzer(BaseAnalyzer):
    """NFL prediction analyzer using Claude AI.

    Analyzes NFL predictions against actual results to determine:
    - Which individual bets won or lost
    - Profit/loss for each bet (using fixed bet amount and American odds)
    - Total profit/loss, ROI, win rate
    - Insights about prediction accuracy and value

    Uses Claude Sonnet 4.5 by default for high-accuracy analysis.
    """

    def __init__(self, config: SportConfig, model: str = "claude-sonnet-4-5-20250929"):
        """Initialize analyzer with sport configuration.

        Args:
            config: Sport configuration object implementing SportConfig interface
            model: Claude model to use (default: claude-sonnet-4-5-20250929)
        """
        # Call parent init (which initializes repositories)
        super().__init__(config, model)

        # Repositories use default paths (predictions/, analysis/)
        sport_code = config.sport_name.lower()
        self.prediction_repo = PredictionRepository(sport_code)
        self.analysis_repo = AnalysisRepository(sport_code)
        # results_repo remains the same (results are shared)

    def _build_analysis_prompt(self, prediction_data: dict, result_data: dict) -> str:
        """Build NFL-specific analysis prompt for Claude.

        Args:
            prediction_data: Prediction JSON with 5 individual bets
            result_data: Result JSON with final score and stats tables

        Returns:
            Formatted prompt string for Claude AI
        """
        prompt = f"""You are an expert sports betting analyst specializing in NFL Expected Value (EV+) betting. Your task is to analyze the performance of 5 individual bets by comparing predictions against actual game results and calculating profit/loss.

**PREDICTION DATA:**
```json
{json.dumps(prediction_data, indent=2)}
```

**ACTUAL GAME RESULTS:**
```json
{json.dumps(result_data, indent=2)}
```

**YOUR ANALYSIS TASK:**

For each of the 5 individual bets, determine if it WON or LOST and calculate the profit/loss.

**BET EVALUATION RULES:**

1. **Player Prop Bets (Over/Under)**
   - Extract player name, stat type, and line from bet text
   - Find player's actual stats in the results tables
   - Compare actual value to the line
   - Example: "Patrick Mahomes Over 250.5 Passing Yards"
     - Look for Patrick Mahomes in passing stats table
     - Check if pass_yds > 250.5
     - If YES: bet WON
     - If NO: bet LOST

2. **Common Stat Types and Where to Find Them:**
   - **Passing yards**: tables.passing → pass_yds column
   - **Passing TDs**: tables.passing → pass_td column
   - **Rushing yards**: tables.rushing → rush_yds column
   - **Rushing TDs**: tables.rushing → rush_td column
   - **Receiving yards**: tables.receiving → rec_yds column
   - **Receptions**: tables.receiving → rec column
   - **Receiving TDs**: tables.receiving → rec_td column
   - **Rushing + Receiving yards**: Sum rush_yds + rec_yds

3. **Profit/Loss Calculation:**
   - Fixed bet amount: ${FIXED_BET_AMOUNT} per bet
   - **If bet WON:**
     - Profit = ${FIXED_BET_AMOUNT} × (American Odds / 100)
     - Example: Odds +150 → Profit = $100 × (150/100) = $150.00
   - **If bet LOST:**
     - Profit = -${FIXED_BET_AMOUNT}
     - Example: Profit = -$100.00

4. **Important Notes:**
   - All bets use POSITIVE American odds (e.g., +100, +150, +200)
   - Be thorough in checking all stats tables for player data
   - Handle player name variations (e.g., "Patrick Mahomes" vs "P. Mahomes")

**OUTPUT FORMAT:**

Return a valid JSON object with this exact structure:

```json
{{
  "bet_results": [
    {{
      "rank": 1,
      "bet": "Patrick Mahomes Over 250.5 Passing Yards",
      "odds": 150,
      "ev_percent": 8.5,
      "implied_probability": 40.0,
      "true_probability": 58.0,
      "kelly_half": 14.7,
      "won": true,
      "actual_value": "299 passing yards",
      "stake": {FIXED_BET_AMOUNT},
      "profit": 150.00,
      "reasoning": "Mahomes completed 25/34 passes for 299 yards, clearing the 250.5 line by 48.5 yards. The Chiefs' passing attack was productive throughout the game."
    }},
    {{
      "rank": 2,
      "bet": "Travis Kelce Under 65.5 Receiving Yards",
      "odds": 120,
      "ev_percent": 5.2,
      "implied_probability": 45.5,
      "true_probability": 62.0,
      "kelly_half": 11.8,
      "won": false,
      "actual_value": "99 receiving yards",
      "stake": {FIXED_BET_AMOUNT},
      "profit": -100.00,
      "reasoning": "Kelce had 6 receptions for 99 yards, exceeding the 65.5 line by 33.5 yards. He was heavily targeted in the passing game."
    }}
  ],
  "summary": {{
    "total_bets": 5,
    "bets_won": 3,
    "bets_lost": 2,
    "win_rate": 60.0,
    "total_profit": 210.00,
    "total_staked": 500.00,
    "roi_percent": 42.0,
    "avg_predicted_ev": 6.2,
    "realized_ev": 3.5
  }},
  "insights": [
    "3 of 5 bets hit for 60% win rate and +42% ROI",
    "Passing yard props outperformed (2/2 winners)",
    "True probability estimates were conservative but accurate",
    "Recommended Kelly stakes would have yielded optimal returns"
  ]
}}
```

**SUMMARY CALCULATIONS:**
- `total_bets`: Count of all bets (always 5)
- `bets_won`: Count of bets where won = true
- `bets_lost`: Count of bets where won = false
- `win_rate`: (bets_won / total_bets) × 100
- `total_profit`: Sum of all profit values (can be negative)
- `total_staked`: total_bets × ${FIXED_BET_AMOUNT}
- `roi_percent`: (total_profit / total_staked) × 100
- `avg_predicted_ev`: Average of all ev_percent values from prediction
- `realized_ev`: Actual edge realized based on results

**IMPORTANT INSTRUCTIONS:**
1. Return ONLY the JSON object, no markdown code blocks, no extra text
2. Ensure all JSON is valid and properly formatted
3. Be thorough in checking all stats tables for player data
4. Handle player name variations (e.g., check both full name and abbreviated)
5. Provide clear, specific reasoning for EACH BET explaining the actual stats
6. Calculate profit/loss accurately using the formula above
7. Round profit values to 2 decimal places
8. Generate 3-5 actionable insights about EV+ prediction performance

Now analyze the predictions:"""

        return prompt
