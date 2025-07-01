# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Entrypoint for the Reefcraft GUI application."""

from __future__ import annotations

from pathlib import Path

from gui.main_window import launch_app


def main() -> None:
    """Launch the GUI and block until closed."""
    launch_app(app_root=Path(__file__).resolve().parent)


if __name__ == "__main__":
    main()
