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
from xlb.utils import save_fields_vtk

from reefcraft.sim.cube import Cube


class LBM:
    """Compute water states with LBM."""

    def __init__(self, grid_shape: tuple, fluid_speed: float, Re: float, process_interval: int, mesh_data: tuple[wp.array, wp.array]) -> None:
        """Initialize ComputeLBM fields and data."""
        self.grid_shape = grid_shape
        self.fluid_speed = fluid_speed
        self.current_step = 0
        self.coral_vertices = mesh_data[0]
        self.coral_indices = mesh_data[1]
        self.boundary_conditions = []
        self.Re = Re
        self.clength = self.grid_shape[0] - 1
        self.visc = self.fluid_speed * self.clength / self.Re
        self.omega = 0.5

        self.compute_backend = ComputeBackend.WARP
        self.precision_policy = PrecisionPolicy.FP32FP32

        self.velocity_set = xlb.velocity_set.D3Q27(precision_policy=self.precision_policy, backend=self.compute_backend)
        xlb.init(velocity_set=self.velocity_set, default_backend=self.compute_backend, default_precision_policy=self.precision_policy)
        self.grid = grid_factory(self.grid_shape, compute_backend=self.compute_backend)

        # Add mesh to scene
        self.load_mesh(mesh_data=mesh_data, move=False)

        # Add boundary Conditions
        self.setup_boundary_conditions()

        # Initialize stepper and macro functions
        self.stepper = IncompressibleNavierStokesStepper(
            omega=self.omega,
            grid=self.grid,
            boundary_conditions=self.boundary_conditions,
            collision_type="KBC",
        )
        self.macro = Macroscopic(
            compute_backend=self.compute_backend,
            precision_policy=self.precision_policy,
            velocity_set=self.velocity_set,
        )

        self.f_0, self.f_1, self.bc_mask, self.missing_mask = self.stepper.prepare_fields()

    def load_mesh(self, mesh_data: tuple[wp.array, wp.array], move: bool) -> None:
        """Update Coral and boundary conditions."""
        # Extract the vertices and indices from the mesh_data tuple

        # Shift mesh to center as is:
        if move:
            # Convert warp's Vec3f to NumPy array for vertices
            self.coral_vertices = mesh_data[0].numpy()  # (Nx3) array of vertices

            # Convert indices to NumPy array (typically an (Mx3) array of integer indices)
            self.coral_indices = mesh_data[1].numpy()  # (Mx3) array of indices

            # Shift to xy plane center - from 0,0,0 center
            shift = np.array([self.grid_shape[0] / 2, self.grid_shape[1] / 2, 0.0])

            # Apply the shift to the vertices
            self.coral_vertices = self.coral_vertices + shift

            # Now, create the Trimesh object
            coral_mesh = trimesh.Trimesh(vertices=self.coral_vertices, faces=self.coral_indices)

            self.coral_vertices = coral_mesh.vertices
            self.coral_indices = coral_mesh.faces

        else:
            self.coral_vertices = mesh_data[0]
            self.coral_indices = mesh_data[1]

    def setup_boundary_conditions(self) -> None:
        """Boundary conditions for the simulation."""
        box_no_edge = self.grid.bounding_box_indices(remove_edges=True)

        inlet = box_no_edge["left"]
        outlet = box_no_edge["right"]
        walls = [box_no_edge["bottom"][i] + box_no_edge["top"][i] + box_no_edge["front"][i] + box_no_edge["back"][i] for i in range(self.velocity_set.d)]
        walls = np.unique(np.array(walls), axis=-1).tolist()

        bc_left = RegularizedBC("velocity", prescribed_value=(self.fluid_speed, 0.0, 0.0), indices=inlet)
        bc_walls = FullwayBounceBackBC(indices=walls)
        bc_do_nothing = ExtrapolationOutflowBC(indices=outlet)

        bc_coral = FullwayBounceBackBC(
            velocity_set=self.velocity_set,
            precision_policy=self.precision_policy,
            compute_backend=self.compute_backend,
            mesh_vertices=self.coral_vertices,
        )
        self.boundary_conditions = [bc_coral, bc_walls, bc_left, bc_do_nothing]

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

    def save_coral_vtk(self) -> None:
        """Save coral mesh once as a custom VTK field using save_fields_vtk."""
        import pyvista as pv

        os.makedirs("./output", exist_ok=True)
        faces = np.hstack([np.full((self.coral_indices.shape[0], 1), 3, dtype=np.int32), self.coral_indices.astype(np.int32)]).ravel()
        mesh = pv.PolyData(self.coral_vertices, faces)
        mesh.save(os.path.join("./output", "coral_mesh.vtk"))

    def save_vtk_fields(self) -> None:
        """Save simulation fields to VTK files."""
        # Create pre-allocated fields for density, velocity, and custom coral field
        rho_field = self.grid.create_field(cardinality=1)  # 3D density field (1 channel)
        u_field = self.grid.create_field(cardinality=self.velocity_set.d)  # 3D velocity field (3 channels)

        # Compute macroscopic quantities like density and velocity
        rho_field, u_field = self.macro(self.f_0, rho_field, u_field)

        # Convert Warp arrays to NumPy for saving
        rho_np = rho_field.numpy()[0].astype(np.float32)  # (nx, ny, nz)
        u_np = u_field.numpy().astype(np.float32)  # (3, nx, ny, nz)

        # Reorder velocity components to (nx, ny, nz, 3)
        u_np = np.moveaxis(u_np, 0, -1)

        # Compute pressure and velocity magnitude for visualization
        pressure_np = (rho_np - 1.0) / 3.0
        vel_mag_np = np.linalg.norm(u_np, axis=-1)

        # Prepare fields dictionary, including velocity components and the coral field
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
        save_fields_vtk(fields, timestep=self.current_step, output_dir="./output", prefix="simulation")

    def step(self, save_vtk: bool) -> None:
        """Run one iteration of LBM."""
        self.f_0, self.f_1 = self.stepper(self.f_0, self.f_1, self.bc_mask, self.missing_mask, self.current_step)
        self.f_0, self.f_1 = self.f_1, self.f_0
        self.current_step += 1

        if save_vtk and (num_steps % process_interval == 0):
            self.save_vtk_fields()


