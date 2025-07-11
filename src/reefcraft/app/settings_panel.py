"""Defines the settings panel layout using pyimgui widgets."""

from __future__ import annotations

import imgui

from typing import TYPE_CHECKING

from ..gui.panel import Panel, Section

if TYPE_CHECKING:  # pragma: no cover - only for type hints
    from ..sim.engine import Engine
from ..utils.settings import load_settings


class SettingsPanel:
    """Encapsulate the pyimgui overlay panel."""

    def __init__(self, panel: Panel, engine: "Engine") -> None:
        """Initialize the settings panel."""
        self.panel = panel
        self.engine = engine
        self.settings = load_settings()
        self.growth_rate = 1.0
        self.complexity = 0.5
        self.temperature = 24.0
        self.light = 0.8
        self._register_demo_sections()

    def _register_demo_sections(self) -> None:
        def coral_growth() -> None:
            changed, self.growth_rate = imgui.slider_float("Growth Rate", self.growth_rate, 0.0, 2.0)
            changed, self.complexity = imgui.slider_float("Complexity", self.complexity, 0.0, 1.0)
            if imgui.button("Apply", width=300):
                print("[DEBUG] Apply coral growth")

        def environment() -> None:
            changed, self.temperature = imgui.slider_float("Water Temp", self.temperature, 10.0, 30.0)
            changed, self.light = imgui.slider_float("Light", self.light, 0.0, 1.0)
            if imgui.button("Reset Environment", width=300):
                print("[DEBUG] Reset environment")

        self.panel.register(Section("Coral Growth", coral_growth))
        self.panel.register(Section("Environment", environment))
