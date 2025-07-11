"""Primary window for DearPyGUI representing the canvas for the 3D View."""

from __future__ import annotations

from typing import TYPE_CHECKING

import dearpygui.dearpygui as dpg

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from render.context import RenderContext
    from render.scene import TriangleScene


class Canvas:
    """Offscreen image management and display."""

    def __init__(self, context: RenderContext, scene: TriangleScene, canvas_size: tuple[int, int] = (1024, 768)) -> None:
        """Initialize the canvas for the 3d scene in the viewport."""
        self.context = context
        self.scene = scene
        self.canvas_width, self.canvas_height = canvas_size
        self.context.resize(self.canvas_width, self.canvas_height)
        self.context.set_scene(self.scene)

        initial_data = self.context.render().ravel().tolist()

        self.canvas_texture = dpg.generate_uuid()
        with dpg.texture_registry(show=False):
            dpg.add_dynamic_texture(
                self.canvas_width,
                self.canvas_height,
                initial_data,
                tag=self.canvas_texture,
            )
        self.canvas_drawlist = dpg.add_viewport_drawlist(front=False)
        self.canvas_image = dpg.draw_image(
            self.canvas_texture,
            (0, 0),
            (self.canvas_width, self.canvas_height),
            parent=self.canvas_drawlist,
        )

    def draw(self) -> None:
        """Render the background canvas and 3d scene."""
        image = self.context.render().ravel().tolist()
        dpg.set_value(self.canvas_texture, image)

        x = (dpg.get_viewport_width() - self.canvas_width) / 2
        y = (dpg.get_viewport_height() - self.canvas_height) / 2
        dpg.configure_item(
            self.canvas_image,
            pmin=(x, y),
            pmax=(x + self.canvas_width, y + self.canvas_height),
        )
