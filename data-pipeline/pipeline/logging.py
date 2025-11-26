"""Centralized logging configuration for the pipeline.

Provides a consistent structlog configuration across all CLI entry points.
"""

import logging
import sys

import structlog


def configure_logging(level: int = logging.INFO) -> None:
    """Configure structured logging for the pipeline.

    Sets up both standard library logging and structlog with
    consistent formatting for CLI output.

    Args:
        level: Logging level (default: INFO).
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        level=level,
        stream=sys.stdout,
    )

    # Configure structlog with console rendering
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
