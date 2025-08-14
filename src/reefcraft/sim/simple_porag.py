# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Simple PORAG inspired growth model using :mod:`trimesh` for mesh handling."""

from __future__ import annotations

import numpy as np
import trimesh
import warp as wp

from reefcraft.sim.state import SimState


class SimpleP:
    """Coral growth simulation with polyps evenly spaced on a hemisphere surface.

    The mesh is managed internally with :class:`trimesh.Trimesh` for convenient
    geometric queries while Warp arrays are maintained for GPU kernels and for
    passing data to other parts of the simulation.
    """

    def __init__(
        self,
        sim_state: SimState,
        grid_shape: tuple[int, int, int] = (200, 200, 200),
        polyp_spacing: float = 0.5,
        max_time_steps: int = 1000,
        resource_concentration: float = 1.0,
    ) -> None:
        """Initialize the SimpleP coral growth model."""

        self.grid_shape = grid_shape
        self.polyp_spacing = polyp_spacing
        self.max_time_steps = max_time_steps
        self.resource_concentration = resource_concentration

        self.radius = self.calculate_radius()

        self.mesh = self.initialize_polyps()
        self.update_wp_arrays()

        # Add our new coral to the simulation state
        self.coral_state = sim_state.add_coral()
        self.coral_state.set_mesh(self.verts_wp, self.indices_wp)

    def calculate_radius(self) -> float:
        """Calculate the radius of the hemisphere based on the polyp spacing."""

        num_polyps = 81  # Total polyps on the hemisphere
        surface_area_per_polyp = self.polyp_spacing**2
        total_area = num_polyps * surface_area_per_polyp
        radius = np.sqrt(total_area / (2 * np.pi))
        return float(radius)

    def initialize_polyps(self) -> trimesh.Trimesh:
        """Initialise a hemispherical distribution of polyps as a mesh."""

        num_polyps = 81
        vertices = np.zeros((num_polyps, 3), dtype=np.float32)

        golden_angle = np.pi * (3.0 - np.sqrt(5.0))
        for i in range(num_polyps):
            phi = np.arccos(1 - (i + 0.5) / num_polyps)  # hemisphere polar angle
            theta = golden_angle * i
            x = self.radius * np.sin(phi) * np.cos(theta)
            y = self.radius * np.sin(phi) * np.sin(theta)
            z = self.radius * np.cos(phi)
            vertices[i] = [x, y, z]

        # Construct indices by connecting neighbouring points and a base centre
        indices: list[list[int]] = []
        bottom_center = num_polyps - 1
        for i in range(num_polyps - 1):
            indices.append([i, (i + 1) % (num_polyps - 1), bottom_center])
        for i in range(num_polyps - 1):
            next_i = (i + 1) % (num_polyps - 1)
            indices.append([i, next_i, bottom_center])

        return trimesh.Trimesh(vertices=vertices, faces=np.array(indices, dtype=np.int32), process=False)

    # ------------------------------------------------------------------
    # Mesh/Warp array helpers
    # ------------------------------------------------------------------
    def update_wp_arrays(self) -> None:
        """Update Warp arrays for vertices, indices and normals from the mesh."""

        verts_np = self.mesh.vertices.astype(np.float32)
        faces_np = self.mesh.faces.astype(np.int32)
        normals_np = self.mesh.vertex_normals.astype(np.float32)

        self.verts_wp = wp.array(verts_np, dtype=wp.vec3f)
        self.indices_wp = wp.array(faces_np, dtype=wp.vec3i)
        self.normals_wp = wp.array(normals_np, dtype=wp.vec3f)

    # ------------------------------------------------------------------
    # Simulation update interface
    # ------------------------------------------------------------------
    def update(self, state: SimState) -> None:  # noqa: D401 - Short docstring
        """Update the SimState mesh."""

        self.growth_step()
        self.coral_state.set_mesh(self.verts_wp, self.indices_wp)

    # ------------------------------------------------------------------
    # Growth logic
    # ------------------------------------------------------------------
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

            angle = wp.acos(wp.dot(normal, wp.vec3(0.0, 0.0, 1.0)) / wp.length(normal))
            angle_deg = wp.degrees(angle)

            scale = (360.0 - angle_deg) / 360.0
            growth = resource_at_polyp * scale

            growth_amount[idx] = growth * spacing
            vertices[idx] += normal * growth_amount[idx]

    def add_polyp(self, new_polyp: np.ndarray) -> None:
        """Add a new polyp (vertex) to the mesh if spacing permits."""

        if np.any(np.linalg.norm(self.mesh.vertices - new_polyp, axis=1) < self.polyp_spacing):
            return

        verts = np.vstack([self.mesh.vertices, new_polyp]).astype(np.float32)
        new_idx = len(verts) - 1

        distances = np.linalg.norm(verts[:-1] - new_polyp, axis=1)
        nearest = np.argsort(distances)[:3]
        new_tris = np.array(
            [
                [new_idx, nearest[0], nearest[1]],
                [new_idx, nearest[1], nearest[2]],
                [new_idx, nearest[2], nearest[0]],
            ],
            dtype=np.int32,
        )

        faces = np.vstack([self.mesh.faces, new_tris]).astype(np.int32)
        self.mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
        self.update_wp_arrays()

    def growth_step(self) -> None:
        """Update state by growing the polyps and updating the mesh."""

        growth_amount = wp.zeros(len(self.verts_wp), dtype=wp.float32)
        wp.launch(
            self.growth_kernel,
            dim=len(self.verts_wp),
            inputs=[
                self.verts_wp,
                self.normals_wp,
                growth_amount,
                self.polyp_spacing,
                len(self.verts_wp),
                self.resource_concentration,
                float(self.grid_shape[2]),
            ],
        )
        wp.synchronize()

        # Update the mesh from the Warp vertex array
        self.mesh.vertices[:] = self.verts_wp.numpy()
        self.mesh.vertex_normals = None  # Force recompute

        # Ensure spacing between polyps
        edges = self.mesh.edges_unique
        lengths = self.mesh.edges_unique_length
        candidate: np.ndarray | None = None
        max_gap = self.polyp_spacing
        for edge, length in zip(edges, lengths, strict=False):
            if length > 2 * self.polyp_spacing and length > max_gap:
                v0, v1 = self.mesh.vertices[edge]
                candidate = (v0 + v1) / 2.0
                max_gap = float(length)

        if candidate is not None:
            self.add_polyp(candidate)
        else:
            # Mesh updated; refresh Warp arrays and normals
            self.update_wp_arrays()

    def reset(self) -> None:  # noqa: D401 - Simple placeholder
        """Reset coral state (currently a placeholder)."""

        pass

