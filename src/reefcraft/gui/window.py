# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Defines the main GUI layout using Taichi's GGUI."""

from __future__ import annotations

from typing import TYPE_CHECKING

import taichi as ti

from .panel import Panel, Section

if TYPE_CHECKING:
    from pathlib import Path

    from ..sim.engine import Engine


class Window:
    """Encapsulate the Taichi window and overlay UI panel."""

    def __init__(self, engine: Engine, app_root: Path) -> None:
        """Initialize the window and GUI state."""
        self.engine = engine

        ti.init(arch=ti.vulkan)
        self.window = ti.ui.Window("Reefcraft", res=(1280, 1080), vsync=True)
        self.canvas = self.window.get_canvas()
        self.gui = self.window.get_gui()

        from ..utils.window_style import apply_dark_titlebar_and_icon

        icon_path = (app_root / "resources" / "icon" / "reefcraft.ico").resolve()
        apply_dark_titlebar_and_icon("Reefcraft", icon_path)

        self.panel = Panel(width=300, margin=10)
        self._register_demo_sections()

    def _register_demo_sections(self) -> None:
        """Register example sections for demonstration."""

        def coral_growth(gui: ti.ui.Gui) -> None:
            self.growth_rate = getattr(self, "growth_rate", 1.0)
            self.growth_rate = gui.slider_float("Growth Rate", self.growth_rate, 0.0, 2.0)
            self.complexity = getattr(self, "complexity", 0.5)
            self.complexity = gui.slider_float("Complexity", self.complexity, 0.0, 1.0)
            if gui.button("Apply"):
                print("[DEBUG] Apply coral growth")

        def environment(gui: ti.ui.Gui) -> None:
            self.temperature = getattr(self, "temperature", 24.0)
            self.temperature = gui.slider_float("Water Temp", self.temperature, 10.0, 30.0)
            self.light = getattr(self, "light", 0.8)
            self.light = gui.slider_float("Light", self.light, 0.0, 1.0)
            if gui.button("Reset Environment"):
                print("[DEBUG] Reset environment")

        self.panel.register(Section("Coral Growth", coral_growth))
        self.panel.register(Section("Environment", environment))

    @property
    def running(self) -> bool:
        """Return ``True`` if the underlying Taichi window is still open."""
        return self.window.running

    def update(self) -> None:
        """Render one frame of the simulation and overlay UI."""
        self.canvas.clear((0.0, 0.0, 0.0))
        # Simulation visualization would be drawn to the canvas here
        self.panel.draw(self.window, self.gui)
        self.window.show()
