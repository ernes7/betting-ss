"""Extract individual team profile data from Basketball-Reference."""

import json
import os

from playwright.sync_api import sync_playwright
from ratelimit import limits, sleep_and_retry

from nba.constants import (
    CURRENT_YEAR,
    DATA_PROFILES_DIR,
    BBR_RATE_LIMIT_CALLS,
    BBR_RATE_LIMIT_PERIOD,
    TEAM_PROFILE_TABLES,
    NBA_TEAM_URL_PATTERN,
)


@sleep_and_retry
@limits(calls=BBR_RATE_LIMIT_CALLS, period=BBR_RATE_LIMIT_PERIOD)
def extract_team_profile(team_name: str, pbr_abbr: str):
    """
    Extract all profile tables for a single team.

    Args:
        team_name: Full team name (e.g., "Los Angeles Lakers")
        pbr_abbr: Basketball-Reference team abbreviation (e.g., "LAL")

    Returns:
        Dict mapping table names to extracted data
    """
    # Build team URL using pattern from constants
    url = NBA_TEAM_URL_PATTERN.format(pbr_abbr=pbr_abbr)

    print(f"\nExtracting profile data for {team_name}...")
    print(f"URL: {url}")

    # Create team-specific directory
    team_folder = team_name.lower().replace(" ", "_")
    team_dir = os.path.join(DATA_PROFILES_DIR, team_folder)
    os.makedirs(team_dir, exist_ok=True)

    extracted_data = {}
    extraction_failed = False

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # Load page once
            response = page.goto(url, wait_until="domcontentloaded", timeout=10000)

            # Check for rate limiting
            if response and response.status == 429:
                print(f"  ✗ Rate limited (HTTP 429) - cannot extract data")
                extraction_failed = True
                browser.close()
                return {}
            elif response and response.status != 200:
                print(f"  ✗ HTTP {response.status} - cannot extract data")
                extraction_failed = True
                browser.close()
                return {}

            page.wait_for_timeout(1000)  # 1 second wait for JS tables

            # Extract each table using JavaScript evaluation (fast & efficient)
            for output_name, table_id in TEAM_PROFILE_TABLES.items():
                print(f"  Extracting {output_name} (#{table_id})...")

                try:
                    # Use JavaScript evaluation for fast extraction (same as rankings)
                    table_data = page.evaluate(
                        f"""
                        () => {{
                            const table = document.getElementById('{table_id}');
                            if (!table) return null;

                            // Get table name from caption
                            const tableName = table.caption?.textContent.trim() || '';

                            // Get headers
                            const headers = [];
                            const headerRows = table.querySelectorAll('thead tr');
                            const mainHeaderRow = headerRows[headerRows.length - 1];
                            mainHeaderRow.querySelectorAll('th').forEach(th => {{
                                const dataStat = th.getAttribute('data-stat');
                                if (dataStat) {{
                                    headers.push(dataStat);
                                }}
                            }});

                            // Get rows
                            const rows = [];
                            table.querySelectorAll('tbody tr:not(.thead)').forEach(tr => {{
                                // Skip partial_table rows
                                if (tr.classList.contains('partial_table')) return;

                                const row = {{}};
                                tr.querySelectorAll('th, td').forEach((cell, index) => {{
                                    const dataStat = cell.getAttribute('data-stat');
                                    if (dataStat && headers.includes(dataStat)) {{
                                        row[dataStat] = cell.textContent.trim();
                                    }}
                                }});

                                if (Object.keys(row).length > 0) {{
                                    rows.push(row);
                                }}
                            }});

                            return {{
                                table_name: tableName,
                                headers: headers,
                                data: rows
                            }};
                        }}
                        """
                    )

                    if not table_data:
                        print(
                            f"    Warning: Table #{table_id} not found, skipping..."
                        )
                        continue

                    # Build result
                    result = table_data

                    # Save to file in team-specific folder
                    filename = f"{output_name}.json"
                    filepath = os.path.join(team_dir, filename)

                    with open(filepath, "w", encoding="utf-8") as f:
                        json.dump(result, f, indent=2, ensure_ascii=False)

                    extracted_data[output_name] = result
                    print(f"    ✓ Saved to {filepath}")

                except Exception as e:
                    print(f"    ✗ Error extracting {output_name}: {str(e)}")
                    continue

        except Exception as e:
            print(f"Error loading page for {team_name}: {str(e)}")
            return {}

        finally:
            browser.close()

    print(f"Completed profile extraction for {team_name}")

    return extracted_data
