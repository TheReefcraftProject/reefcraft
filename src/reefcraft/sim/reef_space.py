# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

import warp as wp
import numpy as np

"""
ReefSpace is the space acted on by ComputeLBM and coral growth models.

"""

class ReefSpace():
    def __init__(self, grid_size=(10, 10, 10), radius=1.0, center=wp.vec3(5.0, 5.0, 5.0)):
        self.grid_size = grid_size
        self.radius = radius
        self.center = center

        # Initialize a 3D field (grid) to store distance values
        self.field = wp.empty(shape=grid_size, dtype=wp.float32, device="cuda")

        # Initialize mesh (can be an array of vertices or some other structure)
        self.mesh = np.zeros((grid_size[0], grid_size[1], grid_size[2]))

        # Launch the kernel to create the 3D field and populate it with values (distance from the center)
        self.launch_kernel()

    @wp.kernel
    def make_field(self, field: wp.array3d(dtype=float), center: wp.vec3, radius: float):
        for i, j, k in field:
            p = wp.vec3(float(i), float(j), float(k))
            d = wp.length(p - center) - radius
            field[i, j, k] = d

    def update_mesh(self, new_mesh: np.ndarray):
        # This function updates the mesh (could be used to update particle positions, etc.)
        self.mesh = new_mesh

    def get_field(self):
        # Retrieve the current state of the grid
        return self.field

    def get_mesh(self):
        # Retrieve the current mesh
        return self.mesh

    def launch_kernel(self):
        # Launch the kernel for field creation
        wp.launch(kernel=self.make_field,  # kernel to launch
                  dim=self.grid_size[0] * self.grid_size[1] * self.grid_size[2],  # number of threads (should be number of grid points)
                  inputs=[self.field, self.center, self.radius],  # pass the required arguments (field, center, radius)
                  device="cuda")  # CUDA device


# Example usage:
space = ReefSpace(grid_size=(10, 10, 10), radius=1.0, center=wp.vec3(5.0, 5.0, 5.0))

# Now you can update the field or mesh as needed
new_mesh = np.random.rand(10, 10, 10)  # Example of updating mesh
space.update_mesh(new_mesh)

# Access field and mesh
field_data = space.get_field()
mesh_data = space.get_mesh()
