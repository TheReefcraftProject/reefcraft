# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------
"""LBM computation engine."""

import numpy as np
import trimesh
import warp as wp
import xlb.velocity_set
from xlb.compute_backend import ComputeBackend
from xlb.grid import grid_factory
from xlb.operator.boundary_condition import ExtrapolationOutflowBC, FullwayBounceBackBC, HalfwayBounceBackBC, RegularizedBC
from xlb.operator.macroscopic import Macroscopic
from xlb.operator.stepper import IncompressibleNavierStokesStepper
from xlb.precision_policy import PrecisionPolicy

from reefcraft.sim.state import SimState


class ComputeLBM:
    """Compute water states with LBM."""

    def __init__(self) -> None:
        """Initialize ComputeLBM fields and data."""
        self.grid_shape = (32, 32, 32)
        self.fluid_speed = 0.2
        self.current_step = 0
        self.bc_coral = None
        self.stl_filename = "src/reefcraft/resources/stl/coral.stl"
        self.Re = 30000.0
        self.clength = self.grid_shape[0] - 1
        self.visc = self.fluid_speed * self.clength / self.Re
        self.omega = 0.5

        self.compute_backend = ComputeBackend.WARP
        self.precision_policy = PrecisionPolicy.FP32FP32

        self.velocity_set = xlb.velocity_set.D3Q19(precision_policy=self.precision_policy, backend=self.compute_backend)
        xlb.init(velocity_set=self.velocity_set, default_backend=self.compute_backend, default_precision_policy=self.precision_policy)
        self.grid = grid_factory(self.grid_shape, compute_backend=self.compute_backend)

        self.load_mesh()
        self.setup_boundary_conditions()

        self.stepper = IncompressibleNavierStokesStepper(
            omega=self.omega,
            grid=self.grid,
            boundary_conditions=self.boundary_conditions,
            collision_type="BGK",
        )
        self.macro = Macroscopic(
            compute_backend=self.compute_backend,
            precision_policy=self.precision_policy,
            velocity_set=self.velocity_set,
        )

        self.f_0, self.f_1, self.bc_mask, self.missing_mask = self.stepper.prepare_fields()

    def load_mesh(self, shift_up: float = 15.0) -> None:
        """Load coral mesh from stl file."""
        # Load and process mesh for the simulation
        mesh = trimesh.load_mesh(self.stl_filename, process=False)
        mesh_vertices = mesh.vertices
        self.coral_faces = mesh.faces

        # Define the scaling factor (shrink by a factor of x)
        scaling_factor = 300.0

        # Scale down the vertices by the scaling factor
        mesh_vertices /= scaling_factor

        # Convert the mesh to Warp arrays
        self.verts = wp.array(np.array(mesh_vertices, dtype=np.float32), dtype=wp.vec3f)
        self.faces = wp.array(np.array(self.coral_faces, dtype=np.int32), dtype=wp.vec3i)

        # Transform mesh points to align with grid
        mesh_vertices -= mesh_vertices.min(axis=0)
        mesh_extents = mesh_vertices.max(axis=0)
        length_phys_unit = mesh_extents.max()
        length_lbm_unit = self.grid_shape[0] / 4
        dx = length_phys_unit / length_lbm_unit
        mesh_vertices = mesh_vertices / dx

        # Shift mesh to align with the grid and move it up along the z-axis
        shift = np.array([self.grid_shape[0] / 4, (self.grid_shape[1] - mesh_extents[1] / dx) / 2, shift_up])

        self.coral_vertices = mesh_vertices + shift

        # Cross-sectional area for the coral mesh (just for boundary condition purposes)
        self.coral_cross_section = np.prod(mesh_extents[1:]) / dx**2

    def update_mesh(self, state: SimState) -> None:
        """Update Coral and boundry conditions."""
        state.coral.set_mesh(self.verts, self.faces)

    def setup_boundary_conditions(self) -> None:
        """Boundry conditions."""
        # Boundary conditions
        # box = self.grid.bounding_box_indices()
        box_no_edge = self.grid.bounding_box_indices(remove_edges=True)

        inlet = box_no_edge["left"]
        outlet = box_no_edge["right"]
        walls = [box_no_edge["bottom"][i] + box_no_edge["top"][i] + box_no_edge["front"][i] + box_no_edge["back"][i] for i in range(self.velocity_set.d)]
        walls = np.unique(np.array(walls), axis=-1).tolist()

        bc_left = RegularizedBC("velocity", prescribed_value=(self.fluid_speed, 0.0, 0.0), indices=inlet)
        bc_walls = FullwayBounceBackBC(indices=walls)
        bc_do_nothing = ExtrapolationOutflowBC(indices=outlet)
        bc_coral = FullwayBounceBackBC(mesh_vertices=self.coral_vertices)  # Adding the coral mesh as a BC

        self.boundary_conditions = [bc_walls, bc_left, bc_do_nothing, bc_coral]

    def get_field_numpy(self) -> dict:
        """Get water data fields."""
        rho_field = self.grid.create_field(cardinality=1)
        u_field = self.grid.create_field(cardinality=self.velocity_set.d)

        rho_field, u_field = self.macro(self.f_0, rho_field, u_field)

        rho_np = rho_field.numpy()[0].astype(np.float32)
        u_np = u_field.numpy().astype(np.float32)

        u_np = np.moveaxis(u_np, 0, -1)

        pressure_np = (rho_np - 1.0) / 3.0
        vel_mag_np = np.linalg.norm(u_np, axis=-1)

        fields = {
            "density": rho_np,
            "pressure": pressure_np.astype(np.float32),
            "velocity": u_np,
            "velocity_magnitude": vel_mag_np.astype(np.float32),
        }

        return fields

    def step(self, state: SimState) -> None:
        """Run one iteration of LBM."""
        self.f_0, self.f_1 = self.stepper(self.f_0, self.f_1, self.bc_mask, self.missing_mask, self.current_step)
        self.f_0, self.f_1 = self.f_1, self.f_0
        self.current_step += 1
        # time.sleep(1.0 / steps_per_second)  # Control real-time step rate
        state.velocity_field = self.get_field_numpy()["velocity"]
