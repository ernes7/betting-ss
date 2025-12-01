# Sports Betting Analysis Tool

AI-powered EV+ betting analytics platform. Identifies profitable betting opportunities (+3% minimum EV, typically 3-15%) using Claude Sonnet 4.5 and comprehensive P&L tracking.

## Features

- **EV+ Analysis**: Finds positive expected value bets by comparing AI-predicted probability vs bookmaker odds
- **Automated Pipeline**: Scrapes team rankings, profiles, injury reports, and DraftKings betting odds
- **AI-Powered Predictions**: Claude Sonnet 4.5 analyzes 40K+ tokens to generate top 5 EV+ bets
- **P&L Tracking**: Post-game analysis with ROI, win rate, and realized edge calculations
- **Streamlit Dashboard**: Interactive web UI with profit charts, filterable predictions, and analysis overlay
- **Service Architecture**: Modular OOP design with 5 independent services

## Supported Sports

- **NFL** (32 teams) - Pro-Football-Reference.com + DraftKings odds
- **NBA** (30 teams) - Coming soon for EV+ betting

## Architecture

```
betting-ss/
├── services/                # Backend services (OOP architecture)
│   ├── odds/               # Fetches betting odds from DraftKings
│   ├── prediction/         # AI and EV-based predictions
│   ├── results/            # Fetches game results
│   ├── analysis/           # Compares predictions to results
│   └── cli/                # Workflow orchestration
│
├── frontend/               # Streamlit dashboard
│   ├── app.py              # Main application
│   ├── theme.py            # Custom styling
│   ├── components/         # UI components (cards, charts, metrics)
│   ├── utils/              # Data loading, colors, helpers
│   └── tests/              # Frontend tests
│
├── shared/                 # Shared utilities
│   ├── base/               # Abstract interfaces (Predictor, Analyzer)
│   ├── config/             # Configuration management
│   ├── errors/             # Error handling
│   ├── logging/            # Per-service logging
│   ├── models/             # Data models and EV calculator
│   ├── repositories/       # Data access layer
│   ├── scraping/           # Web scraper utilities
│   └── utils/              # File I/O, validation, optimization
│
├── sports/                 # Sport-specific implementations
│   ├── nfl/
│   │   ├── data/           # Predictions, analysis, odds, results
│   │   ├── nfl_config.py   # Sport configuration
│   │   ├── nfl_analyzer.py # P&L analysis
│   │   ├── teams.py        # Team metadata
│   │   └── constants.py    # NFL constants
│   └── nba/
│       ├── data/
│       └── ...
│
├── config/                 # YAML configuration
│   └── settings.yaml       # Scraping, API, paths config
│
├── logs/                   # Service log files
├── cli.py                  # CLI entry point
└── pyproject.toml
```

## Setup

```bash
# Install dependencies
poetry install

# Install browser for web scraping
playwright install chromium

# Set up API key
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
streamlit run frontend/app.py
```

**Features**: View all predictions, filter by date/status, visualize profits with interactive charts, analyze bet-by-bet results

## Running Tests

```bash
# Run all tests
poetry run pytest

# Run specific service tests
poetry run pytest services/odds/tests/
poetry run pytest frontend/tests/

# Run with coverage
poetry run pytest --cov=services --cov=shared --cov=frontend
```

## Output Examples

**EV+ Predictions**: Top 5 individual bets ranked by expected value (+3% minimum), implied vs true probability, reasoning for each edge

**P&L Analysis**: Win/loss per bet, profit/loss at $100 fixed stake, total ROI, win rate, realized vs predicted edge, accuracy insights

## Adding New Sports (NHL/MLB)

1. Create `sports/{sport}/{sport}_config.py` implementing `SportConfig` interface
2. Create `sports/{sport}/prompt_components.py` with EV-focused bet types
3. Create `sports/{sport}/{sport}_analyzer.py` extending `BaseAnalyzer`
4. Register in `shared/register_sports.py`

## Service Architecture

| Service | Purpose | Tests |
|---------|---------|-------|
| ODDS | Fetches betting odds from DraftKings | 58 |
| PREDICTION | AI and EV-based predictions | 48 |
| RESULTS | Fetches game results | 57 |
| ANALYSIS | Compares predictions to results | 55 |
| CLI | Workflow orchestration | 23 |
| FRONTEND | Dashboard utilities | 53 |

**Total: 294 tests**
