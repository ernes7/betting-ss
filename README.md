# Sports Betting Analysis Tool

AI-powered betting analysis system with Expected Value (EV+) analysis and Kelly Criterion stake sizing. Combines web scraping, odds integration, and Claude AI to identify profitable betting opportunities.

## Features

- **EV+ Analysis**: Identifies positive expected value bets by comparing true probability vs implied odds
- **Kelly Criterion**: Calculates optimal bet sizing to maximize long-term growth
- **Automated Data Extraction**: Scrapes rankings, team profiles, injury reports, and betting odds
- **AI Analysis**: Claude Sonnet 4.5 generates top 5 EV+ bets ranked by expected value
- **Profit/Loss Tracking**: Analyzes actual game results to calculate P&L and ROI
- **Smart Caching**: Metadata tracking avoids redundant scraping (once per day limit)
- **Rich CLI**: Interactive menu with markdown-rendered predictions and analysis

## Supported Sports

- **NFL** (32 teams) - Pro-Football-Reference.com + DraftKings odds
- **NBA** (30 teams) - Coming soon for EV+ betting

## Architecture

```
shared/              # Base classes & utilities
├── base/            # Abstract sport interfaces (Predictor, Analyzer, PromptBuilder)
├── repositories/    # Data access layer (predictions, results, analysis)
├── services/        # Business logic (odds, profiles, metadata)
└── utils/           # Reusable components (web scraping, file I/O, optimization)

nfl/                 # NFL implementation
├── nfl_config.py    # Sport configuration
├── nfl_analyzer.py  # EV+ analysis with P&L calculation
├── prompt_components.py  # NFL-specific bet types and Kelly Criterion
├── cli_utils/       # CLI commands (predict, fetch_odds, fetch_results)
└── data/
    ├── predictions/ # EV+ predictions with Kelly stakes
    ├── analysis/    # P&L analysis results
    ├── odds/        # DraftKings betting odds
    ├── rankings/    # Team rankings & stats
    └── results/     # Game results & box scores

nba/                 # NBA implementation (stubbed for future EV+ support)
```

## Setup

```bash
poetry install
playwright install chromium
echo "ANTHROPIC_API_KEY=your_key_here" > .env
```

## Usage

```bash
poetry run python cli.py
```

### Workflow
1. **Select Sport** (NFL/NBA)
2. **Predict Game**: Enter date, select teams, provide DraftKings URL for odds
3. **Fetch Results**: Automatically analyze predictions and calculate P&L
4. **Review Analysis**: View bet-by-bet results, ROI, and insights

### EV+ Prediction Output
- Top 5 individual bets ranked by expected value
- Kelly Criterion full/half stakes for optimal bankroll management
- Implied probability vs true probability for each bet
- Game analysis explaining why these bets have edge

### P&L Analysis Output
- Win/loss status for each bet
- Profit/loss per bet (uses $100 fixed stake)
- Total ROI, win rate, and realized edge
- Insights about prediction accuracy

## Adding New Sports (NHL/MLB)

1. Create `{sport}/{sport}_config.py` implementing `SportConfig` interface
2. Create `{sport}/prompt_components.py` with EV-focused bet types
3. Create `{sport}/{sport}_analyzer.py` extending `BaseAnalyzer`
4. Register in `shared/register_sports.py`
