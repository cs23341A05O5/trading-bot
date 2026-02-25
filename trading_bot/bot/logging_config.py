"""Logging configuration for the trading bot.

Provides professional logging setup with file rotation and formatting.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


def setup_logging(
    log_dir: str = "logs",
    log_file: str = "trading_bot.log",
    max_bytes: int = 5 * 1024 * 1024,  # 5 MB
    backup_count: int = 5,
    log_level: int = logging.INFO,
) -> logging.Logger:
    """Set up professional logging with rotation.

    Args:
        log_dir: Directory to store log files.
        log_file: Name of the log file.
        max_bytes: Maximum size of each log file before rotation.
        backup_count: Number of backup files to keep.
        log_level: Logging level (default: INFO).

    Returns:
        Configured logger instance.
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger("trading_bot")
    logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Define log format
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(module)s:%(funcName)s:%(lineno)d | %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(log_format, datefmt=date_format)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_path / log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler for errors
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Optional name for the logger. If None, returns the root trading_bot logger.

    Returns:
        Logger instance.
    """
    if name:
        return logging.getLogger(f"trading_bot.{name}")
    return logging.getLogger("trading_bot")
