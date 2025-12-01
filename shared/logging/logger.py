"""Per-service logging infrastructure.

Provides a LoggerFactory that creates loggers writing to service-specific files.
Each service gets its own log file in the logs/ directory.
"""

import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Dict


class LoggerFactory:
    """Factory for creating service-specific loggers.

    Each logger writes to its own file in the logs/ directory.
    Loggers are cached to ensure only one logger per service.

    Example:
        logger = LoggerFactory.get_logger("odds")
        logger.info("Fetching odds from DraftKings")
        logger.error("Failed to parse odds", exc_info=True)
    """

    _loggers: Dict[str, logging.Logger] = {}
    _logs_dir: Path = Path("logs")
    _log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    _date_format: str = "%Y-%m-%d %H:%M:%S"
    _max_bytes: int = 10 * 1024 * 1024  # 10 MB
    _backup_count: int = 5
    _log_level: int = logging.INFO

    @classmethod
    def configure(
        cls,
        logs_dir: Path | str | None = None,
        log_format: str | None = None,
        date_format: str | None = None,
        max_bytes: int | None = None,
        backup_count: int | None = None,
        log_level: int | None = None,
    ) -> None:
        """Configure the logger factory settings.

        Should be called once at application startup.

        Args:
            logs_dir: Directory for log files
            log_format: Log message format
            date_format: Date format for log messages
            max_bytes: Max size of each log file before rotation
            backup_count: Number of backup files to keep
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        if logs_dir is not None:
            cls._logs_dir = Path(logs_dir)
        if log_format is not None:
            cls._log_format = log_format
        if date_format is not None:
            cls._date_format = date_format
        if max_bytes is not None:
            cls._max_bytes = max_bytes
        if backup_count is not None:
            cls._backup_count = backup_count
        if log_level is not None:
            cls._log_level = log_level

    @classmethod
    def get_logger(cls, service_name: str) -> logging.Logger:
        """Get or create a logger for the specified service.

        Args:
            service_name: Name of the service (e.g., "odds", "prediction")

        Returns:
            Logger configured to write to logs/{service_name}.log
        """
        if service_name in cls._loggers:
            return cls._loggers[service_name]

        # Ensure logs directory exists
        cls._logs_dir.mkdir(parents=True, exist_ok=True)

        # Create logger
        logger = logging.getLogger(f"betting.{service_name}")
        logger.setLevel(cls._log_level)

        # Avoid duplicate handlers if logger already exists
        if not logger.handlers:
            # Create file handler with rotation
            log_file = cls._logs_dir / f"{service_name}.log"
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=cls._max_bytes,
                backupCount=cls._backup_count,
            )
            file_handler.setLevel(cls._log_level)

            # Create console handler for errors
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.ERROR)

            # Create formatter
            formatter = logging.Formatter(cls._log_format, cls._date_format)
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            # Add handlers
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

        cls._loggers[service_name] = logger
        return logger

    @classmethod
    def reset(cls) -> None:
        """Reset all loggers. Useful for testing."""
        for logger in cls._loggers.values():
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
        cls._loggers.clear()


# Convenience function for quick logger access
def get_logger(service_name: str) -> logging.Logger:
    """Get a logger for the specified service.

    Convenience wrapper around LoggerFactory.get_logger().

    Args:
        service_name: Name of the service

    Returns:
        Configured logger instance
    """
    return LoggerFactory.get_logger(service_name)
