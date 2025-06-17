# -----------------------------------------------------------------------------
# Copyright (c) 2025
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

import time

import dearpygui.dearpygui as gui
import reefcraft
from system_utils import enable_windows_dark_titlebar

# Constants
WINDOW_DURATION = 5.0  # Show last 5 seconds of data
SAMPLE_RATE_HZ = 100.0  # Sample 100 times per second

# Create and configure the GUI context and font
gui.create_context()
with gui.font_registry():
    app_font = gui.add_font("app/fonts/Archivo-Regular.ttf", 14)
gui.bind_font(app_font)

# Setup main application window
gui.create_viewport(title="Reefcraft", width=800, height=600)
gui.setup_dearpygui()
gui.show_viewport()
enable_windows_dark_titlebar("Reefcraft")

# Create oscilloscope plot inside a window
with gui.window(label="Oscilloscope", pos=(50, 50), no_collapse=True, width=650, height=400), gui.plot(label="sim_value(t)", height=350, width=600):
    x_axis = gui.add_plot_axis(gui.mvXAxis, label="Time (s)", tag="x_axis")
    y_axis = gui.add_plot_axis(gui.mvYAxis, label="Value", tag="y_axis")
    gui.set_axis_limits("y_axis", -1.5, 1.5)
    line_series = gui.add_line_series([], [], parent=y_axis, tag="series")

# Initialize buffers and time origin
time_values = []
signal_values = []
start_time = time.time()


def update_plot() -> None:
    # Calculate time since start
    current_time = time.time() - start_time

    # Get new sample from C++ extension
    current_value = reefcraft.sim_value(current_time)

    # Append sample to buffer
    time_values.append(current_time)
    signal_values.append(current_value)

    # Trim values outside the visible time window
    cutoff_time = current_time - WINDOW_DURATION
    while time_values and time_values[0] < cutoff_time:
        time_values.pop(0)
        signal_values.pop(0)

    # Update the graph with new data
    gui.set_value(line_series, (time_values, signal_values))
    gui.set_axis_limits("x_axis", max(cutoff_time, 0), current_time)

    # Schedule the next frame update
    next_frame_index = gui.get_frame_count() + 1
    gui.set_frame_callback(next_frame_index, update_plot)


# Schedule first update (delay by 2 frames for dark mode to apply)
# The callback for frame 1 is reserved for the dark mode event
initial_frame = gui.get_frame_count() + 2
gui.set_frame_callback(initial_frame, update_plot)

# Run the GUI application
gui.start_dearpygui()
gui.destroy_context()
