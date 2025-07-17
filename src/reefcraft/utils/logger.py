# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Unified logging configuration for Reefcraft, with per-run files and banners."""

import atexit
import sys
from datetime import datetime
from pathlib import Path

from loguru import logger


def configure_logging(app_root: Path | None = None) -> None:
    """Configure loguru with console and per-run file handlers + start/stop banners."""
    # Remove default handlers
    logger.remove()

    # Console (stdout) in color
    logger.add(
        sys.stdout,
        colorize=True,
        backtrace=True,
        diagnose=True,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {file.path}:{line} - {message}",
    )

    # Ensure logs/ directory exists
    base = Path(app_root or Path.cwd())
    log_dir = base / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Timestamped log file per run
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"reefcraft_{now}.log"

    # File sink (no in-run rotation, but old files cleaned up by retention)
    logger.add(
        log_file,
        retention="7 days",
        backtrace=True,
        diagnose=True,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {file.path}:{line} - {message}",
    )

    # Startup banner
    banner = "=" * 80
    start_time = datetime.now().isoformat(sep=" ", timespec="seconds")
    logger.info(banner)
    logger.info(f"Starting Reefcraft  at {start_time}")
    logger.info(banner)

    # Shutdown banner via atexit
    def _shutdown_banner() -> None:
        end_time = datetime.now().isoformat(sep=" ", timespec="seconds")
        logger.info(banner)
        logger.info(f"Shutting down Reefcraft  at {end_time}")
        logger.info(banner)

    atexit.register(_shutdown_banner)
