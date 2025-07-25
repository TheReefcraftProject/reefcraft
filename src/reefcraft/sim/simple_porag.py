# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Simple PORAG inpired growth model."""

import numpy as np
import warp as wp
from scipy.spatial import ConvexHull

from reefcraft.sim.state import SimState


class SimpleP:
    """Coral growth simulation with polyps evenly spaced on a hemisphere surface."""

    def __init__(
        self,
        grid_shape: tuple = (200, 200, 200),
        polyp_spacing: float = 0.1,
        max_time_steps: int = 1000,
        resource_concentration: float = 1.0,
    ) -> None:
        """Initializes the SimpleP coral growth model with basic parameters and Warp for GPU acceleration."""
        self.grid_shape = grid_shape
        self.polyp_spacing = polyp_spacing
        self.max_time_steps = max_time_steps
        self.resource_concentration = resource_concentration

        # Calculate the radius based on the polyp spacing
        self.radius = self.calculate_radius()

        # Initialize polyps as a dictionary with Warp arrays for vertices and indices
        self.mesh = self.initialize_polyps()

        # Initialize normals as a Warp array
        self.normals = wp.zeros((len(self.mesh["vertices"]),), dtype=wp.vec3f, device="cuda")

        # Launch kernel to initialize mesh and normals
        self.launch_mesh_kernel()

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
            # The polar angle adjusted for a hemisphere only
            phi = np.arccos(1 - (i + 0.5) / num_polyps)  # Polar angle in [0, pi/2] for hemisphere
            theta = golden_angle * i  # Azimuthal angle (0 to 2*pi)

            # Convert spherical to Cartesian coordinates using the calculated radius
            x = self.radius * np.sin(phi) * np.cos(theta)
            y = self.radius * np.sin(phi) * np.sin(theta)
            z = self.radius * np.cos(phi)

            # Store the polyp positions in the vertices array
            vertices[i] = [x, y, z]

        # Use a convex hull to connect neighboring vertices into a hemisphere shell
        hull = ConvexHull(vertices)
        indices = hull.simplices.astype(np.int32)

        # Convert the vertices and indices to Warp arrays on CUDA as requested
        vertices_wp = wp.array(vertices, dtype=wp.vec3f, device="cuda")
        indices_wp = wp.array(indices, dtype=wp.vec3i, device="cuda")

        return {"vertices": vertices_wp, "indices": indices_wp}

    def update(self, state: SimState) -> None:
        """Update SimState mesh."""
        self.growth_step()
        state.coral.set_mesh(self.mesh.get("vertices"), self.mesh.get("indices"))

    def update_mesh(self, mesh_data: dict) -> None:
        """Update the mesh with a new set of polyps."""
        self.mesh = mesh_data

    @wp.kernel
    def calculate_normals_kernel(vertices: wp.array(dtype=wp.vec3f), normals: wp.array(dtype=wp.vec3f), n: int) -> None:
        """Kernel to calculate normals for each vertex based on the hemisphere structure."""
        idx = wp.tid()
        if idx < n:
            vertex = vertices[idx]
            normal = vertex / wp.length(vertex)  # Normalize the vector from the origin
            normals[idx] = normal

    def launch_mesh_kernel(self) -> None:
        """Launch kernels to initialize mesh and compute normals."""
        num_polyps = len(self.mesh["vertices"])

        # Ensure the normals are initialized as wp.array with dtype wp.vec3f
        if self.normals is None:
            # Allocate normals array with the correct Warp type
            self.normals = wp.zeros(num_polyps, dtype=wp.vec3f, device="cuda")

        # Launch the kernel to calculate normals
        wp.launch(self.calculate_normals_kernel, dim=num_polyps, inputs=[self.mesh["vertices"], self.normals, num_polyps])

    @wp.kernel
    def growth_kernel(
        vertices: wp.array(dtype=wp.vec3f),
        normals: wp.array(dtype=wp.vec3f),
        growth_amount: wp.array(dtype=wp.float32),
        spacing: float,
        n: int,
        resource_concentration: float,
        z_max: float,
    ) -> None:
        """Kernel to update polyp positions based on growth and normal vectors."""
        idx = wp.tid()
        if idx < n:
            # Get the vertex and normal for the current vertex
            vertex = vertices[idx]
            normal = normals[idx]

            # Compute growth amount based on resource concentration and polyp's z-coordinate
            z_position = vertex[2]
            resource_at_polyp = resource_concentration * (z_position / z_max)

            # Compute the angle between the normal and the z-axis
            angle = wp.acos(wp.dot(normal, wp.vec3(0.0, 0.0, 1.0)) / wp.length(normal))
            angle_deg = wp.degrees(angle)  # Convert the angle from radians to degrees

            # Scale the resource based on convexity
            scale = (360.0 - angle_deg) / 360.0  # Convex = more resources

            # Calculate the final growth amount
            growth = resource_at_polyp * scale

            # Update the growth_amount (apply spacing for movement)
            growth_amount[idx] = growth * spacing

            # Update the polyp's position based on the growth amount and the normal direction
            vertices[idx] += normal * growth_amount[idx]

    def add_polyp(self, new_polyp: tuple) -> None:
        """Add a new polyp (vertex) to the list of polyps if space allows."""
        # Check if there’s space for the new polyp based on spacing
        for vertex in self.mesh["vertices"]:
            distance = np.linalg.norm(vertex - np.array(new_polyp))
            if distance < self.polyp_spacing:
                # No space for this polyp, return
                return

        # If there's space, add the new polyp
        new_vertex_wp = wp.array([new_polyp], dtype=wp.vec3f, device="cuda")
        self.mesh["vertices"] = wp.concatenate([self.mesh["vertices"], new_vertex_wp])
        # Recalculate normals for the new mesh including the added polyp
        self.launch_mesh_kernel()

    def growth_step(self) -> None:
        """Update state by growing the polyps and updating the mesh."""
        # Retrieve the mesh vertices and normals
        vertices = self.mesh["vertices"]
        normals = self.normals

        # Create an array to store the growth amount for each polyp
        growth_amount = wp.zeros(len(vertices), dtype=wp.float32, device="cuda")

        # Launch the growth kernel to update the polyps
        wp.launch(
            self.growth_kernel,
            dim=len(vertices),
            inputs=[vertices, normals, growth_amount, self.polyp_spacing, len(vertices), self.resource_concentration, float(self.grid_shape[2])],
        )  # Pass resource concentration and z_max (grid size)

        # Check if space is available to add a new polyp
        new_polyp = (
            np.random.uniform(-self.radius, self.radius),
            np.random.uniform(-self.radius, self.radius),
            np.random.uniform(0, self.radius),
        )  # Random position within the hemisphere

        # Add the new polyp if there's space
        self.add_polyp(new_polyp)
