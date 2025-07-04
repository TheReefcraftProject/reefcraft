# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Defines the main GUI layout using Taichi."""

from __future__ import annotations

from typing import TYPE_CHECKING

import taichi as ti

if TYPE_CHECKING:
    from pathlib import Path

    from ..sim.engine import Engine


class Window:
    """Encapsulate the Taichi GUI window."""

    def __init__(self, engine: Engine, app_root: Path) -> None:
        """Initialize the window and related Taichi state."""
        self.engine = engine

        ti.init(arch=ti.gpu)
        self.window = ti.ui.Window("Reefcraft", res=(1280, 1080))
        self.gui = self.window.get_gui()

        from ..utils.window_style import apply_dark_titlebar_and_icon

        icon_path = (app_root / "resources" / "icon" / "reefcraft.ico").resolve()
        apply_dark_titlebar_and_icon("Reefcraft", icon_path)

    def run(self) -> None:
        """Enter the main event loop."""
        while self.window.running:
            self.engine.update()

            self.gui.text("Simulation Controls")
            if self.gui.button("Start"):
                self.engine.start()
            if self.gui.button("Pause"):
                self.engine.pause()
            if self.gui.button("Reset"):
                self.engine.reset()

            self.gui.text(f"Time: {self.engine.get_time():.3f}")
            self.window.show()
