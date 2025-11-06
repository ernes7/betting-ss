# Sports Betting Analysis Tool

AI-powered EV+ betting analytics platform. Identifies profitable betting opportunities (+3% minimum EV, typically 3-15%) using Claude Sonnet 4.5, optimal stake sizing via Kelly Criterion, and comprehensive P&L tracking.

## Features

- **EV+ Analysis**: Finds positive expected value bets by comparing AI-predicted probability vs bookmaker odds
- **Kelly Criterion**: Calculates optimal bet sizing (full/half Kelly) to maximize long-term growth
- **Automated Pipeline**: Scrapes team rankings, profiles, injury reports, and DraftKings betting odds
- **AI-Powered Predictions**: Claude Sonnet 4.5 analyzes 40K+ tokens to generate top 5 EV+ bets
- **P&L Tracking**: Post-game analysis with ROI, win rate, and realized edge calculations
- **Streamlit Dashboard**: Interactive web UI with profit charts, filterable predictions, and analysis overlay
- **Rich CLI**: Terminal interface with markdown-rendered predictions and interactive menus

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

### CLI Interface
```bash
poetry run python cli.py
```

**Workflow**: Select sport → Scrape rankings/profiles → Provide DraftKings odds URL → Generate EV+ predictions → Fetch results → Analyze P&L

### Streamlit Dashboard
```bash
streamlit run streamlit/app.py
```

**Features**: View all predictions, filter by date/status, visualize profits with interactive charts, analyze bet-by-bet results

## Output Examples

**EV+ Predictions**: Top 5 individual bets ranked by expected value (+3% minimum), Kelly Criterion full/half stakes, implied vs true probability, reasoning for each edge

**P&L Analysis**: Win/loss per bet, profit/loss at $100 fixed stake, total ROI, win rate, realized vs predicted edge, accuracy insights

## Adding New Sports (NHL/MLB)

1. Create `{sport}/{sport}_config.py` implementing `SportConfig` interface
2. Create `{sport}/prompt_components.py` with EV-focused bet types
3. Create `{sport}/{sport}_analyzer.py` extending `BaseAnalyzer`
4. Register in `shared/register_sports.py`
