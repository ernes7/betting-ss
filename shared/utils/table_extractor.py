"""HTML table extraction using JavaScript evaluation."""

from playwright.sync_api import Page


class TableExtractor:
    """Extracts HTML tables using JavaScript evaluation."""

    @staticmethod
    def extract(page: Page, table_id: str) -> dict | None:
        """Extract a single table from the page using JavaScript.

        Args:
            page: Playwright page object
            table_id: ID of the HTML table to extract

        Returns:
            Dictionary with table_name, headers, and data rows, or None if table not found
        """
        try:
            table_data = page.evaluate(
                f"""
                () => {{
                    const table = document.getElementById('{table_id}');
                    if (!table) return null;

                    // Get table name from caption
                    const tableName = table.caption?.textContent.trim() || 'Stats';

                    // Get headers
                    const headers = [];
                    const headerRows = table.querySelectorAll('thead tr');
                    const mainHeaderRow = headerRows[headerRows.length - 1];
                    mainHeaderRow.querySelectorAll('th').forEach(th => {{
                        const dataStat = th.getAttribute('data-stat');
                        if (dataStat) {{
                            headers.push(dataStat);
                        }} else {{
                            headers.push(th.textContent.trim());
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
                            const header = dataStat || headers[index];
                            if (header) {{
                                row[header] = cell.textContent.trim();
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

            return table_data

        except Exception as e:
            print(f"Error extracting table '{table_id}': {str(e)}")
            return None
