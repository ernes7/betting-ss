"""Configuration module for betting analysis system."""

from .api_config import (
    CLAUDE_MODEL,
    CLAUDE_MODEL_ALIAS,
    CLAUDE_INPUT_COST_PER_MTOK,
    CLAUDE_OUTPUT_COST_PER_MTOK,
    MAX_TOKENS,
    TEMPERATURE,
    calculate_api_cost,
    format_cost_display,
)

from .scraping_config import (
    SPORTS_REFERENCE_RATE_LIMIT_CALLS,
    SPORTS_REFERENCE_RATE_LIMIT_PERIOD,
    DRAFTKINGS_RATE_LIMIT_CALLS,
    DRAFTKINGS_RATE_LIMIT_PERIOD,
    BROWSER_HEADLESS,
    BROWSER_TIMEOUT,
    PAGE_LOAD_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY,
)

from .paths_config import (
    DATA_DIR_TEMPLATE,
    PATH_TEMPLATES,
    FILE_TEMPLATES,
    get_data_path,
    get_file_path,
    ensure_directory,
    ensure_parent_directory,
    get_metadata_path,
)

__all__ = [
    # API config
    "CLAUDE_MODEL",
    "CLAUDE_MODEL_ALIAS",
    "CLAUDE_INPUT_COST_PER_MTOK",
    "CLAUDE_OUTPUT_COST_PER_MTOK",
    "MAX_TOKENS",
    "TEMPERATURE",
    "calculate_api_cost",
    "format_cost_display",
    # Scraping config
    "SPORTS_REFERENCE_RATE_LIMIT_CALLS",
    "SPORTS_REFERENCE_RATE_LIMIT_PERIOD",
    "DRAFTKINGS_RATE_LIMIT_CALLS",
    "DRAFTKINGS_RATE_LIMIT_PERIOD",
    "BROWSER_HEADLESS",
    "BROWSER_TIMEOUT",
    "PAGE_LOAD_TIMEOUT",
    "MAX_RETRIES",
    "RETRY_DELAY",
    # Paths config
    "DATA_DIR_TEMPLATE",
    "PATH_TEMPLATES",
    "FILE_TEMPLATES",
    "get_data_path",
    "get_file_path",
    "ensure_directory",
    "ensure_parent_directory",
    "get_metadata_path",
]