# ---------------------------------------------------
# Run a LBM water flow over coral save fields as VTK:
# ---------------------------------------------------

# Define Parameters
grid_shape = (50, 50, 50)
fluid_speed = 3.0
Re = 3500.0
process_interval = 100
num_steps = 3000

# Load STL mesh or coral mesh
cube_coral = Cube(side_len=10)
cube_mesh = (cube_coral.vertices, cube_coral.indices)

# Load and process stl mesh
stl_mesh = trimesh.load_mesh("../resources/models/coral.stl", process=False)
mesh_vertices = stl_mesh.vertices

# Transform stl mesh points to align with grid
mesh_vertices -= mesh_vertices.min(axis=0)
mesh_extents = mesh_vertices.max(axis=0)
length_phys_unit = mesh_extents.max()
length_lbm_unit = grid_shape[0] / 4
dx = length_phys_unit / length_lbm_unit
mesh_vertices = mesh_vertices / dx
shift = np.array([grid_shape[0] / 4, (grid_shape[1] - mesh_extents[1] / dx) / 2, 0.0])
coral_vertices = mesh_vertices + shift
coral_indices = stl_mesh.faces

# Set up simulation - initialize LBM:
lbm_sim = LBM(grid_shape=grid_shape, fluid_speed=fluid_speed, Re=Re, process_interval=process_interval, mesh_data=(coral_vertices, coral_indices))

# Save coral as stl for paraview visual
lbm_sim.save_coral_vtk()

# Run simulation:
for i in range(num_steps):
    lbm_sim.step(save_vtk=True)  # save fields as vtk at process interval
