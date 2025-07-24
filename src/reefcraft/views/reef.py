# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""The geometric scene for the reef."""

import numpy as np
import pygfx as gfx

from reefcraft.sim.state import CoralState, SimState
from reefcraft.views.water import WaterParticles


class CoralMesh:
    """The buffers for the mesh representing the coral we are growing."""

    def __init__(self) -> None:
        """Allocate raw buffers to hold the coral geometery positions, faces, etc."""
        # Hand-rolled tri as a placeholder
        self.vertices = np.array(
            [
                [-0.5, 0.0, 0.0],
                [0.5, 0.0, 0.0],
                [0.0, 1.0, 0.0],
            ],
            dtype=np.float32,
        )
        self.indices = np.array(
            [
                [0, 1, 2],
            ],
            dtype=np.uint32,
        )
        self.positions_buf = gfx.Buffer(self.vertices)
        self.indices_buf = gfx.Buffer(self.indices)
        self.geometry = gfx.Geometry(positions=self.positions_buf, indices=self.indices_buf)
        self.mesh = gfx.Mesh(self.geometry, gfx.MeshPhongMaterial(color="#0040ff"))

    def sync(self, state: CoralState) -> None:
        """Update the visualized mesh to the latest from the sim."""
        mesh_data = state.get_render_mesh()

        # for now always do a full update!
        # if subdivided:
        self.geometry.positions = gfx.Buffer(mesh_data["vertices"])
        self.geometry.indices = gfx.Buffer(mesh_data["indices"])
        # else
        # self.positions_buf.set_data(mesh_data["vertices"])


class Reef:
    """The geometry, lighting, camera, and draw routines for the reef."""

    def __init__(self, renderer: gfx.WgpuRenderer) -> None:
        """Prepare the Reef class to hold a 3D scene including the coral."""
        self.renderer = renderer
        self.viewport = gfx.Viewport(renderer)
        self.scene = gfx.Scene()

        self.coral = CoralMesh()
        self.scene.add(self.coral.mesh)

        self.water_particles = WaterParticles()
        self.scene.add(self.water_particles.get_actor())

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

    def draw(self, state: SimState) -> None:
        """Update the reef scene and draw."""
        self.coral.sync(state.coral)
        self.water_particles.advect(state.velocity_field)

        #DEBUG
        # mean_speed = np.mean(np.linalg.norm(state.velocity_field, axis=-1))
        # print(f"Mean fluid speed: {mean_speed}")

        self.viewport.render(self.scene, self.camera)
