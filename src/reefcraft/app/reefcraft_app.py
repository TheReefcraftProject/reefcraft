# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Application management for Reefcraft."""

from __future__ import annotations

from pathlib import Path

from rendercanvas.auto import loop

from reefcraft.sim.engine import Engine
from reefcraft.views.window import Window


class ReefcraftApp:
    """Main application framework for Reefcraft."""

    def __init__(self, app_root: Path | None = None) -> None:
        """Initialize the application state."""
        self.app_root = Path(app_root) if app_root else Path(__file__).resolve().parents[1]
        self.engine = Engine()
        self.window = Window(self.engine, self.app_root)

    def run(self) -> None:
        """Start the application."""
        loop.run()
