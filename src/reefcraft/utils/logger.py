# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Unified logging configuration for Reefcraft with timestamped files and banners.

This module provides a centralized logging configuration system for the
Reefcraft application using the Loguru library. It sets up both console
and file logging with consistent formatting, automatic log rotation,
and startup/shutdown banners for clear session tracking.

The logging system provides:
- Console output with color coding and detailed formatting
- Timestamped log files for each application run
- Automatic log file retention and cleanup
- Startup and shutdown banners for session tracking
- Backtrace and diagnostic information for debugging
- Consistent formatting across all log outputs

The logger automatically creates a logs directory and generates
timestamped log files for each application session, making it
easy to track and debug issues across multiple runs.
"""

import atexit
import sys
from datetime import datetime
from pathlib import Path

from loguru import logger


def configure_logging(app_root: Path | None = None) -> None:
    """Configure the Loguru logging system with console and file handlers.

    Sets up a comprehensive logging configuration with both console
    and file output, including colorized console logging, timestamped
    file logging, and automatic startup/shutdown banners. The system
    is designed for both development and production use.

    Key features:
    - Removes default Loguru handlers for custom configuration
    - Console logging with color coding and rich formatting
    - Timestamped log files with automatic retention
    - Startup and shutdown session banners
    - Comprehensive backtrace and diagnostic information
    - Automatic log directory creation

    Args:
        app_root: Root directory of the application for log file placement.
                 If None, uses the current working directory.

    File Organization:
        - Log files are stored in `{app_root}/logs/` directory
        - Each run creates a new timestamped log file
        - Format: `reefcraft_YYYYMMDD_HHMMSS.log`
        - Automatic cleanup after 7 days retention

    Example:
        >>> from reefcraft.utils.logger import configure_logging, logger
        >>> configure_logging(Path("/path/to/app"))
        >>> logger.info("Application started successfully")
        >>> logger.error("An error occurred", extra={"context": "details"})
    """
    # Remove default Loguru handlers to ensure clean configuration
    logger.remove()

    # Configure console output with rich formatting and colors
    _setup_console_logging()

    # Configure file logging with timestamped files
    _setup_file_logging(app_root)

    # Display startup banner and register shutdown banner
    _setup_session_banners()


def _setup_console_logging() -> None:
    """Configure console logging with color coding and rich formatting.

    Sets up stdout logging with:
    - Color coding for different log levels
    - Detailed timestamp formatting
    - File path and line number information
    - Backtrace and diagnostic information for errors
    """
    logger.add(
        sys.stdout,
        colorize=True,
        backtrace=True,
        diagnose=True,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {file.path}:{line} - {message}",
    )


def _setup_file_logging(app_root: Path | None) -> None:
    """Configure file logging with timestamped files and retention.

    Creates timestamped log files for each application run with:
    - Automatic log directory creation
    - Unique timestamped filename for each session
    - 7-day automatic retention policy
    - Detailed formatting for debugging

    Args:
        app_root: Root directory for log file placement
    """
    # Determine base directory and ensure logs directory exists
    base_dir = Path(app_root or Path.cwd())
    log_dir = base_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Generate timestamped filename for this session
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"reefcraft_{timestamp}.log"

    # Configure file sink with retention and detailed formatting
    logger.add(
        str(log_file),
        retention="7 days",  # Automatic cleanup after 7 days
        backtrace=True,
        diagnose=True,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {file.path}:{line} - {message}",
    )


def _setup_session_banners() -> None:
    """Configure startup and shutdown banners for session tracking.

    Displays clear session boundaries with:
    - Startup banner with timestamp
    - Automatic shutdown banner via atexit
    - Consistent formatting for easy log parsing
    """
    # Create session banner
    banner = "=" * 80
    start_time = datetime.now().isoformat(sep=" ", timespec="seconds")

    # Display startup banner
    logger.info(banner)
    logger.info(f"Starting Reefcraft at {start_time}")
    logger.info(banner)

    # Register shutdown banner to display on application exit
    def _shutdown_banner() -> None:
        """Display shutdown banner with timestamp.

        Called automatically when the application exits via atexit.
        Provides clear session termination logging.
        """
        end_time = datetime.now().isoformat(sep=" ", timespec="seconds")
        logger.info(banner)
        logger.info(f"Shutting down Reefcraft at {end_time}")
        logger.info(banner)

    # Register the shutdown banner to run on application exit
    atexit.register(_shutdown_banner)
