# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Unified location to manage all the applciation paths for resources, etc."""

from pathlib import Path

_APP_ROOT: Path | None = None


def set_app_root(path: Path) -> None:
    """Set the root directory of the application explicitly (once)."""
    global _APP_ROOT
    _APP_ROOT = path.resolve()


def get_app_root() -> Path:
    """Return the application root path, or raise if not set."""
    if _APP_ROOT is None:
        raise RuntimeError("APP_ROOT not set. Call set_app_root() at app startup.")
    return _APP_ROOT


def icons_dir() -> Path:
    """Return path to the application's icons directory."""
    return get_app_root() / "resources" / "icons"


def fonts_dir() -> Path:
    """Return path to the application's fonts directory."""
    return get_app_root() / "resources" / "fonts"


def resources_dir() -> Path:
    """Return path to the application's root resources directory."""
    return get_app_root() / "resources"
