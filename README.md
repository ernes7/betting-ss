# Sports Betting Analysis Tool

AI-powered betting analysis system for multi-sport support. Combines web scraping with Claude AI to generate data-driven parlays.

## Features

- **Extensible OOP Architecture**: Plug-and-play system for adding new sports (~150 lines of config)
- **Automated Data Extraction**: Scrapes rankings, team profiles, and injury reports from sports-reference sites
- **AI Analysis**: Claude Sonnet 4.5 generates 3-parlay predictions (80-95% confidence thresholds)
- **Smart Caching**: Metadata tracking avoids redundant scraping (once per day limit)
- **Rich CLI**: Interactive team selection with markdown-rendered predictions

## Supported Sports

- **NFL** (32 teams) - Pro-Football-Reference.com
- **NBA** (30 teams) - Basketball-Reference.com

## Architecture

```
shared/              # Base classes & utilities (Scraper, Predictor, PromptBuilder)
├── base/            # Abstract sport interfaces
├── utils/           # Reusable components (metadata, web scraping, file I/O)
└── factory.py       # Sport instantiation

nfl/                 # NFL implementation
├── nfl_config.py    # Sport configuration (~65 lines)
├── prompt_components.py  # NFL-specific bet types (~85 lines)
└── data/            # Scraped rankings & profiles

nba/                 # NBA implementation (same pattern)
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

Select sport → week → teams → home team → get AI-generated parlays

## Adding New Sports (NHL/MLB)

1. Create `{sport}/{sport}_config.py` implementing `SportConfig` interface
2. Create `{sport}/prompt_components.py` with sport-specific bet types
3. Register in `shared/register_sports.py`

**Total: ~150 lines** (vs ~1200 lines without OOP architecture)
