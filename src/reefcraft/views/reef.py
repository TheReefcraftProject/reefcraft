# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""The geometric scene for the reef."""

import numpy as np
import pygfx as gfx

from reefcraft.sim.sim_context import CoralContext, SimContext
from reefcraft.utils.logger import logger


class CoralMesh:
    """The buffers for the mesh representing the coral we are growing."""

    def __init__(self) -> None:
        """Allocate raw buffers to hold the coral geometery positions, faces, etc."""
        # 1) Three 3-D points (x, y, z) for the triangle’s corners
        self.vertices = np.array(
            [
                [0.0, 0.0, 0.0],  # vertex 0
                [1.0, 0.0, 0.0],  # vertex 1
                [0.0, 1.0, 0.0],  # vertex 2
            ],
            dtype=np.float32,
        )

        # 2) A flat index list saying “one triangle: connect 0→1→2”
        self.indices = np.array([0, 1, 2], dtype=np.uint32)

        # 3) Wrap those in gfx.Buffer and build your Geometry
        # self.positions_buf = gfx.Buffer(self.vertices)
        # self.indices_buf = gfx.Buffer(self.indices)

        # self.geometry = gfx.Geometry(
        #     positions=self.positions_buf,
        #     indices=self.indices_buf,
        # )
        self.geometry = gfx.Geometry(positions=self.vertices, indices=self.indices)
        gfx.Mesh(self.geometry, gfx.MeshPhongMaterial(color="#0040ff"))
        self.material = gfx.MeshPhongMaterial(color="#0040ff")  # Tell the material to use vertex colors

    def update(self, context: CoralContext) -> None:
        """Update the visualized mesh to the latest from the sim."""
        mesh_data = context.get_render_mesh()
        # if mesh_data["verts"] is not None:
        # for now always do a full update!
        # self.geometry.positions = gfx.Buffer(mesh_data["verts"])
        # self.geometry.indices = gfx.Buffer(mesh_data["faces"])


class Reef:
    """The geometry, lighting, camera, and draw routines for the reef."""

    def __init__(self, renderer: gfx.WgpuRenderer) -> None:
        """Prepare the Reef class to hold a 3D scene including the coral."""
        self.renderer = renderer
        self.viewport = gfx.Viewport(renderer)
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
        self.controller = gfx.OrbitController(self.camera, register_events=self.viewport)
        self.camera.show_object(self.scene)

    def update(self, time: float, sim_context: SimContext) -> None:
        """Update the reef scene and draw."""
        self.coral.update(sim_context.coral)
        pass

    def draw(self) -> None:
        """Update the reef scene and draw."""
        self.viewport.render(self.scene, self.camera)
