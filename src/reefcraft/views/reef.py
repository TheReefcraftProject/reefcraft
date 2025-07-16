# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""The geometric scene for the reef."""

import numpy as np
import pygfx as gfx

from reefcraft.sim.llabres import LlabresSurface


class Reef:
    """The geometry, lighting, camera, and draw routines for the reef."""

    def __init__(self, renderer) -> None:
        self.renderer = renderer
        self.scene = gfx.Scene()

        # Create Llabres surface
        self.surface = LlabresSurface(device="cuda")

        mesh_data = self.surface.get_numpy()

        self.positions_buf = gfx.Buffer(np.array(mesh_data["verts"], copy=True))
        self.indices_buf = gfx.Buffer(np.array(mesh_data["faces"], copy=True))
        self.normals_buf = gfx.Buffer(np.zeros_like(mesh_data["verts"]))  # Zero normals since wireframe

        self.geometry = gfx.Geometry(positions=self.positions_buf, indices=self.indices_buf, normals=self.normals_buf)
        self.material = gfx.MeshPhongMaterial(color="#0040ff", flat_shading=True)
        self.mesh = gfx.Mesh(self.geometry, self.material)
        self.mesh.local.rotation = np.array([-0.7071, 0.0, 0.0, 0.7071], dtype=np.float32)
        self.scene.add(self.mesh)

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

    def grow_and_draw(self):
        subdivided = self.surface.step()
        mesh_data = self.surface.get_numpy()

        if subdivided:
            # Topology changed → rebuild buffers
            self.positions_buf = gfx.Buffer(mesh_data["verts"])
            self.indices_buf = gfx.Buffer(mesh_data["faces"])
            self.normals_buf = gfx.Buffer(np.zeros_like(mesh_data["verts"]))

            self.geometry.positions = self.positions_buf
            self.geometry.indices = self.indices_buf
            self.geometry.normals = self.normals_buf
        else:
            # No subdivision → safe to update positions
            self.positions_buf.set_data(mesh_data["verts"])

        self.renderer.render(self.scene, self.camera, flush=False)
