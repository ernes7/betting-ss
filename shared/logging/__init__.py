"""Per-service logging infrastructure.

Each service gets its own log file in the logs/ directory.

Example:
    from shared.logging import get_logger

    logger = get_logger("odds")
    logger.info("Starting odds fetch")
    logger.error("Failed to parse", exc_info=True)
"""

from shared.logging.logger import LoggerFactory, get_logger

__all__ = ["LoggerFactory", "get_logger"]
