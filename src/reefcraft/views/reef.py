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

        self.scene.add(gfx.Mesh(gfx.box_geometry(1, 1, 1), gfx.MeshPhongMaterial(color="#0040ff")))

        self.scene.add(gfx.AmbientLight("#fff", 0.3))
        light = gfx.DirectionalLight("#fff", 3)
        light.local.position = (1.5, 2.0, 4.0)
        self.scene.add(light)

        self.camera = gfx.PerspectiveCamera()
        self.controller = gfx.OrbitController(self.camera, register_events=self.renderer)
        self.camera.show_object(self.scene)

    def draw(self) -> None:
        """Draw a solid rectangle on the left side of the UI scene."""
        self.renderer.render(self.scene, self.camera, flush=False)
