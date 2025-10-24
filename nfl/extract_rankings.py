"""NFL Rankings Extraction Tool

Extracts all ranking tables from Pro-Football-Reference.com and converts to JSON.
"""

import json
import os
import re
from datetime import date
from pathlib import Path

from playwright.sync_api import sync_playwright
from ratelimit import limits, sleep_and_retry
from tqdm import tqdm

from nfl.constants import (
    DATA_RANKINGS_DIR,
    NFL_STATS_URL,
    PFR_RATE_LIMIT_CALLS,
    PFR_RATE_LIMIT_PERIOD,
    RANKING_TABLES,
)

# Metadata file path
RANKINGS_METADATA_FILE = os.path.join(DATA_RANKINGS_DIR, ".metadata.json")


def load_rankings_metadata() -> dict:
    """Load rankings metadata file tracking when rankings were last scraped."""
    if os.path.exists(RANKINGS_METADATA_FILE):
        try:
            with open(RANKINGS_METADATA_FILE) as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load rankings metadata file: {str(e)}")
            return {}
    return {}


def save_rankings_metadata(metadata: dict):
    """Save rankings metadata file."""
    os.makedirs(DATA_RANKINGS_DIR, exist_ok=True)
    try:
        with open(RANKINGS_METADATA_FILE, "w") as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save rankings metadata file: {str(e)}")


def was_rankings_scraped_today() -> bool:
    """Check if rankings were scraped today."""
    metadata = load_rankings_metadata()
    today = date.today().isoformat()
    return metadata.get("last_scraped") == today


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

    Uses metadata tracking to avoid scraping multiple times per day.

    Args:
        url: URL to scrape from
        output_dir: Directory where JSON files will be saved

    Returns:
        Dictionary with extraction results (success/failure counts)
    """
    # Check if rankings were already scraped today
    if was_rankings_scraped_today():
        print(f"\n{'='*70}")
        print("RANKINGS ALREADY EXTRACTED TODAY")
        print(f"{'='*70}")
        print("✓ Using existing ranking data from today")
        print("  Rankings are refreshed once per day to respect rate limits")
        print(f"{'='*70}\n")
        return {"success": [], "failed": [], "skipped": True}

    print(f"Fetching fresh ranking data from {url}...")
    results = {"success": [], "failed": [], "skipped": False}

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

    # Update metadata with today's date
    if results["success"]:
        metadata = {"last_scraped": date.today().isoformat()}
        save_rankings_metadata(metadata)

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
