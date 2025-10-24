# Sports Betting Analysis Tool

AI-powered betting analysis system that combines web scraping with Claude AI to generate data-driven betting predictions and parlays.

## Features

- Automated stats extraction from official sports websites
- AI-powered game analysis using Claude Sonnet 4.5
- Smart parlay generation with confidence ratings
- Rich CLI interface with progress tracking
- Metadata tracking to avoid redundant data fetching

## Supported Sports

- **NFL**: Full support with rankings, team profiles, and injury reports

## Planned Sports

- NHL (Coming soon)
- NBA (Coming soon)

## Setup

1. Clone the repository
2. Install dependencies: `poetry install`
3. Install Playwright browsers: `playwright install chromium`
4. Create `.env` file with your Anthropic API key: `ANTHROPIC_API_KEY=your_key_here`

## Usage

Run the CLI: `python cli.py`

The tool will guide you through selecting teams and generating predictions.

## Project Structure

- `nfl/` - NFL-specific modules and data
- `cli.py` - Main CLI entry point
