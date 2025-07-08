# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Entrypoint for the Reefcraft GUI application."""

from __future__ import annotations

from pathlib import Path

from .app import ReefcraftApp


def main() -> None:
    """Launch the application and block until closed."""
    app = ReefcraftApp(app_root=Path(__file__).resolve().parent)
    app.run()


if __name__ == "__main__":
    main()
