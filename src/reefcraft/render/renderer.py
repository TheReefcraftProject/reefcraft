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

        # 2) Make a proper 3D camera
        # self.canvas = canvas
        w, h = canvas.get_physical_size()  # returns (width, height)
        self.camera = gfx.PerspectiveCamera(70, w / h)  # fov=70°, aspect=w/h
        self.camera.local.position = (5, 5, 5)  # place the camera
        self.camera.look_at((0, 0, 0))  # aim at the origin

        # 4) Build the scene and add a row of cubes
        self.scene = gfx.Scene()
        # self.scene.add(gfx.Background.from_color("#fff"))
        cube_geo = gfx.box_geometry(1, 1, 1)  # unit box :contentReference[oaicite:0]{index=0}
        cube_mat = gfx.MeshBasicMaterial(color=(0.2, 0.6, 0.8, 1.0))

        for i in range(3):
            cube = gfx.Mesh(cube_geo, cube_mat)
            # assign a tuple, *not* cube.local.position.set(...)
            cube.local.position = ((i - 1) * 2.5, 0, 0)
            self.scene.add(cube)

        # 5) Add lighting
        self.scene.add(gfx.AmbientLight(color=(0.2, 0.2, 0.2)))
        light = gfx.DirectionalLight(color="white", intensity=1.0)
        light.local.position = (5, 10, 5)
        self.scene.add(light)
        self.stats = gfx.Stats(viewport=self.renderer)

        self.controller = gfx.OrbitController(self.camera, register_events=self.renderer)

        self.renderer.request_draw(self.update)

    def update(self) -> None:
        """Render one frame of the simulation and overlay UI."""
        # print("[DEBUG] self.renderer.render")
        with self.stats:
            self.renderer.render(self.scene, self.camera, flush=False)
        self.stats.render()
