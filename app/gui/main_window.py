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

import math


def launch_app(app_root: Path) -> None:
    settings = load_settings()
    engine = SimulationEngine()

    # def update_sim():
    #     engine.update()
    #     dpg.set_value("sim_output", f"Value: {engine.get_last_value(): .3f}")

    def on_growth_rate_change(sender, app_data, user_data):
        engine.set_growth_rate(app_data)

    def draw_blob(output_value, time) -> None:
        dpg.delete_item("blob_canvas", children_only=True)

        cx, cy = 300, 200
        base_radius_nominal = 100
        breath_amplitude = 10
        base_radius = base_radius_nominal + math.sin(time * 1.5) * breath_amplitude

        noise_amp = 10
        segments = 50
        points = []

        for i in range(segments):
            theta = i / segments * 2 * math.pi
            noise = (
                math.sin(theta * 5 + time * 2) +
                0.5 * math.sin(theta * 8 + time * 3)
            )
            r = base_radius + output_value * noise_amp * noise
            x = cx + r * math.cos(theta)
            y = cy + r * math.sin(theta)
            points.append((x, y))

        points.append(points[0])  # close the circle (there's still a break ugh)
    
        # Base color modulation
        r = int(150 + 50 * math.sin(time * 0.2))
        g = int(100 + 40 * math.sin(time * 0.7 + 2))
        b = int(220 + 35 * math.sin(time * 0.4 + 5))

        core_color = (r, g, b, 80)     # fill
        # glow_color = (r, g, b, 60)     # wide glow (not used here, preferred manual)
        edge_color = (r, g, b, 155)    # outline

        # fill: soft, semi-transparent core
        dpg.draw_polygon(points=points, color=edge_color, fill=core_color, parent="blob_canvas")

        # glow stroke 0.5: WIDE and FAINT
        dpg.draw_polyline(points=points, color=(130, 150, 255, 10), thickness=50, parent="blob_canvas")

        # glow stroke 1: wide and faint
        dpg.draw_polyline(points=points, color=(180, 150, 255, 20), thickness=30, parent="blob_canvas")

        # glow stroke 1.5: not as wide and bolder
        dpg.draw_polyline(points=points, color=(180, 150, 255, 30), thickness=15, parent="blob_canvas")

        # glow stroke 2: tighter and bolder
        dpg.draw_polyline(points=points, color=(150, 100, 230, 105), thickness=5, parent="blob_canvas")


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
        dpg.add_slider_float(label="Growth Rate", default_value=1.0, min_value=0.01, max_value=5.0, callback=on_growth_rate_change)
        dpg.add_button(label="Start Simulation", callback=lambda: (print("[Start] clicked"), engine.start()))
        dpg.add_button(label="Pause", callback=lambda: engine.pause())
        dpg.add_button(label="Reset", callback=lambda: engine.reset())
        dpg.add_spacer(height=10)
        dpg.add_text("Value: 0.000", tag="sim_output")

    with dpg.window(label="Visual Output", tag="visual_window", pos=(320, 120), width=600, height=400):
        with dpg.drawlist(width=600, height=400, tag="blob_canvas"):
            pass  # initially empty; we'll draw into this

    # with dpg.window(label="Output / Log", tag="log_window", pos=(320, 0), width=860, height=400):
    # dpg.add_text("Status output...")
    # dpg.show_logger()

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.render_dearpygui_frame()

    from app.utils.window_style import apply_dark_titlebar_and_icon

    icon_path = (app_root / "resources" / "icon" / "reefcraft.ico").resolve()
    apply_dark_titlebar_and_icon("Reefcraft", icon_path)
    dpg.set_primary_window("control_window", True)


# NOTE: This manual render loop is required due to limitations in DearPyGui 2.0.0,
# which removed per-frame callbacks like `set_render_callback()` and 
# `add_viewport_draw_handler()` from earlier versions.
#
# If future versions of DPG reintroduce frame-level update hooks, or if the
# experimental task system and plugin extensions become stable and documented,
# we may replace this loop with a callback- or coroutine-based update mechanism.

    while dpg.is_dearpygui_running():
        engine.update()
        value = engine.get_last_value()
        time = engine.get_time()
        
        dpg.set_value("sim_output", f"Value: {engine.get_last_value():.3f}")
        draw_blob(value, time)
        
        dpg.render_dearpygui_frame()

    # dpg.start_dearpygui() --> replaced by above loop
    dpg.destroy_context()
