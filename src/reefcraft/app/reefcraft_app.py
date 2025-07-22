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
from reefcraft.ui.window import Window
from reefcraft.utils.logger import configure_logging, logger


class ReefcraftApp:
    """Main application framework for Reefcraft."""

    def __init__(self, app_root: Path | None = None) -> None:
        """Initialize the application state."""
        self.app_root = Path(app_root) if app_root else Path(__file__).resolve().parents[1]
        configure_logging(self.app_root)
        self.engine = Engine()
        self.window = Window(self.engine, self.app_root)

    def run(self) -> None:
        """Run the application and block until the window closes."""
        # =====================================================================
        # Start the Engine and loop. This hands event control off to pygfx.
        # Not necessarily ideal, but there are lots of sandtraps in terms of
        # processing events to do it manually.  For, now let pygfx do it.
        # The callback that allows this to occur is on the renderer created by
        # the Window class
        # =====================================================================
        self.window.register_app_step(self.step)
        self.engine.start()
        loop.run()

    def step(self) -> None:
        """Perform a complete step for the frame by calling update() on engine then draw() on views."""
        self.engine.update()
        self.window.draw(self.engine.state)
