"""NFL Rankings Extraction Tool

Extracts all ranking tables from Pro-Football-Reference.com and converts to JSON.
"""

import json
import re
from pathlib import Path

from playwright.sync_api import sync_playwright
from ratelimit import limits, sleep_and_retry
from tqdm import tqdm

from constants import (
    DATA_RANKINGS_DIR,
    NFL_STATS_URL,
    PFR_RATE_LIMIT_CALLS,
    PFR_RATE_LIMIT_PERIOD,
    RANKING_TABLES,
)


def table_name_to_filename(table_name: str) -> str:
    """Convert table name to a valid filename."""
    # Remove " Table" suffix and convert to lowercase with underscores
    name = table_name.replace(" Table", "").lower()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"[\s-]+", "_", name)
    return f"{name}.json"


def extract_single_table(page, table_id: str, output_name: str, output_dir: str, pbar=None) -> bool:
    """
    Extract a single table from the page and save as JSON.

    Args:
        page: Playwright page object
        table_id: ID of the table to extract
        output_name: Name for the output file (without .json)
        output_dir: Directory where JSON will be saved
        pbar: Optional tqdm progress bar to update

    Returns:
        True if extraction succeeded, False otherwise
    """
    try:
        if pbar:
            pbar.set_description(f"Extracting {output_name}")

        table_data = page.evaluate(f"""
            () => {{
                const table = document.getElementById('{table_id}');
                if (!table) return null;

                // Get headers
                const headers = [];
                const headerRows = table.querySelectorAll('thead tr');
                const mainHeaderRow = headerRows[headerRows.length - 1];
                mainHeaderRow.querySelectorAll('th').forEach(th => {{
                    headers.push(th.getAttribute('data-stat') || th.textContent.trim());
                }});

                // Get rows
                const rows = [];
                table.querySelectorAll('tbody tr:not(.thead)').forEach(tr => {{
                    const row = {{}};
                    tr.querySelectorAll('th, td').forEach((cell, index) => {{
                        const header = headers[index];
                        if (header) {{
                            row[header] = cell.textContent.trim();
                        }}
                    }});
                    if (Object.keys(row).length > 0) {{
                        rows.push(row);
                    }}
                }});

                return {{
                    table_name: table.caption?.textContent.trim() || 'Team Stats',
                    headers: headers,
                    data: rows
                }};
            }}
        """)

        if not table_data:
            if pbar:
                pbar.write(f"  ⚠️  Table '{table_id}' not found")
            return False

        # Save to JSON
        output_path = Path(output_dir) / f"{output_name}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(table_data, f, indent=2)

        if pbar:
            pbar.write(f"  ✓ {output_name}: {len(table_data['data'])} rows")
        return True

    except Exception as e:
        if pbar:
            pbar.write(f"  ✗ Error extracting '{output_name}': {str(e)}")
        return False


@sleep_and_retry
@limits(calls=PFR_RATE_LIMIT_CALLS, period=PFR_RATE_LIMIT_PERIOD)
def extract_all_rankings(url: str = NFL_STATS_URL, output_dir: str = DATA_RANKINGS_DIR) -> dict:
    """
    Extract all ranking tables from URL in one page load.

    Args:
        url: URL to scrape from
        output_dir: Directory where JSON files will be saved

    Returns:
        Dictionary with extraction results (success/failure counts)
    """
    print(f"Navigating to {url}...")
    results = {"success": [], "failed": []}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate once
        page.goto(url, wait_until="domcontentloaded", timeout=10000)

        # Brief wait for JS-rendered tables to load
        page.wait_for_timeout(1000)

        # Extract all tables from the same page with progress bar
        with tqdm(total=len(RANKING_TABLES), desc="Extracting tables", unit="table") as pbar:
            for output_name, table_id in RANKING_TABLES.items():
                if extract_single_table(page, table_id, output_name, output_dir, pbar):
                    results["success"].append(output_name)
                else:
                    results["failed"].append(output_name)
                pbar.update(1)

        browser.close()

    # Print summary
    print(f"\n{'='*70}")
    print(f"EXTRACTION COMPLETE")
    print(f"{'='*70}")
    print(f"✓ Success: {len(results['success'])}/{len(RANKING_TABLES)} tables")
    if results["failed"]:
        print(f"✗ Failed: {', '.join(results['failed'])}")
    print(f"{'='*70}\n")

    return results


def main() -> None:
    """Main entry point for the script."""
    extract_all_rankings()


if __name__ == "__main__":
    main()
