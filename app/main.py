# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Entrypoint for the Reefcraft GUI application."""

from pathlib import Path

from .gui.main_window import launch_app

APP_ROOT = Path(__file__).resolve().parent  # → reefcraft/app

if __name__ == "__main__":
    launch_app(app_root=APP_ROOT)
