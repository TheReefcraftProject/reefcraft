"""Primary window for DearPyGUI representing the canvas for the 3D View."""

import dearpygui.dearpygui as dpg


class Canvas:
    """Fixed side panel that holds collapsible sections."""

    def __init__(self, canvas_size: tuple[int, int] = (1024, 768)) -> None:
        """Initialize the panel with width, margin, and pinned side."""
        self.window_id = dpg.add_window(
            label="Canvas",
            no_title_bar=True,
            no_move=True,
            no_resize=True,
            no_scrollbar=True,
        )
        dpg.set_primary_window(self.window_id, True)

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

        dpg.add_image(self.canvas_texture, parent=self.window_id, tag="offscreen_tex")

    def _checkerboard_pattern(self, width: int, height: int, square: int = 16) -> list[float]:
        """Return RGBA data for a checkerboard texture."""
        data: list[float] = []
        for y in range(height):
            for x in range(width):
                val = 24 if ((x // square + y // square) % 2 == 0) else 16
                f = val / 255.0
                data.extend([f, f, f, 1.0])
        return data

    def draw(self) -> None:
        """Render the background canvas and 3d scene."""
        window_width, window_height = dpg.get_item_rect_size(self.window_id)
        x = int((window_width - self.canvas_width) / 2)
        y = int((window_height - self.canvas_height) / 2)
        dpg.configure_item("offscreen_tex", pos=(x, y))
