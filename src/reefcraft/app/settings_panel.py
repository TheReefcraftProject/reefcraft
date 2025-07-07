# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Defines the masettings panel layout."""

import dearpygui.dearpygui as dpg

from ..gui.panel import Panel, Section
from ..sim.engine import Engine
from ..utils.settings import load_settings


class SettingsPanel:
    """Encapsulate the Dear PyGui viewport and overlay UI panel."""

    def __init__(self, panel: Panel, engine: Engine) -> None:
        """Initialize the panel and state."""
        self.panel = panel
        self.engine = engine
        self.settings = load_settings()

        # Default values for demo section widgets
        self.growth_rate = 1.0
        self.complexity = 0.5
        self.temperature = 24.0
        self.light = 0.8

        self._register_demo_sections()

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
