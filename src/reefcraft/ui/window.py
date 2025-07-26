# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Primary window for the application and views."""

from collections.abc import Callable
from pathlib import Path

import pygfx as gfx
from rendercanvas.auto import RenderCanvas

from reefcraft.sim.engine import Engine
from reefcraft.sim.state import SimState
from reefcraft.ui.button import Button
from reefcraft.ui.layout import Layout
from reefcraft.ui.panel import Panel
from reefcraft.ui.reef import Reef
from reefcraft.ui.slider import Slider
from reefcraft.utils.logger import logger
from reefcraft.utils.window_style import apply_dark_titlebar_and_icon


class Window:
    """The window is both an OS level window as well as a render canvas and renderer."""

    def __init__(self, engine: Engine, app_root: Path) -> None:
        """Initialize the window and view state."""
        self.engine = engine
        self.canvas = RenderCanvas(size=(1920, 1080), title="Reefcraft", update_mode="continuous", max_fps=60)  # type: ignore

        # Make the window beautiful with dark mode titel bar and an icon
        icon_path = (app_root / "resources" / "icon" / "reefcraft.ico").resolve()
        apply_dark_titlebar_and_icon("Reefcraft", icon_path)

        # Prepare our pygfx renderer
        self.renderer = gfx.WgpuRenderer(self.canvas)
        self.stats = gfx.Stats(viewport=self.renderer)

        # Create the view of the reef and the ui panel
        self.reef = Reef(self.renderer)
        self.panel = Panel(self.renderer)

        _ = Layout(
            [
                Slider(self.panel, width=250, on_change=lambda val: logger.debug(f"Slider1 Value: {val}")),
                Slider(self.panel, width=250, on_change=lambda val: logger.debug(f"Slider1 Value: {val}")),
                Slider(self.panel, width=250, on_change=lambda val: logger.debug(f"Slider1 Value: {val}")),
                Button(self.panel, width=250, height=20, label="Mom", on_click=lambda: logger.debug("MOM Button Clicked!")),
                Button(self.panel, width=250, height=20, label="Grow", on_click=lambda: logger.debug("Let's grow some coral!")),
            ],
        )

    @property
    def is_open(self) -> bool:
        """Flag indicating the window is still open."""
        return not self.canvas.get_closed()

    def register_app_step(self, step: Callable) -> None:
        """Async schedule the update and draw cycles as a single 'step'."""
        self.renderer.request_draw(step)

    def draw(self, state: SimState) -> None:
        """Render one frame of the simulation and overlay UI."""
        with self.stats:
            self.reef.draw(state)
            self.panel.draw(state)
        self.stats.render()
        self.renderer.flush()
