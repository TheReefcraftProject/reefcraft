# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------
import os
import time
import numpy as np
import matplotlib.pyplot as plt
from xlb.compute_backend import ComputeBackend
from xlb.precision_policy import PrecisionPolicy
from xlb.grid import grid_factory
from xlb.operator.stepper import IncompressibleNavierStokesStepper
from xlb.operator.boundary_condition import RegularizedBC, ExtrapolationOutflowBC, FullwayBounceBackBC, HalfwayBounceBackBC
import xlb.velocity_set
import jax.numpy as jnp
from xlb.operator.macroscopic import Macroscopic
from xlb.utils import save_image, save_fields_vtk  
import trimesh 

"""
Here we define a LBM class that utilizes XLB to handle computations of fluid fields.

Purpose: An instance of this will be utilized to compute and return the state of fields (e.g. velcity, 
pressure, chemical concentrations) for use in simulating water.

"""
# ----- LBM Class ----- #
class ComputeLBM:
    """
    A class to simulate fluid dynamics using Lattice Boltzmann Method (LBM).
    
    Attributes:
        grid_shape (tuple): The shape of the grid (x, y, z).
        num_steps (int): The number of simulation steps to run.
        fluid_speed (float): The fluid's speed, used to calculate viscosity.
        stl_filename (str): Path to the STL file representing the mesh for boundary conditions.
        post_process_interval (int): The interval at which post-processing (e.g., saving fields) occurs.
        visc (float): The viscosity of the fluid, calculated based on fluid_speed and Reynolds number.
        omega (float): The relaxation factor for the LBM, calculated from viscosity.
    """
    def __init__(self, grid_shape, num_steps, fluid_speed, stl_filename, post_process_interval):
        # Grid parameters
        self.grid_shape = grid_shape
        self.num_steps = num_steps
        self.fluid_speed = fluid_speed
        self.stl_filename = stl_filename
        self.post_process_interval = post_process_interval
        self.visc = 1

        # Physical Parameters
        self.Re = 50000.0
        self.clength = grid_shape[0] - 1
        self.visc = fluid_speed * self.clength / self.Re  # viscosity based on fluid speed and Reynolds number
        self.omega = 1.0 / (3.0 * self.visc + 0.5)  # Relaxation factor for LBM

        # Simulation Configuration
        self.compute_backend = ComputeBackend.WARP
        self.precision_policy = PrecisionPolicy.FP32FP32

        # Setup XLB and grid
        self.velocity_set = xlb.velocity_set.D3Q27(precision_policy=self.precision_policy, backend=self.compute_backend)
        xlb.init(velocity_set=self.velocity_set, default_backend=self.compute_backend, default_precision_policy=self.precision_policy)
        self.grid = grid_factory(self.grid_shape, compute_backend=self.compute_backend)

        # Load the mesh
        self.load_mesh()

        # Save coral mesh for visualization
        self.save_coral_mesh()

        # Boundary conditions
        self.setup_boundary_conditions()

        # Stepper and macroscopic operator setup
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

        # Prepare fields for simulation
        self.f_0, self.f_1, self.bc_mask, self.missing_mask = self.stepper.prepare_fields()

    def load_mesh(self):
        # Load and process mesh for the simulation
        mesh = trimesh.load_mesh(self.stl_filename, process=False)
        mesh_vertices = mesh.vertices
        self.coral_faces = mesh.faces

        # Transform mesh points to align with grid
        mesh_vertices -= mesh_vertices.min(axis=0)
        mesh_extents = mesh_vertices.max(axis=0)
        length_phys_unit = mesh_extents.max()
        length_lbm_unit = self.grid_shape[0] / 4
        dx = length_phys_unit / length_lbm_unit
        mesh_vertices = mesh_vertices / dx
        shift = np.array([self.grid_shape[0] / 4, (self.grid_shape[1] - mesh_extents[1] / dx) / 2, 0.0])
        self.coral_vertices = mesh_vertices + shift

        # Cross-sectional area for the coral mesh (just for boundary condition purposes)
        self.coral_cross_section = np.prod(mesh_extents[1:]) / dx**2

    def save_coral_mesh(self):
        """Save the coral mesh to the output directory for visualization."""
        import pyvista as pv
        os.makedirs("./output", exist_ok=True)
        faces = np.hstack(
            [np.full((self.coral_faces.shape[0], 1), 3, dtype=np.int32), self.coral_faces.astype(np.int32)]
        ).ravel()
        mesh = pv.PolyData(self.coral_vertices, faces)
        mesh.save(os.path.join("./output", "coral_mesh.vtk"))

    def setup_boundary_conditions(self):
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

    def save_vtk_fields(self, step):
        """
        Save simulation fields to VTK files for each timestep.
        """
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
    
    def get_field_numpy(self):
        """
        Returns velocity, density, and fields as dictionary of numpy arrays.
        returns keys:
            "density"
            "pressure"
            "velocity"
            "velocity_magnitude"
        """
         # Create pre-allocated fields
        rho_field = self.grid.create_field(cardinality=1)  # 3D density field (1 channel)
        u_field = self.grid.create_field(cardinality=self.velocity_set.d)  # 3D velocity field (3 channels)

        # Compute macroscopic quantities (density and velocity)
        rho_field, u_field = self.macro(self.f_0, rho_field, u_field)
        
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
            "velocity": u_np,
            "velocity_magnitude": vel_mag_np.astype(np.float32),
        } 
        return fields

    def run_vtk(self):
        """
        Run the simulation loop with saving VTK.
        """
        start_time = time.time()
        for step in range(self.num_steps):
            # Call stepper with the correct arguments
            self.f_0, self.f_1 = self.stepper(self.f_0, self.f_1, self.bc_mask, self.missing_mask, step)

            # Swap the buffers
            self.f_0, self.f_1 = self.f_1, self.f_0

            # Save VTK files at the specified intervals
            if step % self.post_process_interval == 0 or step == self.num_steps - 1:
                    self.save_vtk_fields(step)

            # Print progress at intervals
            if step % 100 == 0:
                elapsed_time = time.time() - start_time
                print(f"Iteration: {step}/{self.num_steps} | Time elapsed: {elapsed_time:.2f}s")
                start_time = time.time()

        print("Simulation completed successfully.")

    def run_step(self, step):
        """
        Run one iteration, return fields as numpy arrays (uses get_field_numpy())
        """

        step = step

        self.f_0, self.f_1 = self.stepper(self.f_0, self.f_1, self.bc_mask, self.missing_mask, step)

        # Swap the buffers
        self.f_0, self.f_1 = self.f_1, self.f_0

        return self.get_field_numpy()
    
    def run(self):
        """
        Run the simulation loop.
        """
        start_time = time.time()
        for step in range(self.num_steps):
            # Call stepper with the correct arguments
            self.f_0, self.f_1 = self.stepper(self.f_0, self.f_1, self.bc_mask, self.missing_mask, step)

            # Swap the buffers
            self.f_0, self.f_1 = self.f_1, self.f_0


            # Print progress at intervals
            if step % 100 == 0:
                elapsed_time = time.time() - start_time
                print(f"Iteration: {step}/{self.num_steps} | Time elapsed: {elapsed_time:.2f}s")
                start_time = time.time()

        print("Simulation completed successfully.")

