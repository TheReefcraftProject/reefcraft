from __future__ import annotations

"""Unified logging configuration for Reefcraft."""
import sys
from pathlib import Path

from loguru import logger


def configure_logging(app_root: Path | None = None) -> None:
    """Configure loguru with console and file handlers."""
    logger.remove()
    logger.add(
        sys.stdout,
        colorize=True,
        backtrace=True,
        diagnose=True,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {file.path}:{line} - {message}",
    )
    log_path = Path(app_root or Path.cwd()) / "reefcraft.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger.add(
        log_path,
        rotation="10 MB",
        retention="7 days",
        backtrace=True,
        diagnose=True,
    )


# Configure logging at import so tests have logs
configure_logging()
