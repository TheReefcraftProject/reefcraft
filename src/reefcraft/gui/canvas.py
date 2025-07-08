"""Primary window for DearPyGUI representing the canvas for the 3D View."""

import dearpygui.dearpygui as dpg


class Canvas:
    """Offscreen image management and display."""

    def __init__(self, canvas_size: tuple[int, int] = (1024, 768)) -> None:
        """Initialize the canvas for the 3d scene in the viewport."""
        self.canvas_width, self.canvas_height = canvas_size
        self.checkerboard_square = 16

        self.canvas_texture = dpg.generate_uuid()
        with dpg.texture_registry(show=False):
            dpg.add_dynamic_texture(
                self.canvas_width,
                self.canvas_height,
                self._checkerboard_pattern(
                    self.canvas_width,
                    self.canvas_height,
                    self.checkerboard_square,
                ),
                tag=self.canvas_texture,
            )
        self.canvas_drawlist = dpg.add_viewport_drawlist(front=False)
        self.canvas_image = dpg.draw_image(
            self.canvas_texture,
            (0, 0),
            (self.canvas_width, self.canvas_height),
            parent=self.canvas_drawlist,
        )

    def _checkerboard_pattern(self, width: int, height: int, square: int = 16) -> list[float]:
        """Return RGBA data for a checkerboard texture."""
        data: list[float] = []
        for y in range(height):
            for x in range(width):
                val = 32 if ((x // square + y // square) % 2 == 0) else 16
                f = val / 255.0
                data.extend([f, f, f * 1.05, 1.0])
        return data

    def draw(self) -> None:
        """Render the background canvas and 3d scene."""
        x = (dpg.get_viewport_width() - self.canvas_width) / 2
        y = (dpg.get_viewport_height() - self.canvas_height) / 2
        dpg.configure_item(
            self.canvas_image,
            pmin=(x, y),
            pmax=(x + self.canvas_width, y + self.canvas_height),
        )
