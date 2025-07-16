# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Primary window for the application and views."""

from pathlib import Path

import glfw
import pygfx as gfx
from rendercanvas.auto import RenderCanvas

from reefcraft.sim.engine import Engine
from reefcraft.utils.window_style import apply_dark_titlebar_and_icon
from reefcraft.views.reef import Reef
from reefcraft.views.ui import Panel


class Window:
    """The window is both an OS level window as well as a render canvas and renderer."""

    def __init__(self, engine: Engine, app_root: Path) -> None:
        """Initialize the window and view state."""
        self.engine = engine
        self.canvas = RenderCanvas(size=(1920, 1080), title="Reefcraft")  # , update_mode="continuous", max_fps=60)

        # Make the window beautiful with dark mode titel bar and an icon
        icon_path = (app_root / "resources" / "icon" / "reefcraft.ico").resolve()
        apply_dark_titlebar_and_icon("Reefcraft", icon_path)

        # Prepare our pygfx renderer
        self.renderer = gfx.WgpuRenderer(self.canvas)
        # TODO: set up update(time) and draw() cycles separately
        # disp = gfx.Display(before_render=animate, stats=True)
        self.stats = gfx.Stats(viewport=self.renderer)

        # Create the view of the reef and the ui panel
        self.reef = Reef(self.renderer)
        self.panel = Panel(self.renderer)

        self.renderer.request_draw(self.draw())

    @property
    def is_open(self) -> bool:
        """Flag indicating the window is still open."""
        return not self.canvas.get_closed()

    def update(self, time: float) -> None:
        """Advance one frame of the simulation and overlay UI."""
        self.reef.update(time)
        self.panel.update(time)

    def draw(self) -> None:
        """Render one frame of the simulation and overlay UI."""
        print("DRAW")
        with self.stats:
            self.reef.draw()
            self.panel.draw()
        self.stats.render()
        self.renderer.flush()
