# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Primary window for the application and views."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rendercanvas.auto import RenderCanvas

from reefcraft.ui.reef import Reef
from reefcraft.ui.ui_context import UIContext
from reefcraft.ui.views.panel import Panel
from reefcraft.utils.window_style import apply_dark_titlebar_and_icon

if TYPE_CHECKING:
    from pathlib import Path

    from reefcraft.sim.engine import Engine


class Window:
    """The window is both an OS level window as well as a render canvas and renderer."""

    def __init__(self, engine: Engine, app_root: Path) -> None:
        """Initialize the window and view state."""
        self.engine = engine
        self.canvas = RenderCanvas(size=(1920, 1080), title="Reefcraft", update_mode="continuous", max_fps=60)  # type: ignore

        # Make the window beautiful with dark mode title bar and an icon
        icon_path = (app_root / "resources" / "icons" / "logo.ico").resolve()
        apply_dark_titlebar_and_icon("Reefcraft", icon_path)

        # Create the global UI context with renderer state
        self.context = UIContext(canvas=self.canvas)

        # Create the view of the reef and the UI panel
        self.reef = Reef(self.context.renderer)
        self.panel = Panel(self.context, engine=self.engine)

        self.context.renderer.request_draw(self.draw)

    @property
    def is_open(self) -> bool:
        """Flag indicating the window is still open."""
        return not self.canvas.get_closed()

    def draw(self) -> None:
        """Render one frame of the simulation and overlay UI."""
        self.reef.draw(self.engine.state)
        self.panel.draw(self.engine.state)
        self.context.renderer.flush()
