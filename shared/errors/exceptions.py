"""Custom exceptions for the betting application.

All exceptions inherit from BettingError for consistent handling.
Service-specific exceptions provide context about where errors occurred.
"""


class BettingError(Exception):
    """Base exception for all betting application errors."""

    def __init__(self, message: str, context: dict | None = None):
        """Initialize the exception.

        Args:
            message: Human-readable error message
            context: Additional context about the error
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}


# Service-specific exceptions

class OddsError(BettingError):
    """Errors related to the ODDS service."""
    pass


class OddsFetchError(OddsError):
    """Failed to fetch odds from source."""
    pass


class OddsParseError(OddsError):
    """Failed to parse odds data."""
    pass


class PredictionError(BettingError):
    """Errors related to the PREDICTION service."""
    pass


class PredictionAPIError(PredictionError):
    """Failed to get prediction from Claude API."""
    pass


class PredictionDataError(PredictionError):
    """Invalid or missing data for prediction."""
    pass


class ResultsError(BettingError):
    """Errors related to the RESULTS service."""
    pass


class ResultsFetchError(ResultsError):
    """Failed to fetch results from source."""
    pass


class ResultsParseError(ResultsError):
    """Failed to parse results data."""
    pass


class AnalysisError(BettingError):
    """Errors related to the ANALYSIS service."""
    pass


class AnalysisDataError(AnalysisError):
    """Missing or invalid data for analysis."""
    pass


# Scraping exceptions

class ScrapingError(BettingError):
    """Base exception for scraping operations."""
    pass


class ScrapingTimeoutError(ScrapingError):
    """Scraping operation timed out."""
    pass


class ScrapingRateLimitError(ScrapingError):
    """Rate limit exceeded during scraping."""
    pass


class TableExtractionError(ScrapingError):
    """Failed to extract table from page."""
    pass


# Configuration exceptions

class ConfigError(BettingError):
    """Errors related to configuration."""
    pass


class ConfigNotFoundError(ConfigError):
    """Configuration file not found."""
    pass


class ConfigValidationError(ConfigError):
    """Configuration validation failed."""
    pass


# Data exceptions

class DataError(BettingError):
    """Base exception for data operations."""
    pass


class DataNotFoundError(DataError):
    """Requested data not found."""
    pass


class DataValidationError(DataError):
    """Data validation failed."""
    pass


class DataIOError(DataError):
    """Error reading or writing data."""
    pass
