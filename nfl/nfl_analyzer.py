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
        prompt = f"""You are an expert sports betting analyst specializing in NFL Expected Value (EV+) betting. Analyze the performance of individual bets by comparing predictions against actual game results.

**PREDICTION DATA:**
```json
{json.dumps(prediction_data, indent=2)}
```

**ACTUAL GAME RESULTS:**
```json
{json.dumps(result_data, indent=2)}
```

**YOUR TASK:**

For each bet, determine if it WON or LOST and calculate profit/loss. Keep it concise - just check hits, no detailed reasoning per bet.

**BET EVALUATION RULES:**

1. **Player Props (Over/Under)**
   - Extract player name, stat type, and line
   - Find player's actual stats in results tables
   - Compare actual to line → WIN or LOSS

2. **Stat Locations:**
   - Passing yards/TDs: tables.passing → pass_yds, pass_td
   - Rushing yards/TDs: tables.rushing → rush_yds, rush_td
   - Receiving yards/TDs/Receptions: tables.receiving → rec_yds, rec_td, rec
   - Combined yards: Sum rush_yds + rec_yds

3. **Profit/Loss:**
   - Bet amount: ${FIXED_BET_AMOUNT} per bet
   - **WON**: Profit = ${FIXED_BET_AMOUNT} × (Odds / 100)
   - **LOST**: Profit = -${FIXED_BET_AMOUNT}

**OUTPUT FORMAT:**

Return valid JSON (no reasoning per bet, just actual value):

```json
{{
  "bet_results": [
    {{
      "rank": 1,
      "bet": "Patrick Mahomes Over 250.5 Passing Yards",
      "odds": 150,
      "ev_percent": 8.5,
      "won": true,
      "actual_value": "299 pass yards",
      "predicted_line": 250.5,
      "actual_numeric": 299,
      "stat_type": "passing_yards",
      "direction": "over",
      "stake": {FIXED_BET_AMOUNT},
      "profit": 150.00
    }},
    {{
      "rank": 2,
      "bet": "Travis Kelce Under 65.5 Receiving Yards",
      "odds": 120,
      "ev_percent": 5.2,
      "won": false,
      "actual_value": "99 rec yards",
      "predicted_line": 65.5,
      "actual_numeric": 99,
      "stat_type": "receiving_yards",
      "direction": "under",
      "stake": {FIXED_BET_AMOUNT},
      "profit": -100.00
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
    "realized_ev": 3.5,
    "avg_margin": 18.5,
    "avg_margin_won": 42.3,
    "avg_margin_lost": -25.0,
    "max_margin": 78.5,
    "min_margin": -45.0,
    "close_calls": 1
  }},
  "insights": [
    "3/5 bets hit (60% win rate, +42% ROI)",
    "Passing props 2/2, rushing props 1/2, receiving props 0/1",
    "EV estimates were accurate - predicted +6.2%, realized +3.5%",
    "True probability calibration was good across bet types"
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
- `avg_margin`: Average of all margin values (actual_numeric - predicted_line)
- `avg_margin_won`: Average margin for winning bets only
- `avg_margin_lost`: Average margin for losing bets only (will be negative)
- `max_margin`: Largest margin (best performance)
- `min_margin`: Smallest margin (worst performance)
- `close_calls`: Count of bets within ±10 units of the line

**IMPORTANT INSTRUCTIONS:**
1. Return ONLY the JSON object, no markdown code blocks, no extra text
2. Ensure all JSON is valid and properly formatted
3. Be thorough in checking all stats tables for player data
4. Handle player name variations (e.g., check both full name and abbreviated)
5. For each bet, extract these fields:
   - `actual_value`: Human-readable (e.g., "299 pass yards")
   - `predicted_line`: Extract number from bet (e.g., "Over 250.5" → 250.5)
   - `actual_numeric`: Player's actual stat value (e.g., 299)
   - `stat_type`: e.g., "passing_yards", "rushing_yards", "receiving_yards", "receptions"
   - `direction`: "over" or "under" (extracted from bet description)
6. Calculate profit/loss accurately using the formula above
7. Round profit values to 2 decimal places
8. Generate 3-5 concise insights about overall prediction performance (not individual bets)

Now analyze the predictions:"""

        return prompt
