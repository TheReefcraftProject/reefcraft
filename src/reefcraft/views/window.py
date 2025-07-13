# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Primary window for the application and views."""

from pathlib import Path

import pygfx as gfx
from rendercanvas.auto import RenderCanvas

from reefcraft.sim.engine import Engine
from reefcraft.utils.window_style import apply_dark_titlebar_and_icon
from reefcraft.views.reef import Reef
from reefcraft.views.ui import Panel


class Window:
    """The window is both an OS level window as well as a render canvas and renderer."""

    def __init__(self, engine: Engine, app_root: Path) -> None:
        """Initialize the window and GUI state."""
        self.canvas = RenderCanvas(size=(1920, 1080), title="Reefcraft", update_mode="continuous", max_fps=60)
        icon_path = (app_root / "resources" / "icon" / "reefcraft.ico").resolve()
        apply_dark_titlebar_and_icon("Reefcraft", icon_path)

        self.renderer = gfx.WgpuRenderer(self.canvas)
        self.renderer.request_draw(self.update)

        self.stats = gfx.Stats(viewport=self.renderer)

        self.reef = Reef(self.renderer)
        self.panel = Panel(self.renderer)

    def update(self) -> None:
        """Render one frame of the simulation and overlay UI."""
        with self.stats:
            self.reef.draw()
            self.panel.draw()
        self.stats.render()
