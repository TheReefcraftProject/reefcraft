"""Standalone pygfx window for displaying the 3D scene."""

from __future__ import annotations

from typing import TYPE_CHECKING

import glfw
from wgpu.gui.glfw import update_glfw_canvasses

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from reefcraft.render.context import RenderContext
    from reefcraft.render.scene import Scene


class Canvas:
    """Manage a dedicated pygfx rendering window."""

    def __init__(self, context: RenderContext, scene: Scene, canvas_size: tuple[int, int] = (1024, 768)) -> None:
        """Initialize the canvas and connect it to the :class:`RenderContext`."""
        self.context = context
        self.scene = scene
        self.canvas_width, self.canvas_height = canvas_size
        self.context.resize(self.canvas_width, self.canvas_height)
        self.context.set_scene(self.scene)

        # hook the draw callback for continuous animation
        self.context.canvas.request_draw(self._draw_frame)

    def _draw_frame(self) -> None:
        """Render one frame and schedule the next draw."""
        self.context.render()
        self.context.canvas.request_draw()

    def draw(self) -> None:
        """Poll window events and display the latest frame."""
        glfw.poll_events()
        update_glfw_canvasses()

    @property
    def closed(self) -> bool:
        """Return ``True`` if the pygfx window has been closed."""
        return self.context.canvas.is_closed()
