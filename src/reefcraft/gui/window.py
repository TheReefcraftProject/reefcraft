# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Defines the main GUI layout using Dear PyGui."""

from __future__ import annotations

from typing import TYPE_CHECKING

import dearpygui.dearpygui as dpg

from .canvas import Canvas
from .panel import Panel

if TYPE_CHECKING:
    from pathlib import Path

    from render.context import RenderContext
    from render.scene import TriangleScene

    from ..sim.engine import Engine


class Window:
    """Encapsulate the Dear PyGui viewport and overlay UI panel."""

    def __init__(self, engine: Engine, app_root: Path, context: RenderContext, scene: TriangleScene) -> None:
        """Initialize the window and GUI state."""
        viewport_color: tuple[int, int, int, int] = (20, 20, 22, 255)
        panel_side: str = "left"
        self.engine = engine

        dpg.create_context()
        dpg.create_viewport(title="Reefcraft", width=1920, height=1080)
        dpg.set_viewport_clear_color(list(viewport_color))

        self.canvas = Canvas(context, scene)
        self._panel = Panel(width=300, margin=0, side=panel_side)

        dpg.setup_dearpygui()

        from ..utils.window_style import apply_dark_titlebar_and_icon

        icon_path = (app_root / "resources" / "icon" / "reefcraft.ico").resolve()
        apply_dark_titlebar_and_icon("Reefcraft", icon_path)

        dpg.show_viewport()

        # Initialize the theme system.
        # TODO: Move this to its own class
        with dpg.theme() as reefcraft_theme, dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (100, 100, 200, 255), category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 0, category=dpg.mvThemeCat_Core)
        dpg.bind_theme(reefcraft_theme)
        with dpg.font_registry():
            try:
                font_path = (app_root / "resources" / "fonts" / "Archivo-Regular.ttf").resolve()
                default_font = dpg.add_font(str(font_path.resolve()), 13)
                dpg.bind_font(default_font)
            except Exception as e:
                print(f"⚠️ Font not loaded: {e}")
        # dpg.show_style_editor()

    @property
    def running(self) -> bool:
        """Return ``True`` if the Dear PyGui viewport is still running."""
        return dpg.is_dearpygui_running()

    @property
    def panel(self) -> Panel:
        """Return the panel class for others to register sections."""
        return self._panel

    def update(self) -> None:
        """Render one frame of the simulation and overlay UI."""
        self.canvas.draw()
        self.panel.draw()
        dpg.render_dearpygui_frame()
