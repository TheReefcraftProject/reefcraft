# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""The geometric scene for the reef."""

import numpy as np
import pygfx as gfx
import warp as wp
import wgpu


class CoralMesh:
    """The buffers for the mesh representing the coral we are growing."""

    def __init__(self) -> None:
        self.vertices, self.indicies = self.default_polyp_mesh(size=1.0, height=0.2, res=24)

        self.positions_buf = gfx.Buffer(self.vertices)
        self.indices_buf = gfx.Buffer(self.indicies)

        self.geometry = gfx.Geometry(positions=self.positions_buf, indices=self.indices_buf)
        self.material = gfx.MeshPhongMaterial(color="#0040ff")  # Tell the material to use vertex colors

    def default_polyp_mesh(self, size=1.0, height=0.3, res=16):
        """Returns: vertices: (res*res, 3) float32 array indices:  ((res-1)*(res-1)*2, 3) uint32 array."""
        # 1) build a res×res grid in the x–y plane
        xs = np.linspace(-size / 2, size / 2, res, dtype=np.float32)
        ys = np.linspace(-size / 2, size / 2, res, dtype=np.float32)
        xv, yv = np.meshgrid(xs, ys, indexing="xy")

        # 2) Gaussian bump for the mound normalized radius squared, falls off sharply
        rr = (xv / (size / 2)) ** 2 + (yv / (size / 2)) ** 2
        zv = height * np.exp(-5 * rr).astype(np.float32)

        # 3) Stack into vertex list
        vertices = np.stack([xv, zv, yv], axis=-1).reshape(-1, 3)

        # 4) Build quad‐to‐tri indices
        indices = []
        for i in range(res - 1):
            for j in range(res - 1):
                i0 = i * res + j
                i1 = i0 + 1
                i2 = i0 + res
                i3 = i2 + 1
                # two triangles per quad
                indices.append([i0, i2, i1])
                indices.append([i1, i2, i3])

        indices = np.array(indices, dtype=np.uint32)

        return vertices, indices


class Reef:
    """The geometry, lighting, camera, and draw routines for the reef."""

    def __init__(self, renderer) -> None:
        self.renderer = renderer
        self.scene = gfx.Scene()

        self.coral = CoralMesh()
        self.scene.add(gfx.Mesh(self.coral.geometry, self.coral.material))

        self.scene.add(gfx.AmbientLight("#fff", 0.3))
        light = gfx.DirectionalLight("#fff", 3)
        light.local.position = (1.5, 2.0, 1.0)
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

    def update(self, time: float) -> None:
        """Update the reef scene and draw."""
        # self.positions_buf.set_data(self.wp_vertices.numpy())
        self.renderer.render(self.scene, self.camera, flush=False)
