# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Defines the main GUI layout and application launch logic."""

from pathlib import Path

import dearpygui.dearpygui as dpg
from utils.settings import load_settings


def launch_app(app_root: Path) -> None:
    settings = load_settings()

    dpg.create_context()
    dpg.create_viewport(title="Reefcraft", width=1200, height=800)

    with dpg.font_registry():
        try:
            font_path = "resources/fonts/Archivo-Regular.ttf"
            default_font = dpg.add_font(font_path, 18)
            dpg.bind_font(default_font)
        except Exception as e:
            print(f"⚠️ Font not loaded: {e}")

    with dpg.window(label="Simulation Controls", tag="control_window", width=300, height=400):
        dpg.add_text("Simulation Settings")
        dpg.add_slider_float(label="Growth Rate", default_value=1.0, min_value=0.1, max_value=10.0)
        dpg.add_button(label="Start Simulation")
        dpg.add_button(label="Pause")
        dpg.add_button(label="Reset")

    # with dpg.window(label="Output / Log", tag="log_window", pos=(320, 0), width=860, height=400):
    # dpg.add_text("Status output...")
    # dpg.show_logger()

    dpg.setup_dearpygui()
    dpg.show_viewport()

    from platform.window_style import apply_dark_titlebar_and_icon

    icon_path = app_root / "resources" / "icon" / "reefcraft.ico"
    apply_dark_titlebar_and_icon("Reefcraft", icon_path)
    dpg.set_primary_window("control_window", True)
    dpg.start_dearpygui()
    dpg.destroy_context()
