"""Error handler that writes errors to errors.json and stops execution.

When an error occurs, all details are written to errors.json in the project root.
The file is overwritten each time a new error occurs.
"""

import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, NoReturn

from shared.errors.exceptions import BettingError
from shared.logging.logger import get_logger


class ErrorHandler:
    """Handles errors by logging and writing to errors.json.

    When handle() is called, it:
    1. Logs the error to the service's log file
    2. Writes full error details to errors.json
    3. Re-raises the exception to stop execution

    Example:
        handler = ErrorHandler(service_name="odds")

        try:
            fetch_odds(url)
        except Exception as e:
            handler.handle(e, context={"url": url})
    """

    def __init__(
        self,
        service_name: str,
        error_file: Path | str = "errors.json",
        include_traceback: bool = True,
    ):
        """Initialize the error handler.

        Args:
            service_name: Name of the service (for logging)
            error_file: Path to the error output file
            include_traceback: Whether to include full traceback in output
        """
        self.service_name = service_name
        self.error_file = Path(error_file)
        self.include_traceback = include_traceback
        self.logger = get_logger(service_name)

    def handle(self, error: Exception, context: dict[str, Any] | None = None) -> NoReturn:
        """Handle an error by logging, writing to file, and re-raising.

        Args:
            error: The exception that occurred
            context: Additional context about the error

        Raises:
            The original exception after logging and writing to file
        """
        # Merge context from BettingError if applicable
        full_context = {}
        if isinstance(error, BettingError) and error.context:
            full_context.update(error.context)
        if context:
            full_context.update(context)

        # Build error data
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "service": self.service_name,
            "error_type": type(error).__name__,
            "error_class": f"{type(error).__module__}.{type(error).__name__}",
            "message": str(error),
            "context": full_context,
        }

        if self.include_traceback:
            error_data["traceback"] = traceback.format_exc()

        # Log the error
        self.logger.error(
            f"{error_data['error_type']}: {error_data['message']}",
            exc_info=True,
        )

        # Write to errors.json (overwrites previous errors)
        self._write_error_file(error_data)

        # Re-raise to stop execution
        raise error

    def _write_error_file(self, error_data: dict[str, Any]) -> None:
        """Write error data to the error file.

        Args:
            error_data: Dictionary containing error details
        """
        try:
            self.error_file.write_text(
                json.dumps(error_data, indent=2, ensure_ascii=False)
            )
        except Exception as write_error:
            # If we can't write the error file, at least log it
            self.logger.error(f"Failed to write error file: {write_error}")

    def wrap(self, context: dict[str, Any] | None = None):
        """Context manager for automatic error handling.

        Example:
            handler = ErrorHandler(service_name="odds")

            with handler.wrap(context={"operation": "fetch"}):
                fetch_odds(url)
        """
        return _ErrorContext(self, context)


class _ErrorContext:
    """Context manager for ErrorHandler.wrap()."""

    def __init__(self, handler: ErrorHandler, context: dict[str, Any] | None):
        self.handler = handler
        self.context = context

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None:
            self.handler.handle(exc_val, context=self.context)
        return False


def create_error_handler(service_name: str) -> ErrorHandler:
    """Create an ErrorHandler for a service.

    Convenience function that uses default settings.

    Args:
        service_name: Name of the service

    Returns:
        Configured ErrorHandler instance
    """
    return ErrorHandler(
        service_name=service_name,
        error_file="errors.json",
        include_traceback=True,
    )
