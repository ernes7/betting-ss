"""NFL-specific results fetcher implementation."""

from datetime import datetime
from typing import Any
from ratelimit import limits, sleep_and_retry

from shared.base.results_fetcher import ResultsFetcher
from shared.base.sport_config import SportConfig
from shared.utils import WebScraper, TableExtractor


class NFLResultsFetcher(ResultsFetcher):
    """Fetch NFL game results from Pro-Football-Reference boxscore pages.

    Extracts:
    - Final score and winner
    - Quarter-by-quarter scoring
    - Game info (stadium, weather, officials)
    - Team statistics
    - Passing, rushing, receiving statistics
    - Defensive statistics
    - Starting lineups
    """

    def __init__(self, config: SportConfig):
        """Initialize NFL results fetcher.

        Args:
            config: NFL configuration object
        """
        super().__init__(config)
        self.web_scraper = WebScraper()

    @sleep_and_retry
    @limits(calls=1, period=5)  # 1 call per 5 seconds for Pro-Football-Reference
    def extract_game_result(self, boxscore_url: str) -> dict[str, Any]:
        """Extract final score and stats from NFL boxscore page.

        Args:
            boxscore_url: URL to the game's boxscore page on Pro-Football-Reference

        Returns:
            Dictionary with game results:
            {
                "game_date": str,
                "teams": {"away": str, "home": str},
                "final_score": {"away": int, "home": int},
                "winner": str,
                "boxscore_url": str,
                "fetched_at": str,
                "tables": {
                    "scoring": {...},
                    "game_info": {...},
                    "team_stats": {...},
                    "passing": {...},
                    "rushing": {...},
                    "receiving": {...},
                    "defense": {...},
                    "home_starters": {...},
                    "away_starters": {...}
                }
            }

        Raises:
            Exception: If game not found or critical data missing
        """
        print(f"\nFetching game result from {boxscore_url}...")

        result_data = {
            "sport": "nfl",
            "game_date": None,
            "teams": {"away": None, "home": None},
            "final_score": {"away": None, "home": None},
            "winner": None,
            "boxscore_url": boxscore_url,
            "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tables": {}
        }

        with self.web_scraper.launch() as page:
            try:
                # Navigate to boxscore page
                response = self.web_scraper.navigate_and_wait(page, boxscore_url)

                # Check for HTTP errors
                if response and response.status == 404:
                    raise Exception("Game not found (HTTP 404) - may not have been played yet")
                elif response and response.status == 429:
                    raise Exception("Rate limited (HTTP 429) - please wait and try again")
                elif response and response.status != 200:
                    raise Exception(f"HTTP {response.status} error")

                # Extract all result tables
                tables_extracted = 0
                tables_missing = []

                for table_name, table_id in self.config.result_tables.items():
                    print(f"  Extracting {table_name} (#{table_id})...")

                    table_data = TableExtractor.extract(page, table_id)

                    if table_data:
                        result_data["tables"][table_name] = table_data
                        tables_extracted += 1
                        print(f"    ✓ Extracted {len(table_data.get('data', []))} rows")
                    else:
                        tables_missing.append(table_name)
                        print(f"    ⚠ Table '#{table_id}' not found")

                # Check if we got critical tables
                if "scoring" not in result_data["tables"]:
                    raise Exception("Critical table 'scoring' not found - cannot determine final score")

                # Parse final score from scoring table
                scoring_data = result_data["tables"]["scoring"]
                self._parse_final_score(scoring_data, result_data)

                # Extract team names from scoring table headers
                self._parse_team_names(scoring_data, result_data)

                # Determine winner
                if result_data["final_score"]["away"] > result_data["final_score"]["home"]:
                    result_data["winner"] = result_data["teams"]["away"]
                elif result_data["final_score"]["home"] > result_data["final_score"]["away"]:
                    result_data["winner"] = result_data["teams"]["home"]
                else:
                    result_data["winner"] = "TIE"

                print(f"\n  ✅ Successfully extracted {tables_extracted}/{len(self.config.result_tables)} tables")
                if tables_missing:
                    print(f"  ⚠ Missing tables: {', '.join(tables_missing)}")

                print(f"  Final Score: {result_data['teams']['away']} {result_data['final_score']['away']} - "
                      f"{result_data['teams']['home']} {result_data['final_score']['home']}")
                print(f"  Winner: {result_data['winner']}")

                return result_data

            except Exception as e:
                print(f"  ❌ Error extracting game result: {str(e)}")
                raise

    def _parse_final_score(self, scoring_data: dict, result_data: dict):
        """Parse final score from scoring table.

        Args:
            scoring_data: Extracted scoring table data
            result_data: Result data dictionary to update
        """
        # The scoring table has play-by-play rows with vis_team_score and home_team_score columns
        if not scoring_data.get("data"):
            raise Exception("Scoring table has no data")

        rows = scoring_data["data"]

        if len(rows) < 1:
            raise Exception("Scoring table must have at least 1 row")

        # Get the last row which has the final scores
        last_row = rows[-1]

        # Look for vis_team_score and home_team_score columns
        away_score = None
        home_score = None

        if "vis_team_score" in last_row:
            try:
                away_score = int(last_row["vis_team_score"])
            except (ValueError, TypeError):
                pass

        if "home_team_score" in last_row:
            try:
                home_score = int(last_row["home_team_score"])
            except (ValueError, TypeError):
                pass

        if away_score is None or home_score is None:
            raise Exception("Could not parse final scores from scoring table")

        result_data["final_score"]["away"] = away_score
        result_data["final_score"]["home"] = home_score

    def _parse_team_names(self, scoring_data: dict, result_data: dict):
        """Parse team names from scoring table.

        Args:
            scoring_data: Extracted scoring table data
            result_data: Result data dictionary to update
        """
        if not scoring_data.get("data"):
            return

        rows = scoring_data["data"]

        # The scoring table has vis_team_score and home_team_score columns
        # We need to figure out which team is which by seeing which team's scoring plays
        # increase which score column

        home_team_name = None
        away_team_name = None

        # Look for scoring plays and track which team increases which score
        for i, row in enumerate(rows):
            if "team" not in row or not row["team"]:
                continue

            team = row["team"]

            # Check if this play increased vis_team_score or home_team_score
            if i > 0:
                prev_row = rows[i-1]
                curr_vis = int(row.get("vis_team_score", 0) or 0)
                prev_vis = int(prev_row.get("vis_team_score", 0) or 0)
                curr_home = int(row.get("home_team_score", 0) or 0)
                prev_home = int(prev_row.get("home_team_score", 0) or 0)

                if curr_vis > prev_vis:
                    # This team is the visiting/away team
                    away_team_name = team
                elif curr_home > prev_home:
                    # This team is the home team
                    home_team_name = team
            else:
                # First scoring play - check which score column is non-zero
                vis_score = int(row.get("vis_team_score", 0) or 0)
                home_score = int(row.get("home_team_score", 0) or 0)

                if vis_score > 0 and home_score == 0:
                    away_team_name = team
                elif home_score > 0 and vis_score == 0:
                    home_team_name = team

            # Break early if we found both teams
            if home_team_name and away_team_name:
                break

        # Assign the teams
        if away_team_name:
            result_data["teams"]["away"] = away_team_name
        if home_team_name:
            result_data["teams"]["home"] = home_team_name
