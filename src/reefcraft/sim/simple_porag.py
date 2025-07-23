# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Simple PORAG inpired growth model."""

import numpy as np
import warp as wp

from reefcraft.sim.state import SimState


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

        # Initialize polyps as floating-point 3D coordinates
        self.polyps = self.initialize_polyps()

    def calculate_radius(self) -> float:
        """Calculates the radius of the hemisphere based on the polyp spacing."""
        num_polyps = 81  # Total polyps on the hemisphere
        surface_area_per_polyp = self.polyp_spacing**2  # Area occupied by each polyp

        # Total surface area covered by the polyps
        total_area = num_polyps * surface_area_per_polyp

        # Hemisphere surface area formula: 2πr^2 = total_area
        radius = np.sqrt(total_area / (2 * np.pi))

        return radius

    def initialize_polyps(self) -> dict:
        """Initializes the polyps on the hemisphere mesh as a dictionary of Warp arrays.

        Returns:
        - A dictionary with 'vertices' (wp.array) and 'indices' (wp.array).
        """
        num_polyps = 81
        vertices = np.zeros((num_polyps, 3), dtype=np.float32)  # NumPy array for vertices
        indices = np.arange(num_polyps, dtype=np.int32)  # Indices array (simple example)

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

            # Store the polyp positions in the vertices array
            vertices[i] = [x, y, z]

        # Convert the vertices and indices to Warp arrays
        vertices_wp = wp.array(vertices, dtype=wp.vec3, device="cuda")
        indices_wp = wp.array(indices, dtype=wp.int32, device="cuda")

        return {"vertices": vertices_wp, "indices": indices_wp}

    def update(self, state: SimState) -> None:
        """Update state."""
        state.coral.set_mesh(self.polyps.get("vertices"), self.polyps.get("indices"))

    def growth_function(self, polyp: tuple) -> float:
        """Compute growth amount based on resource concentration and polyp's z-coordinate."""
        # Example: Linear resource gradient based on z-coordinate (top has most resources)
        z_position = polyp[2]
        resource_at_polyp = self.resource_concentration * (z_position / self.radius)
        return resource_at_polyp

    def add_polyp(self, new_polyp: tuple) -> None:
        """Add a new polyp (vertex) to the list of polyps."""
        pass
