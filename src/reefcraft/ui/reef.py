# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""The geometric scene for the reef."""

import numpy as np
import pygfx as gfx

from reefcraft.sim.state import CoralState, SimState
from reefcraft.ui.water import WaterParticles
from reefcraft.utils.logger import logger


class CoralMesh:
    """The buffers for the mesh representing the coral we are growing."""

    def __init__(self, scene: gfx.Scene) -> None:
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
        scene.add(self.mesh)

    def sync(self, state: CoralState) -> None:
        """Update the visualized mesh to the latest from the sim."""
        mesh_data = state.get_render_mesh()

        # for now always do a full update!
        # if subdivided:
        self.geometry.positions = gfx.Buffer(mesh_data["vertices"])
        self.geometry.indices = gfx.Buffer(mesh_data["indices"])
        # else
        # self.positions_buf.set_data(mesh_data["vertices"])


def create_rectangle_edges(y: float, width: float = 1.0, depth: float = 1.0, color: str = "#45CDF7") -> gfx.Line:
    """Create a dashed rectangle made of disconnected segments at y height."""
    w, d = width / 2, depth / 2

    # Explicit segment pairs (not a line strip)
    positions = np.array(
        [
            [-w, y, -d],
            [+w, y, -d],  # front edge
            [+w, y, -d],
            [+w, y, +d],  # right edge
            [+w, y, +d],
            [-w, y, +d],  # back edge
            [-w, y, +d],
            [-w, y, -d],  # left edge
        ],
        dtype=np.float32,
    )

    geometry = gfx.Geometry(positions=positions)

    material = gfx.LineSegmentMaterial(
        color=color,
        thickness=2,
        dash_pattern=[
            5,
            5,
        ],
        thickness_space="screen",
    )

    return gfx.Line(geometry, material)


class Reef:
    """The geometry, lighting, camera, and draw routines for the reef."""

    def __init__(self, renderer: gfx.WgpuRenderer) -> None:
        """Prepare the Reef class to hold a 3D scene including the coral."""
        self.renderer = renderer
        self.viewport = gfx.Viewport(renderer)
        self.scene = gfx.Scene()

        self.corals: dict[CoralState, CoralMesh] = {}

        self.water_particles = WaterParticles()
        self.scene.add(self.water_particles.get_actor())

        self.scene.add(gfx.AmbientLight("#fff", 0.3))
        light = gfx.DirectionalLight("#fff", 3)
        light.local.position = (1.5, 2.0, 1.0)
        self.scene.add(light)

        # TODO read in the size of the simualtion space
        self._sim_bottom: gfx.Line | None = None
        self._sim_top: gfx.Line | None = None
        self.generate_sim_volume(100.0, 100.0, 100.0)

        grid = gfx.Grid(
            None,
            gfx.GridMaterial(
                major_step=10,
                minor_step=1,
                thickness_space="world",
                axis_thickness=0.2,
                axis_color="#9A9AE4C1",
                major_thickness=0.1,
                major_color="#8D8DC099",
                minor_thickness=0.08,
                minor_color="#5D5D7876",
                infinite=True,
            ),
            orientation="xz",
        )
        grid.local.position = (0, -0.001, 0)
        self.scene.add(grid)

        self.camera = gfx.PerspectiveCamera()
        self.controller = gfx.OrbitController(self.camera, register_events=self.viewport)
        self.camera.show_object(self.scene)

    def generate_sim_volume(self, width: float, depth: float, height: float) -> None:
        """Create dashed box outline for simulation volume."""

        def create_rectangle_edges(y: float) -> gfx.Line:
            w, d = width / 2, depth / 2
            positions = np.array(
                [
                    [-w, y, -d],
                    [+w, y, -d],
                    [+w, y, -d],
                    [+w, y, +d],
                    [+w, y, +d],
                    [-w, y, +d],
                    [-w, y, +d],
                    [-w, y, -d],
                ],
                dtype=np.float32,
            )
            geometry = gfx.Geometry(positions=positions)
            # TODO read the color and line thickness from the theme
            material = gfx.LineSegmentMaterial(
                color="#45CDF7",
                thickness=0.2,
                dash_pattern=[12, 8],
                dash_offset=6,
                thickness_space="model",
            )
            return gfx.Line(geometry, material)

        # Remove old ones if present
        if self._sim_bottom:
            self.scene.remove(self._sim_bottom)
        if self._sim_top:
            self.scene.remove(self._sim_top)

        self._sim_bottom = create_rectangle_edges(y=0)
        self._sim_top = create_rectangle_edges(y=height)

        self.sim_width = width
        self.sim_depth = depth
        self.sim_height = height

        self.scene.add(self._sim_bottom)
        self.scene.add(self._sim_top)

    def draw(self, state: SimState) -> None:
        """Update the reef scene and draw."""
        for coral_state in state.corals:
            if coral_state not in self.corals:
                self.corals[coral_state] = CoralMesh(self.scene)
            self.corals[coral_state].sync(coral_state)

        self.water_particles.advect(state.get_fields()["velocity"])
        # DEBUG
        # mean_speed = np.mean(np.linalg.norm(state.velocity_field, axis=-1))
        # print(f"Mean fluid speed: {mean_speed}")

        self.viewport.render(self.scene, self.camera)
