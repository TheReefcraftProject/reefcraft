# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""The geometric scene for the reef."""

import pygfx as gfx


class Reef:
    """The geometry, lighting, camera, and draw routines for the reef."""

    def __init__(self, renderer) -> None:
        self.renderer = renderer
        self.scene = gfx.Scene()

        cube = gfx.Mesh(gfx.box_geometry(1, 1, 1), gfx.MeshPhongMaterial(color="#0040ff"))
        cube.local.position = (0, 0.5, 0)
        self.scene.add(cube)

        self.scene.add(gfx.AmbientLight("#fff", 0.3))
        light = gfx.DirectionalLight("#fff", 3)
        light.local.position = (1.5, 2.0, 4.0)
        self.scene.add(light)

        grid = gfx.Grid(
            None,
            gfx.GridMaterial(
                major_step=0.1,
                minor_step=0.01,
                thickness_space="world",
                axis_thickness=0.0025,
                axis_color="#9A9AE4BD",
                major_thickness=0.002,
                major_color="#8D8DC08B",
                minor_thickness=0.001,
                minor_color="#5D5D785A",
                infinite=True,
            ),
            orientation="xz",
        )
        grid.local.position = (0, -0.001, 0)
        self.scene.add(grid)

        self.camera = gfx.PerspectiveCamera()
        self.controller = gfx.OrbitController(self.camera, register_events=self.renderer)
        self.camera.show_object(self.scene)

    def draw(self) -> None:
        """Draw a solid rectangle on the left side of the UI scene."""
        self.renderer.render(self.scene, self.camera, flush=False)
