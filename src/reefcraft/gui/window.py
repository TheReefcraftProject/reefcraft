# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Defines the main GUI layout using Dear PyGui."""

from __future__ import annotations

from typing import TYPE_CHECKING

import dearpygui.dearpygui as dpg

from .panel import Panel, Section

if TYPE_CHECKING:
    from pathlib import Path

    from ..sim.engine import Engine


class Window:
    """Encapsulate the Dear PyGui viewport and overlay UI panel."""

    def __init__(
        self,
        engine: Engine,
        app_root: Path,
        *,
        canvas_size: tuple[int, int] = (1024, 768),
        border_color: tuple[int, int, int, int] = (32, 32, 32, 255),
        checkerboard_square: int = 16,
    ) -> None:
        """Initialize the window and GUI state."""
        self.engine = engine

        self.canvas_width, self.canvas_height = canvas_size
        self.checkerboard_square = checkerboard_square

        dpg.create_context()
        dpg.create_viewport(title="Reefcraft", width=1280, height=1080)

        self.panel = Panel(width=300, margin=10)

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
        dpg.set_viewport_clear_color(list(border_color))
        self.canvas_drawlist = dpg.add_viewport_drawlist(front=False)
        self.canvas_image = dpg.draw_image(
            self.canvas_texture,
            (0, 0),
            (self.canvas_width, self.canvas_height),
            parent=self.canvas_drawlist,
        )
        dpg.set_primary_window(self.panel.window_id, True)

        # Default values for demo section widgets
        self.growth_rate = 1.0
        self.complexity = 0.5
        self.temperature = 24.0
        self.light = 0.8

        self._register_demo_sections()

        dpg.setup_dearpygui()

        from ..utils.window_style import apply_dark_titlebar_and_icon

        icon_path = (app_root / "resources" / "icon" / "reefcraft.ico").resolve()
        apply_dark_titlebar_and_icon("Reefcraft", icon_path)

        dpg.show_viewport()

    def _checkerboard_pattern(
        self, width: int, height: int, square: int = 16
    ) -> list[float]:
        """Return RGBA data for a checkerboard texture."""
        data: list[float] = []
        for y in range(height):
            for x in range(width):
                val = 200 if ((x // square + y // square) % 2 == 0) else 255
                f = val / 255.0
                data.extend([f, f, f, 1.0])
        return data


    def _register_demo_sections(self) -> None:
        """Register example sections for demonstration."""

        def coral_growth() -> None:
            dpg.add_slider_float(
                label="Growth Rate",
                default_value=self.growth_rate,
                min_value=0.0,
                max_value=2.0,
                callback=lambda s, a: setattr(self, "growth_rate", a),
            )
            dpg.add_slider_float(
                label="Complexity",
                default_value=self.complexity,
                min_value=0.0,
                max_value=1.0,
                callback=lambda s, a: setattr(self, "complexity", a),
            )
            dpg.add_button(
                label="Apply",
                callback=lambda: print("[DEBUG] Apply coral growth"),
            )

        def environment() -> None:
            dpg.add_slider_float(
                label="Water Temp",
                default_value=self.temperature,
                min_value=10.0,
                max_value=30.0,
                callback=lambda s, a: setattr(self, "temperature", a),
            )
            dpg.add_slider_float(
                label="Light",
                default_value=self.light,
                min_value=0.0,
                max_value=1.0,
                callback=lambda s, a: setattr(self, "light", a),
            )
            dpg.add_button(
                label="Reset Environment",
                callback=lambda: print("[DEBUG] Reset environment"),
            )

        self.panel.register(Section("Coral Growth", coral_growth))
        self.panel.register(Section("Environment", environment))

    @property
    def running(self) -> bool:
        """Return ``True`` if the Dear PyGui viewport is still running."""
        return dpg.is_dearpygui_running()

    def update(self) -> None:
        """Render one frame of the simulation and overlay UI."""
        win_w, win_h = dpg.get_viewport_width(), dpg.get_viewport_height()

        x = (win_w - self.canvas_width) / 2
        y = (win_h - self.canvas_height) / 2
        dpg.configure_item(
            self.canvas_image,
            pmin=(x, y),
            pmax=(x + self.canvas_width, y + self.canvas_height),
        )

        self.panel.draw()
        dpg.render_dearpygui_frame()
