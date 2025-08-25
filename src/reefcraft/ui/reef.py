# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""The geometric scene for the reef visualization.

This module provides the Reef class that manages the 3D visualization scene
for the coral reef simulation. It handles the 3D scene setup, lighting,
camera controls, and rendering of coral meshes and water particles.

The Reef class provides:
- 3D scene management with lighting and camera controls
- Coral mesh visualization and synchronization
- Water particle effects for fluid visualization
- Simulation volume visualization with grid and boundaries
- Integration with the simulation engine and state
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pygfx as gfx

from reefcraft.sim.state import CoralState, SimState
from reefcraft.ui.school import FishSchool
from reefcraft.ui.water import WaterParticles

if TYPE_CHECKING:
    from reefcraft.sim.engine import Engine
    from reefcraft.sim.state import CoralState, SimState


class CoralMesh:
    """The buffers for the mesh representing the coral we are growing.

    CoralMesh manages the 3D mesh representation of a coral entity,
    including vertex positions, face indices, and geometry buffers.
    It provides synchronization between the simulation state and
    the visual representation.

    Attributes:
        vertices: NumPy array of vertex positions
        indices: NumPy array of face indices
        positions_buf: PyGFX buffer for vertex positions
        indices_buf: PyGFX buffer for face indices
        geometry: PyGFX geometry object combining positions and indices
        mesh: PyGFX mesh object with material for rendering
    """

    def __init__(self, scene: gfx.Scene) -> None:
        """Initialize the coral mesh with placeholder geometry.

        Creates a simple triangular mesh as a placeholder and adds it
        to the scene. The mesh uses a blue material for visibility.

        Args:
            scene: The PyGFX scene to add the coral mesh to
        """
        # Hand-rolled triangle as a placeholder
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
        """Update the visualized mesh to match the latest simulation state.

        Synchronizes the visual mesh with the current coral state from
        the simulation. Currently performs a full geometry update, but
        could be optimized for incremental updates in the future.

        Args:
            state: The current coral state containing mesh data
        """
        mesh_data = state.get_render_mesh()
        if mesh_data is None:
            return

        # For now, always do a full update!
        # TODO: Implement incremental updates for subdivided meshes
        # if subdivided:
        self.geometry.positions = gfx.Buffer(mesh_data["vertices"])
        self.geometry.indices = gfx.Buffer(mesh_data["indices"])
        # else
        # self.positions_buf.set_data(mesh_data["vertices"])


def create_rectangle_edges(y: float, width: float = 1.0, depth: float = 1.0, color: str = "#45CDF7") -> gfx.Line:
    """Create a dashed rectangle made of disconnected line segments at y height.

    Creates a rectangular outline using individual line segments rather than
    a continuous line strip. This allows for dashed line effects and better
    control over the appearance.

    Args:
        y: The y-coordinate (height) where the rectangle is positioned
        width: The width of the rectangle along the x-axis
        depth: The depth of the rectangle along the z-axis
        color: The color of the line segments in hex format

    Returns:
        A PyGFX Line object representing the dashed rectangle outline
    """
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
        dash_pattern=[5, 5],
        thickness_space="screen",
    )

    return gfx.Line(geometry, material)


