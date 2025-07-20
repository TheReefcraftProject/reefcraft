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

class ComputeLBM:
    def __init__(self):
        self.grid_shape = (64,64,64)
        self.fluid_speed = 1.0 
        self.current_step = 0

        self.Re = 50000.0
        self.clength = self.grid_shape[0] - 1
        self.visc = self.fluid_speed * self.clength / self.Re
        self.omega = 1.0 / (3.0 * self.visc + 0.5)

        self.compute_backend = ComputeBackend.WARP
        self.precision_policy = PrecisionPolicy.FP32FP32

        self.velocity_set = xlb.velocity_set.D3Q27(precision_policy=self.precision_policy, backend=self.compute_backend)
        xlb.init(velocity_set=self.velocity_set, default_backend=self.compute_backend, default_precision_policy=self.precision_policy)
        self.grid = grid_factory(self.grid_shape, compute_backend=self.compute_backend)

        self.setup_boundary_conditions()

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

    def update_mesh(self, mesh_data: dict):
        # Extract the mesh vertices, faces, and normals from the dictionary
        self.coral_vertices = mesh_data["verts"]  # Warp array of vertices
        self.coral_faces = mesh_data["faces"]  # Warp array of faces
        self.coral_normals = mesh_data.get("norms", None)  # Optionally get normals if available

        # Process the mesh vertices (transform to the grid space)
        mesh_extents = self.coral_vertices.max(axis=0) - self.coral_vertices.min(axis=0)
        length_phys_unit = mesh_extents.max()
        length_lbm_unit = self.grid_shape[0] / 4
        dx = length_phys_unit / length_lbm_unit
        self.coral_vertices = self.coral_vertices / dx

        # Shift mesh to align with the grid
        shift = np.array([self.grid_shape[0] / 4, (self.grid_shape[1] - mesh_extents[1] / dx) / 2, 0.0])
        self.coral_vertices += shift

        # Calculate the cross-sectional area for the coral mesh (just for boundary condition purposes)
        self.coral_cross_section = np.prod(mesh_extents[1:]) / dx**2

        # Update the boundary condition for the coral mesh
        self.bc_coral = HalfwayBounceBackBC(mesh_vertices=self.coral_vertices)
        self.boundary_conditions.append(self.bc_coral)

    def setup_boundary_conditions(self):
        box = self.grid.bounding_box_indices()
        box_no_edge = self.grid.bounding_box_indices(remove_edges=True)

        inlet = box_no_edge["left"]
        outlet = box_no_edge["right"]
        walls = [box["bottom"][i] + box["top"][i] + box["front"][i] + box["back"][i] for i in range(self.velocity_set.d)]
        walls = np.unique(np.array(walls), axis=-1).tolist()

        bc_left = RegularizedBC("velocity", prescribed_value=(self.fluid_speed, 0.0, 0.0), indices=inlet)
        bc_walls = FullwayBounceBackBC(indices=walls)
        bc_do_nothing = ExtrapolationOutflowBC(indices=outlet)

        self.boundary_conditions = [bc_walls, bc_left, bc_do_nothing]

    def get_field_numpy(self) -> dict:
        rho_field = self.grid.create_field(cardinality=1)
        u_field = self.grid.create_field(cardinality=self.velocity_set.d)

        rho_field, u_field = self.macro(self.f_0, rho_field, u_field)

        rho_np = rho_field.numpy()[0].astype(np.float32)
        u_np = u_field.numpy().astype(np.float32)

        u_np = np.moveaxis(u_np, 0, -1)

        coral_mesh_np = self.get_coral_mesh_field()

        pressure_np = (rho_np - 1.0) / 3.0
        vel_mag_np = np.linalg.norm(u_np, axis=-1)

        fields = {
            "density": rho_np,
            "pressure": pressure_np.astype(np.float32),
            "velocity": u_np,
            "velocity_magnitude": vel_mag_np.astype(np.float32),
            "coral_mesh": coral_mesh_np,
        }

        return fields

    def get_coral_mesh_field(self):
        coral_mesh_field = np.zeros(self.grid_shape, dtype=np.float32)
        for i in range(self.coral_vertices.shape[0]):
            x, y, z = self.coral_vertices[i]
            ix = int(np.round(x))
            iy = int(np.round(y))
            iz = int(np.round(z))

            if 0 <= ix < self.grid_shape[0] and 0 <= iy < self.grid_shape[1] and 0 <= iz < self.grid_shape[2]:
                coral_mesh_field[ix, iy, iz] = 1

        return coral_mesh_field


    def step(self, mesh_data: dict) -> None:

        self.f_0, self.f_1 = self.stepper(self.f_0, self.f_1, self.bc_mask, self.missing_mask, self.current_step)
        self.f_0, self.f_1 = self.f_1, self.f_0
        self.current_step += 1
        self.update_mesh(mesh_data=mesh_data)
        #time.sleep(1.0 / steps_per_second)  # Control real-time step rate
        
