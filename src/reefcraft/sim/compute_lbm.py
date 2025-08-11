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


class ComputeLBM:
    """Compute water states with LBM."""

    def __init__(self, grid_shape: tuple, fluid_speed: float, Re: float) -> None:
        """Initialize ComputeLBM fields and data."""
        self.grid_shape = grid_shape
        self.fluid_speed = fluid_speed
        self.current_step = 0
        self.coral_vertices = None
        self.coral_indices = None
        self.boundary_conditions = []
        self.Re = Re
        self.clength = self.grid_shape[0] - 1
        self.visc = self.fluid_speed * self.clength / self.Re
        self.omega = 0.5

        self.compute_backend = ComputeBackend.WARP
        self.precision_policy = PrecisionPolicy.FP32FP32

        self.velocity_set = xlb.velocity_set.D3Q19(precision_policy=self.precision_policy, backend=self.compute_backend)
        xlb.init(velocity_set=self.velocity_set, default_backend=self.compute_backend, default_precision_policy=self.precision_policy)
        self.grid = grid_factory(self.grid_shape, compute_backend=self.compute_backend)

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

    def update_mesh(self, mesh_data: tuple[wp.array, wp.array]) -> None:
        """Update Coral and boundary conditions."""
        # Convert warp's to NumPy array for vertices
        self.coral_vertices = mesh_data[0].numpy()
        self.coral_indices = mesh_data[1].numpy()

        # Shift to xy plane center - from 0,0,0 center
        shift = np.array([self.grid_shape[0] / 2, self.grid_shape[1] / 2, 0.0])

        # Apply the shift to the vertices
        self.coral_vertices = self.coral_vertices + shift

        # Now, create the Trimesh object
        coral_mesh = trimesh.Trimesh(vertices=self.coral_vertices, faces=self.coral_indices)

        self.coral_vertices = coral_mesh.vertices
        self.coral_indices = coral_mesh.faces

        self.setup_boundary_conditions(True)

        self.f_0, self.f_1, self.bc_mask, self.missing_mask = self.stepper.prepare_fields()

    def setup_boundary_conditions(self, update_coral: bool) -> None:
        """Boundary conditions for the simulation."""
        box_no_edge = self.grid.bounding_box_indices(remove_edges=True)

        inlet = box_no_edge["left"]
        outlet = box_no_edge["right"]
        walls = [box_no_edge["bottom"][i] + box_no_edge["top"][i] + box_no_edge["front"][i] + box_no_edge["back"][i] for i in range(self.velocity_set.d)]
        walls = np.unique(np.array(walls), axis=-1).tolist()

        bc_left = RegularizedBC("velocity", prescribed_value=(self.fluid_speed, 0.0, 0.0), indices=inlet)
        bc_walls = FullwayBounceBackBC(indices=walls)
        bc_do_nothing = ExtrapolationOutflowBC(indices=outlet)

        if update_coral:
            bc_coral = HalfwayBounceBackBC(
                velocity_set=self.velocity_set,
                precision_policy=self.precision_policy,
                compute_backend=self.compute_backend,
                mesh_vertices=self.coral_vertices,
            )
            self.boundary_conditions = [bc_coral, bc_walls, bc_left, bc_do_nothing]
            self.stepper.boundary_conditions = self.boundary_conditions
        else:
            self.boundary_conditions = [bc_walls, bc_left, bc_do_nothing]
            self.stepper.boundary_conditions = self.boundary_conditions

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
        # print(fields["velocity"])
        return fields

    def step(self, dt: float) -> None:
        """Run one iteration of LBM."""
        self.f_0, self.f_1 = self.stepper(self.f_0, self.f_1, self.bc_mask, self.missing_mask, self.current_step)
        self.f_0, self.f_1 = self.f_1, self.f_0
        self.current_step += 1
