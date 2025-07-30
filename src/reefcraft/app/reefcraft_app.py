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
from reefcraft.utils.paths import get_app_root, set_app_root


class ReefcraftApp:
    """Main application framework for Reefcraft."""

    def __init__(self, app_root: Path | None = None) -> None:
        """Prepare the application (without starting engine)."""
        set_app_root(Path(app_root) if app_root else Path(__file__).resolve().parents[1])
        configure_logging(get_app_root())

        self.window: Window | None = None

    def run(self) -> None:
        """Start the app, engine, and main loop."""
        with Engine(dt=0.01) as engine:
            self.window = Window(engine, get_app_root())
            # NOTE: Engine is paused by default; play button will control it.  Engine is on its own thread
            # NOTE: Window is registed for real-time draw callbacks and will recieve the draw callback regularly via loop()
            loop.run()
