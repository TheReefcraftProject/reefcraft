# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Defines the main GUI layout and application launch logic."""

from pathlib import Path

import dearpygui.dearpygui as dpg
from utils.settings import load_settings
from simulation import SimulationEngine


def launch_app(app_root: Path) -> None:
    settings = load_settings()
    engine = SimulationEngine()

    # def update_sim():
    #     engine.update()
    #     dpg.set_value("sim_output", f"Value: {engine.get_last_value(): .3f}")

    dpg.create_context()
    dpg.create_viewport(title="Reefcraft", width=1200, height=800)

    with dpg.font_registry():
        try:
            font_path = (app_root / "resources" / "fonts" / "Archivo-Regular.ttf").resolve()
            default_font = dpg.add_font(str(font_path.resolve()), 14)
            dpg.bind_font(default_font)
        except Exception as e:
            print(f"⚠️ Font not loaded: {e}")

    with dpg.window(label="Simulation Controls", tag="control_window", width=300, height=400):
        dpg.add_text("Simulation Settings")
        dpg.add_slider_float(label="Growth Rate", default_value=1.0, min_value=0.1, max_value=10.0)
        dpg.add_button(label="Start Simulation", callback=lambda: (print("[Start] clicked"), engine.start()))
        dpg.add_button(label="Pause", callback=lambda: engine.pause())
        dpg.add_button(label="Reset", callback=lambda: engine.reset())
        dpg.add_spacer(height=10)
        dpg.add_text("Value: 0.000", tag="sim_output")

    # with dpg.window(label="Output / Log", tag="log_window", pos=(320, 0), width=860, height=400):
    # dpg.add_text("Status output...")
    # dpg.show_logger()

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.render_dearpygui_frame()

    from platform.window_style import apply_dark_titlebar_and_icon

    icon_path = (app_root / "resources" / "icon" / "reefcraft.ico").resolve()
    apply_dark_titlebar_and_icon("Reefcraft", icon_path)
    dpg.set_primary_window("control_window", True)

    # TODO: Replace while-loop with DearPyGui callback loop if we ever need async or event-driven UI
    while dpg.is_dearpygui_running():
        engine.update()
        dpg.set_value("sim_output", f"Value: {engine.get_last_value():.3f}")
        dpg.render_dearpygui_frame()

    
    dpg.start_dearpygui()
    dpg.destroy_context()
