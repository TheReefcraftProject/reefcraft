# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Defines the main GUI layout and launch logic using Taichi."""

from __future__ import annotations

from typing import TYPE_CHECKING

import taichi as ti
from sim.sim import Sim
from utils.settings import load_settings

if TYPE_CHECKING:
    from pathlib import Path


def launch_app(app_root: Path) -> None:
    """Start the Taichi-based GUI."""
    load_settings()
    engine = Sim()

    ti.init()
    window = ti.ui.Window("Reefcraft", res=(400, 300))
    gui = window.get_gui()

    from app.utils.window_style import apply_dark_titlebar_and_icon

    icon_path = (app_root / "resources" / "icon" / "reefcraft.ico").resolve()
    apply_dark_titlebar_and_icon("Reefcraft", icon_path)

    while window.running:
        engine.update()

        gui.text("Simulation Controls")
        if gui.button("Start"):
            engine.start()
        gui.same_line()
        if gui.button("Pause"):
            engine.pause()
        gui.same_line()
        if gui.button("Reset"):
            engine.reset()

        gui.text(f"Time: {engine.get_time():.3f}")
        window.show()
