# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Defines the main GUI layout using Dear PyGui."""

import pygfx as gfx
from rendercanvas.auto import RenderCanvas


class Renderer:
    """Encapsulate the Dear PyGui viewport and overlay UI panel."""

    def __init__(self, canvas: RenderCanvas) -> None:
        self.renderer = gfx.WgpuRenderer(canvas)
        self.scene = gfx.Scene()

        self.scene.add(gfx.Mesh(gfx.box_geometry(1, 1, 1), gfx.MeshPhongMaterial(color="#0040ff")))

        light = gfx.DirectionalLight("#fff", 1)
        light.local.position = (1.5, 2.0, 4.0)
        self.scene.add(light)
        self.scene.add(gfx.AmbientLight("#fff", 0.3))

        self.camera = gfx.PerspectiveCamera()
        self.controller = gfx.OrbitController(self.camera, register_events=self.renderer)
        self.camera.show_object(self.scene)

        self.stats = gfx.Stats(viewport=self.renderer)

        self.renderer.request_draw(self.update)

    def update(self) -> None:
        """Render one frame of the simulation and overlay UI."""
        # print("[DEBUG] self.renderer.render")
        with self.stats:
            self.renderer.render(self.scene, self.camera, flush=False)
        self.stats.render()
