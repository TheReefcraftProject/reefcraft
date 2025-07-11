"""Main application window using pygfx and pyimgui."""

from __future__ import annotations

from pathlib import Path

import imgui
from wgpu.gui.auto import run

from .panel import Panel
from .imgui_utils.imgui_renderer import ImguiRenderer

from ..render.context import RenderContext
from ..render.scene import Scene
from ..sim.engine import Engine


class Window:
    """Encapsulate the pygfx window and overlay UI panel."""

    def __init__(self, engine: Engine, app_root: Path, context: RenderContext, scene: Scene) -> None:
        self.engine = engine
        self.context = context
        self.canvas = context.canvas
        self.renderer = context.renderer
        self.canvas.request_draw(self._draw)
        self.imgui = ImguiRenderer(self.renderer.device, self.canvas)
        self._panel = Panel(width=300, margin=0, side="left")
        self.imgui.set_gui(self._draw_gui)

    @property
    def running(self) -> bool:
        """Return ``True`` if the window is still open."""
        return not self.canvas.is_closed()

    @property
    def panel(self) -> Panel:
        return self._panel

    def _draw_gui(self):
        imgui.new_frame()
        win_w, win_h = self.canvas.get_logical_size()
        self.panel.draw(win_w, win_h)
        imgui.end_frame()
        imgui.render()
        return imgui.get_draw_data()

    def _draw(self):
        self.engine.update()
        self.context.render()
        self.imgui.render()

    def run(self) -> None:
        run()
