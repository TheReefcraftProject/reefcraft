# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Entrypoint for the Reefcraft GUI application."""

# from gui.main_window import launch_app
# if __name__ == "__main__":
#    launch_app(app_root=APP_ROOT)
import os
from pathlib import Path

import taichi.math as tm
from utils.window_style import apply_dark_titlebar_and_icon

APP_ROOT = Path(__file__).resolve().parent  # → reefcraft/app

os.environ["TI_LOG"] = "debug"  # get verbose Taichi logs
import taichi as ti

ti.init(arch=ti.vulkan, debug=True)  # enable debug mode for Vulkan

# Initialize Taichi
ti.init(arch=ti.gpu)

# Resolution parameters
n = 320
pixels = ti.field(dtype=ti.f32, shape=(n * 2, n))


@ti.func
def complex_sqr(z):  # complex square of a 2D vector
    return tm.vec2(z[0] * z[0] - z[1] * z[1], 2 * z[0] * z[1])


@ti.kernel
def paint(t: float):
    for i, j in pixels:  # Parallelized over all pixels
        c = tm.vec2(-0.8, tm.cos(t) * 0.2)
        z = tm.vec2(i / n - 1, j / n - 0.5) * 2
        iterations = 0
        while z.norm() < 20 and iterations < 50:
            z = complex_sqr(z) + c
            iterations += 1
        pixels[i, j] = 1 - iterations * 0.02


# Create a window using the new GGUI API
window = ti.ui.Window(name="Reefcraft", res=(n * 2, n))  # ([docs.taichi-lang.org](https://docs.taichi-lang.org/docs/ggui))
canvas = window.get_canvas()  # ([docs.taichi-lang.org](https://docs.taichi-lang.org/docs/ggui))

icon_path = (APP_ROOT / "resources" / "icon" / "reefcraft.ico").resolve()
apply_dark_titlebar_and_icon("Reefcraft", icon_path)

i = 0
while window.running:
    paint(i * 0.03)
    canvas.set_image(pixels)
    window.show()
    i += 1
