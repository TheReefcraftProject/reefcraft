# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Simple PORAG inpired growth model."""

import numpy as np
import warp as wp


class SimpleP:
    """Coral growth simulation with polyps evenly spaced on a hemisphere surface."""

    def __init__(
        self,
        grid_shape: tuple = (200, 200, 200),
        polyp_spacing: float = 0.00025,
        max_time_steps: int = 1000,
        resource_concentration: float = 1.0,
    ) -> None:
        """Initializes the SimpleP coral growth model with basic parameters and Warp for GPU acceleration.

        Parameters:
        - grid_shape: The size of the 3D grid (lattice).
        - polyp_spacing: The distance between adjacent polyps.
        - max_time_steps: Maximum number of simulation time steps.
        - resource_concentration: Initial resource concentration at the source nodes.
        """
        self.grid_shape = grid_shape
        self.polyp_spacing = polyp_spacing
        self.max_time_steps = max_time_steps
        self.resource_concentration = resource_concentration

        # Calculate the radius based on the polyp spacing
        self.radius = self.calculate_radius()

        # Initialize the grid and polyps on GPU
        self.grid = wp.array3d(grid_shape, dtype=float)  # Initialize grid with Warp (GPU)
        self.polyps = self.initialize_polyps()

        # Initialize the resource field with a gradient from resource_concentration to 0 on the floor level
        self.initialize_resource_field()

    def calculate_radius(self) -> float:
        """Calculates the radius of the hemisphere based on the polyp spacing."""
        num_polyps = 81  # Total polyps on the hemisphere
        surface_area_per_polyp = self.polyp_spacing**2  # Area occupied by each polyp

        # Total surface area covered by the polyps
        total_area = num_polyps * surface_area_per_polyp

        # Hemisphere surface area formula: 2πr^2 = total_area
        radius = np.sqrt(total_area / (2 * np.pi))

        return radius

    def initialize_polyps(self) -> list[tuple[int, int, int]]:
        """Initializes the polyps on the hemisphere mesh.

        Returns:
        - A list of polyp positions.
        """
        num_polyps = 81
        polyps = []

        # Golden angle for even distribution
        golden_angle = np.pi * (3.0 - np.sqrt(5.0))

        for i in range(num_polyps):
            # The polar angle (0 to pi/2 for hemisphere)
            phi = np.arccos(1 - 2 * (i + 0.5) / num_polyps)
            # The azimuthal angle (0 to 2*pi)
            theta = golden_angle * i

            # Convert spherical to Cartesian coordinates using the calculated radius
            x = self.radius * np.sin(phi) * np.cos(theta)
            y = self.radius * np.sin(phi) * np.sin(theta)
            z = self.radius * np.cos(phi)

            # Convert the float positions to grid-like integer positions
            ix = int(np.round(x / self.polyp_spacing))
            iy = int(np.round(y / self.polyp_spacing))
            iz = int(np.round(z / self.polyp_spacing))

            # Make sure the polyps stay within bounds of the grid
            if 0 <= ix < self.grid_shape[0] and 0 <= iy < self.grid_shape[1] and 0 <= iz < self.grid_shape[2]:
                polyps.append((ix, iy, iz))

        return polyps

    @wp.kernel
    def resource_gradient_kernel(field: wp.array3d(dtype=wp.float32), resource_concentration: float, grid_shape: wp.types.array(dtype=wp.types.int32)) -> None:
        """Kernel to initialize the resource field with a gradient from resource_concentration at the top to 0 at the floor."""
        i, j, k = wp.tid()  # Get the current thread's unique ID for the (x, y, z) coordinates

        # Get the z-coordinate from k
        top_z = wp.float32(grid_shape[2] - 1)  # Topmost z-coordinate (highest point in the grid)
        floor_z = wp.float32(0)  # Floor z-coordinate (lowest point in the grid)

        # Calculate the resource value based on the z-coordinate
        resource_value = resource_concentration * (wp.float32(1 - k) / (top_z - floor_z))

        # Set the value in the field
        field[i, j, k] = resource_value

    def initialize_resource_field(self) -> None:
        """Initializes the resource field with a gradient from resource_concentration at the top to 0 at the floor."""
        grid_shape = np.array(self.grid_shape, dtype=np.int32)

        # Launch the kernel with the 3D grid as input
        wp.launch(self.resource_gradient_kernel, dim=self.grid_shape, inputs=[self.grid, self.resource_concentration, grid_shape], device=wp.get_device())

        print("Resource field initialized with gradient.")


# Example usage
wp.init()
simple_p = SimpleP(polyp_spacing=0.00025)
print(f"Calculated radius: {simple_p.radius}")
