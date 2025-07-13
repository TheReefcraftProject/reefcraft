# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Defines the main GUI layout using Dear PyGui."""

from pathlib import Path

from rendercanvas.auto import RenderCanvas

from ..sim.engine import Engine
from ..utils.window_style import apply_dark_titlebar_and_icon

# from .panel import Panel


class Window:
    """Encapsulate the Dear PyGui viewport and overlay UI panel."""

    def __init__(self, engine: Engine, app_root: Path) -> None:
        """Initialize the window and GUI state."""
        self.canvas = RenderCanvas(size=(1920, 1080), title="Reefcraft", update_mode="continuous", max_fps=120)
        icon_path = (app_root / "resources" / "icon" / "reefcraft.ico").resolve()
        apply_dark_titlebar_and_icon("Reefcraft", icon_path)

        # self._panel = Panel(width=300, margin=0)

    @property
    def is_closed(self) -> bool:
        """State of the canvas/window."""
        return self.canvas.get_closed()

    # @property
    # def panel(self) -> Panel:
    #    """Return the panel class for others to register sections."""
    #    return self._panel

    def update(self) -> None:
        """Render one frame of the simulation and overlay UI."""
        self.canvas.request_draw()
