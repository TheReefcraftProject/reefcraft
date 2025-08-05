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
        sim_state: SimState,
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

        self.radius = self.calculate_radius()

        self.mesh = self.initialize_polyps()
        self.normals = wp.zeros((len(self.mesh["vertices"]),), dtype=wp.vec3f)

        self.launch_mesh_kernel()

        # Add our new coral to the simulation state
        self.coral_state = sim_state.add_coral()
        self.coral_state.set_mesh(self.mesh["vertices"], self.mesh["indices"])

    def calculate_radius(self) -> float:
        """Calculates the radius of the hemisphere based on the polyp spacing."""
        num_polyps = 81  # Total polyps on the hemisphere
        surface_area_per_polyp = self.polyp_spacing**2  # Area occupied by each polyp

        # Total surface area covered by the polyps
        total_area = num_polyps * surface_area_per_polyp

        radius = np.sqrt(total_area / (2 * np.pi))

        return radius

    def initialize_polyps(self) -> dict:
        """Initializes the polyps on the hemisphere mesh as a dictionary of Warp arrays.

        Returns:
        - A dictionary with 'vertices' (wp.array) and 'indices' (wp.array).
        """
        num_polyps = 81  # Total number of polyps (vertices)
        vertices = np.zeros((num_polyps, 3), dtype=np.float32)  # NumPy array for vertices

        # Golden angle for even distribution
        golden_angle = np.pi * (3.0 - np.sqrt(5.0))

        for i in range(num_polyps):
            # Polar angle adjusted for a hemisphere only
            phi = np.arccos(1 - (i + 0.5) / num_polyps)  # Polar angle in [0, pi/2] for hemisphere
            theta = golden_angle * i  # Azimuthal angle (0 to 2*pi)

            # Convert spherical to Cartesian coordinates
            x = self.radius * np.sin(phi) * np.cos(theta)
            y = self.radius * np.sin(phi) * np.sin(theta)
            z = self.radius * np.cos(phi)

            vertices[i] = [x, y, z]

        # Manually create indices for the hemisphere
        # Here we are creating triangles by connecting each vertex to the center and its neighbors
        indices = []

        # Add the base of the hemisphere (a circle at the bottom of the hemisphere)
        bottom_center = num_polyps - 1  # the last vertex is the center of the base
        for i in range(num_polyps - 1):
            indices.append([i, (i + 1) % (num_polyps - 1), bottom_center])

        # Create the upper hemisphere faces (a fan structure)
        for i in range(num_polyps - 1):
            # Create faces between adjacent points on the surface
            next_i = (i + 1) % (num_polyps - 1)  # next vertex in the list
            indices.append([i, next_i, num_polyps - 1])  # Connect the surface vertices to the center

        # Convert the vertices and indices to Warp arrays
        vertices_wp = wp.array(np.array(vertices, dtype=np.float32), dtype=wp.vec3f)
        indices_wp = wp.array(np.array(indices, dtype=np.int32), dtype=wp.vec3i)
        print(f"Type of indeces: {type(indices_wp)}")

        return {"vertices": vertices_wp, "indices": indices_wp}

    def update(self, state: SimState) -> None:
        """Update SimState mesh."""
        self.growth_step()
        self.coral_state.set_mesh(self.mesh.get("vertices"), self.mesh.get("indices"))

    def update_mesh(self, mesh_data: dict) -> None:
        """Update the mesh with a new set of polyps."""
        self.mesh = mesh_data

    @wp.kernel
    def calculate_normals_kernel(vertices: wp.array(dtype=wp.vec3f), normals: wp.array(dtype=wp.vec3f), n: int) -> None:
        """Kernel to calculate normals for each vertex based on the hemisphere structure."""
        idx = wp.tid()
        if idx < n:
            vertex = vertices[idx]
            normal = vertex / wp.length(vertex)
            normals[idx] = normal

    def launch_mesh_kernel(self) -> None:
        """Launch kernels to initialize mesh and compute normals."""
        num_polyps = len(self.mesh["vertices"])

        # Ensure the normals are initialized as wp.array with dtype wp.vec3f
        if self.normals is None:
            # Allocate normals array with the correct Warp type
            self.normals = wp.zeros(num_polyps, dtype=wp.vec3f)

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
            vertex = vertices[idx]
            normal = normals[idx]

            z_position = vertex[2]
            resource_at_polyp = resource_concentration * (z_position / z_max)

            # Compute the angle between the normal and the z-axis: THIS NEEDS UPDATE
            angle = wp.acos(wp.dot(normal, wp.vec3(0.0, 0.0, 1.0)) / wp.length(normal))
            angle_deg = wp.degrees(angle)

            # Scale the resource based on convexity
            scale = (360.0 - angle_deg) / 360.0

            # Calculate the final growth amount
            growth = resource_at_polyp * scale

            # Update the growth_amount (apply spacing for movement)
            growth_amount[idx] = growth * spacing

            # Update the polyp's position based on the growth amount and the normal direction
            vertices[idx] += normal * growth_amount[idx]

    def add_polyp(self, new_polyp: tuple) -> None:
        """Add a new polyp (vertex) to the list of polyps if space allows."""
        # Check if there’s space for the new polyp based on spacing
        vertices_np = self.mesh["vertices"].numpy()
        for vertex in vertices_np:
            if np.linalg.norm(vertex - np.array(new_polyp, dtype=np.float32)) < self.polyp_spacing:
                return

        # Add the new polyp
        new_vertices = np.concatenate([vertices_np, np.array([new_polyp], dtype=np.float32)], axis=0)
        new_idx = len(new_vertices) - 1

        indices_np = self.mesh["indices"].numpy()
        distances = np.linalg.norm(vertices_np - np.array(new_polyp, dtype=np.float32), axis=1)
        nearest = np.argsort(distances)[:3]
        new_tris = np.array(
            [
                [new_idx, nearest[0], nearest[1]],
                [new_idx, nearest[1], nearest[2]],
                [new_idx, nearest[2], nearest[0]],
            ],
            dtype=np.int32,
        )

        self.mesh["vertices"] = wp.array(new_vertices, dtype=wp.vec3f)
        self.mesh["indices"] = wp.array(np.concatenate([indices_np, new_tris]), dtype=wp.vec3)

        self.normals = wp.zeros(len(new_vertices), dtype=wp.vec3f)
        self.launch_mesh_kernel()

    def growth_step(self) -> None:
        """Update state by growing the polyps and updating the mesh."""
        vertices = self.mesh["vertices"]
        normals = self.normals

        # Create an array to store the growth amount for each polyp
        growth_amount = wp.zeros(len(vertices), dtype=wp.float32)

        # Launch the growth kernel to update the polyps
        wp.launch(
            self.growth_kernel,
            dim=len(vertices),
            inputs=[vertices, normals, growth_amount, self.polyp_spacing, len(vertices), self.resource_concentration, float(self.grid_shape[2])],
        )  # Pass resource concentration and z_max (grid size)

        wp.synchronize()
        verts_np = self.mesh["vertices"].numpy()
        indices_np = self.mesh["indices"].numpy()

        candidate = None
        max_gap = self.polyp_spacing

        for tri in indices_np:
            for i in range(3):
                vi = tri[i]
                vj = tri[(i + 1) % 3]
                dist = np.linalg.norm(verts_np[vi] - verts_np[vj])
                if dist > 2 * self.polyp_spacing and dist > max_gap:
                    max_gap = dist
                    candidate = (verts_np[vi] + verts_np[vj]) / 2.0

        if candidate is not None:
            self.add_polyp(tuple(candidate))
