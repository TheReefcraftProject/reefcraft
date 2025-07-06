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

    def __init__(self, engine: Engine, app_root: Path) -> None:
        """Initialize the window and GUI state."""
        self.engine = engine

        dpg.create_context()
        dpg.create_viewport(title="Reefcraft", width=1280, height=1080)
        dpg.setup_dearpygui()

        from ..utils.window_style import apply_dark_titlebar_and_icon

        icon_path = (app_root / "resources" / "icon" / "reefcraft.ico").resolve()
        apply_dark_titlebar_and_icon("Reefcraft", icon_path)

        self.panel = Panel(width=300, margin=10)

        self.canvas_window = dpg.add_window(
            label="",
            no_title_bar=True,
            no_move=True,
            no_resize=True,
        )
        self.canvas_texture = dpg.generate_uuid()
        dpg.add_dynamic_texture(1, 1, [255, 255, 255, 255], tag=self.canvas_texture)
        self.canvas_image = dpg.add_image(self.canvas_texture, parent=self.canvas_window)

        # Default values for demo section widgets
        self.growth_rate = 1.0
        self.complexity = 0.5
        self.temperature = 24.0
        self.light = 0.8

        self._register_demo_sections()

        dpg.show_viewport()

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

        canvas_w = win_w - self.panel.width - 3 * self.panel.margin
        canvas_h = win_h - 2 * self.panel.margin

        dpg.configure_item(
            self.canvas_window,
            pos=(self.panel.margin, self.panel.margin),
            width=canvas_w,
            height=canvas_h,
        )
        dpg.configure_item(self.canvas_image, width=canvas_w, height=canvas_h)

        self.panel.draw()
        dpg.render_dearpygui_frame()
