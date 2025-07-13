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
        self.canvas = RenderCanvas(size=(1920, 1080), title="Reefcraft", update_mode="continuous", max_fps=60)
        icon_path = (app_root / "resources" / "icon" / "reefcraft.ico").resolve()
        apply_dark_titlebar_and_icon("Reefcraft", icon_path)
