# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------
"""LBM computation engine."""

import os
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
from xlb.utils import save_fields_vtk

class ComputeLBM:
    """Compute water states with LBM."""

    def __init__(self) -> None:
        """Initialize ComputeLBM fields and data."""
        self.grid_shape = (32, 32, 32)
        self.fluid_speed = 0.02
        self.current_step = 0
        self.bc_coral = None
        self.stl_filename = "src/reefcraft/resources/stl/coral.stl"
        self.Re = 30000.0
        self.clength = self.grid_shape[0] - 1
        self.visc = self.fluid_speed * self.clength / self.Re
        self.omega = 0.5
        self.post_process_interval = 50
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

    def load_mesh(self) -> None:
        """Load coral mesh from stl file."""
        # Load and process mesh for the simulation
        mesh = trimesh.load_mesh(self.stl_filename, process=False)
        mesh_vertices = mesh.vertices
        self.coral_faces = mesh.faces

        # Define the scaling factor (shrink by a factor of x)
        scaling_factor = 300.0

        # Scale down the vertices by the scaling factor
        mesh_vertices /= scaling_factor

        # Transform mesh points to align with grid
        mesh_vertices -= mesh_vertices.min(axis=0)
        mesh_extents = mesh_vertices.max(axis=0)
        length_phys_unit = mesh_extents.max()
        length_lbm_unit = self.grid_shape[0] / 4
        dx = length_phys_unit / length_lbm_unit
        mesh_vertices = mesh_vertices / dx

        # Shift mesh to align with the grid and move it to the center of the xy-plane
        center_shift_xy = np.array(
            [
                (self.grid_shape[0] - mesh_extents[0] / dx) / 2,  # Center along x-axis
                (self.grid_shape[1] - mesh_extents[1] / dx) / 2,  # Center along y-axis
                0.0,  # Keep the z-axis aligned for now (it will be shifted by shift_up later)
            ]
        )

        # Move the coral slightly up from the bottom boundary so it lines up with
        # the LBM grid when rendered.  This creates an anchor for the physics and
        # rendering domains.
        shift_up = 2.0
        anchor_shift = np.array([0.0, 0.0, shift_up])

        # Apply the shifts to the mesh vertices
        self.coral_vertices = mesh_vertices + center_shift_xy + anchor_shift

        # Convert the mesh to Warp arrays after positioning so physics and
        # rendering share the same coordinates
        self.verts = wp.array(np.array(self.coral_vertices, dtype=np.float32), dtype=wp.vec3f)
        self.faces = wp.array(np.array(self.coral_faces, dtype=np.int32), dtype=wp.vec3i)

        # Cross-sectional area for the coral mesh (just for boundary condition purposes)
        self.coral_cross_section = np.prod(mesh_extents[1:]) / dx**2

    def update_mesh(self, state: SimState) -> None:
        """Update Coral and boundry conditions."""
        state.coral.set_mesh(self.verts, self.faces)

    def setup_boundary_conditions(self) -> None:
        """Boundry conditions."""
        # Boundary conditions
        box = self.grid.bounding_box_indices()
        box_no_edge = self.grid.bounding_box_indices(remove_edges=True)

        inlet = box_no_edge["left"]
        outlet = box_no_edge["right"]
        walls = [box["bottom"][i] + box["top"][i] + box["front"][i] + box["back"][i] for i in range(self.velocity_set.d)]
        walls = np.unique(np.array(walls), axis=-1).tolist()

        bc_left = RegularizedBC("velocity", prescribed_value=(self.fluid_speed, 0.0, 0.0), indices=inlet)
        bc_walls = FullwayBounceBackBC(indices=walls)
        bc_do_nothing = ExtrapolationOutflowBC(indices=outlet)
        bc_coral = HalfwayBounceBackBC(mesh_vertices=self.coral_vertices)  # Adding the coral mesh as a BC

        self.boundary_conditions = [bc_walls, bc_left, bc_do_nothing, bc_coral]

    def save_coral_mesh(self) -> None:
        """Save the coral mesh to the output directory for visualization."""
        import pyvista as pv

        os.makedirs("./output", exist_ok=True)
        faces = np.hstack([np.full((self.coral_faces.shape[0], 1), 3, dtype=np.int32), self.coral_faces.astype(np.int32)]).ravel()
        mesh = pv.PolyData(self.coral_vertices, faces)
        mesh.save(os.path.join("./output", f"coral_mesh_step_{self.current_step}.vtk"))

    def save_vtk_fields(self, step) -> None:
        """Save simulation fields to VTK files for each timestep."""
        # Create pre-allocated fields
        rho_field = self.grid.create_field(cardinality=1)  # 3D density field (1 channel)
        u_field = self.grid.create_field(cardinality=self.velocity_set.d)  # 3D velocity field (3 channels)

        # Compute macroscopic quantities like density and velocity
        rho_field, u_field = self.macro(self.f_0, rho_field, u_field)
        u_field = u_field[:, 1:-1, 1:-1, 1:-1]
        rho_field = rho_field[:, 1:-1, 1:-1, 1:-1]
        # Convert Warp arrays to NumPy for saving
        rho_np = rho_field.numpy()[0].astype(np.float32)  # (nx, ny, nz)
        u_np = u_field.numpy().astype(np.float32)  # (3, nx, ny, nz)

        # Reorder velocity components to (nx, ny, nz, 3)
        u_np = np.moveaxis(u_np, 0, -1)

        # Compute pressure and velocity magnitude for visualization
        pressure_np = (rho_np - 1.0) / 3.0
        vel_mag_np = np.linalg.norm(u_np, axis=-1)

        # Prepare fields dictionary with scalar components
        fields = {
            "density": rho_np,
            "pressure": pressure_np.astype(np.float32),
            "velocity_x": u_np[..., 0],
            "velocity_y": u_np[..., 1],
            "velocity_z": u_np[..., 2],
            "velocity_magnitude": vel_mag_np.astype(np.float32),
        }

        # Save the fields as VTK files
        os.makedirs("./output", exist_ok=True)
        save_fields_vtk(fields, timestep=step, output_dir="./output", prefix="simulation")
        print(f"VTK files saved for timestep {step}")

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
        # time.sleep(1.0 / steps_per_second)  # Control real-time step rate
        state.velocity_field = self.get_field_numpy()["velocity"]

        if self.current_step % self.post_process_interval == 0:
            self.save_vtk_fields(self.current_step)
            self.save_coral_mesh()

        self.current_step += 1
