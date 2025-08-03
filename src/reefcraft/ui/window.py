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
from reefcraft.ui.reef import Reef
from reefcraft.ui.views.palette import Palette
from reefcraft.utils.logger import logger
from reefcraft.utils.window_style import apply_dark_titlebar_and_icon


class Window:
    """The window is both an OS level window as well as a render canvas and renderer."""

    def __init__(self, engine: Engine, app_root: Path) -> None:
        """Initialize the window and view state."""
        self.engine = engine
        self.canvas = RenderCanvas(size=(1920, 1080), title="Reefcraft", update_mode="continuous", max_fps=60)  # type: ignore

        # Make the window beautiful with dark mode titel bar and an icon
        icon_path = (app_root / "resources" / "icons" / "logo.ico").resolve()
        apply_dark_titlebar_and_icon("Reefcraft", icon_path)

        # Prepare our pygfx renderer
        self.renderer = gfx.WgpuRenderer(self.canvas)
        self.stats = gfx.Stats(viewport=self.renderer)

        # Create the view of the reef and the ui panel
        self.reef = Reef(self.renderer)
        self.panel = Palette(self.renderer, self.engine)

        self.renderer.request_draw(self.draw)

    @property
    def is_open(self) -> bool:
        """Flag indicating the window is still open."""
        return not self.canvas.get_closed()

    def draw(self) -> None:
        """Render one frame of the simulation and overlay UI."""
        # with self.stats:
        self.reef.draw(self.engine.state)
        self.panel.draw(self.engine.state)
        # self.stats.render()
        self.renderer.flush()
