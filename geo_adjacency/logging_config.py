"""
Logging configuration for the geo-adjacency package.

This module provides centralized logging setup and configuration for all modules
in the geo_adjacency package.
"""

import logging
from typing import Optional


def setup_logger(
    name: str,
    level: int = logging.WARNING,
    console_format: Optional[str] = None,
    file_format: Optional[str] = None,
) -> logging.Logger:
    """
    Set up a logger with consistent formatting and handlers.

    Args:
        name (str): Name of the logger (typically __name__ from calling module)
        level (int): Logging level (default: logging.WARNING)
        console_format (Optional[str]): Custom format string for console output
        file_format (Optional[str]): Custom format string for file output

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)

    # Prevent adding duplicate handlers
    if logger.handlers:
        return logger

    # Set default formats if not provided
    if console_format is None:
        console_format = "%(name)s - %(levelname)s - %(message)s"

    if file_format is None:
        file_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # Create formatters
    console_formatter = logging.Formatter(console_format)
    console_handler.setFormatter(console_formatter)

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.setLevel(level)

    return logger
