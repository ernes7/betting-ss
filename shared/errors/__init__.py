"""Error handling for the betting application.

Provides custom exceptions and an error handler that writes to errors.json.
When an error occurs, execution stops and details are saved for debugging.

Example:
    from shared.errors import ErrorHandler, OddsFetchError

    handler = ErrorHandler(service_name="odds")

    try:
        fetch_odds(url)
    except OddsFetchError as e:
        handler.handle(e, context={"url": url})
"""

from shared.errors.exceptions import (
    # Base
    BettingError,
    # Service-specific
    OddsError,
    OddsFetchError,
    OddsParseError,
    PredictionError,
    PredictionAPIError,
    PredictionDataError,
    ResultsError,
    ResultsFetchError,
    ResultsParseError,
    AnalysisError,
    AnalysisDataError,
    # Scraping
    ScrapingError,
    ScrapingTimeoutError,
    ScrapingRateLimitError,
    TableExtractionError,
    # Configuration
    ConfigError,
    ConfigNotFoundError,
    ConfigValidationError,
    # Data
    DataError,
    DataNotFoundError,
    DataValidationError,
    DataIOError,
)
from shared.errors.handler import ErrorHandler, create_error_handler

__all__ = [
    # Base
    "BettingError",
    # Service-specific
    "OddsError",
    "OddsFetchError",
    "OddsParseError",
    "PredictionError",
    "PredictionAPIError",
    "PredictionDataError",
    "ResultsError",
    "ResultsFetchError",
    "ResultsParseError",
    "AnalysisError",
    "AnalysisDataError",
    # Scraping
    "ScrapingError",
    "ScrapingTimeoutError",
    "ScrapingRateLimitError",
    "TableExtractionError",
    # Configuration
    "ConfigError",
    "ConfigNotFoundError",
    "ConfigValidationError",
    # Data
    "DataError",
    "DataNotFoundError",
    "DataValidationError",
    "DataIOError",
    # Handler
    "ErrorHandler",
    "create_error_handler",
]