class Reef:
    """The geometry, lighting, camera, and draw routines for the reef.

    The Reef class manages the complete 3D visualization environment for
    the coral reef simulation. It handles scene setup, lighting, camera
    controls, coral mesh management, water particle effects, and rendering.

    Key features:
    - 3D scene with ambient and directional lighting
    - Orbit camera controller for interactive viewing
    - Coral mesh visualization and synchronization
    - Water particle effects for fluid visualization
    - Grid and simulation volume boundaries
    - Integration with simulation engine and state

    The class automatically manages:
    - Scene hierarchy and object lifecycle
    - Camera positioning and controls
    - Lighting setup and positioning
    - Water particle animation and updates
    - Simulation volume visualization

    Attributes:
        renderer: PyGFX WGPU renderer for graphics output
        viewport: PyGFX viewport for rendering
        scene: PyGFX scene containing all 3D objects
        engine: Optional reference to the simulation engine
        corals: Dictionary mapping coral states to their mesh representations
        water_particles: Water particle system for fluid visualization
        _advect_counter: Counter for throttling water particle updates
        _sim_bottom: Line representing the bottom of the simulation volume
        _sim_top: Line representing the top of the simulation volume
        sim_width: Width of the simulation volume
        sim_depth: Depth of the simulation volume
        sim_height: Height of the simulation volume
        camera: Perspective camera for 3D viewing
        controller: Orbit controller for camera manipulation
    """

    def __init__(self, renderer: gfx.WgpuRenderer, engine: Engine | None = None) -> None:
        """Initialize the reef visualization scene.

        Sets up the complete 3D visualization environment including:
        - Scene, viewport, and renderer setup
        - Lighting configuration (ambient + directional)
        - Camera and orbit controller
        - Grid and simulation volume boundaries
        - Water particle system
        - Coral mesh management

        Args:
            renderer: PyGFX WGPU renderer for graphics output
            engine: Optional reference to the simulation engine
        """
        self.renderer = renderer
        self.viewport = gfx.Viewport(renderer)
        self.scene = gfx.Scene()
        self.engine = engine

        self.corals: dict[CoralState, CoralMesh] = {}

        # self.water_particles = WaterParticles()
        # self.scene.add(self.water_particles.get_actor())
        self.school = FishSchool()
        self.scene.add(self.school.get_actor())

        # Setup lighting
        self.scene.add(gfx.AmbientLight("#fff", 0.3))
        light = gfx.DirectionalLight("#fff", 3)
        light.local.position = (1.5, 2.0, 1.0)
        self.scene.add(light)

        # TODO: Read simulation space size from configuration
        self._sim_bottom: gfx.Line | None = None
        self._sim_top: gfx.Line | None = None
        self.generate_sim_volume(100.0, 100.0, 100.0)

        # Add reference grid
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

        # Setup camera and controls
        self.camera = gfx.PerspectiveCamera()
        self.controller = gfx.OrbitController(self.camera, register_events=self.viewport)
        self.camera.show_object(self.scene)

    def generate_sim_volume(self, width: float, depth: float, height: float) -> None:
        """Create dashed box outline for simulation volume visualization.

        Generates a visual representation of the simulation boundaries using
        dashed line segments at the bottom and top of the volume. This helps
        users understand the spatial extent of the simulation.

        Args:
            width: Width of the simulation volume along the x-axis
            depth: Depth of the simulation volume along the z-axis
            height: Height of the simulation volume along the y-axis
        """

        def create_rectangle_edges(y: float) -> gfx.Line:
            """Create rectangle edges at the specified y-coordinate."""
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
            # TODO: Read color and line thickness from theme configuration
            material = gfx.LineSegmentMaterial(
                color="#45CDF7",
                thickness=0.2,
                dash_pattern=[12, 8],
                dash_offset=6,
                thickness_space="model",
            )
            return gfx.Line(geometry, material)

        # Remove old boundaries if present
        if self._sim_bottom:
            self.scene.remove(self._sim_bottom)
        if self._sim_top:
            self.scene.remove(self._sim_top)

        self._sim_bottom = create_rectangle_edges(y=0)
        self._sim_top = create_rectangle_edges(y=height)

        # Store dimensions for reference
        self.sim_width = width
        self.sim_depth = depth
        self.sim_height = height

        # Add boundaries to scene
        self.scene.add(self._sim_bottom)
        self.scene.add(self._sim_top)

    def draw(self, state: SimState) -> None:
        """Update the reef scene and render the current frame.

        Updates the visualization based on the current simulation state,
        including water particle animation and coral mesh synchronization.
        The method handles rendering the complete scene to the viewport.

        Note:
            Direct coral mesh synchronization from SimState is deprecated;
            RenderBridge now updates meshes via the data store. Water particle
            visualization is maintained for now, with throttled updates when
            the simulation is paused.

        Args:
            state: Current simulation state containing coral and fluid data
        """
        # Deprecated direct sync from SimState; RenderBridge now updates meshes via store
        # Keeping water particles visualization for now; throttle when paused
        if getattr(self.engine, "is_playing", False) and state.water.coral_vertices is not None:
            self.school.step(state.get_fields()["velocity"], state.time, state.last_dt)

        # DEBUG: Uncomment for fluid speed monitoring
        # mean_speed = np.mean(np.linalg.norm(state.velocity_field, axis=-1))
        # print(f"Mean fluid speed: {mean_speed}")

        self.viewport.render(self.scene, self.camera)
