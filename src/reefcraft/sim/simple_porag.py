# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Simple PORAG inspired growth model using :mod:`trimesh` for mesh handling."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import trimesh
import warp as wp

if TYPE_CHECKING:
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
        grid_shape: tuple[int, int, int] = (100, 100, 100),
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
        # Start with an icosphere and keep vertices on or above the equator
        sphere = trimesh.creation.icosphere(subdivisions=2, radius=self.radius)
        verts = sphere.vertices
        faces = sphere.faces

        mask = verts[:, 2] >= 0.0
        index_map = -np.ones(len(verts), dtype=np.int32)
        index_map[mask] = np.arange(mask.sum(), dtype=np.int32)
        faces_top = faces[np.all(mask[faces], axis=1)]
        verts_top = verts[mask]
        faces_top = index_map[faces_top]

        # Find boundary edges of the cut hemisphere
        edges = np.vstack([faces_top[:, [0, 1]], faces_top[:, [1, 2]], faces_top[:, [2, 0]]])
        edges_sorted = np.sort(edges, axis=1)
        unique_edges, counts = np.unique(edges_sorted, axis=0, return_counts=True)
        boundary_oriented = []
        for e in unique_edges[counts == 1]:
            idx = np.where((edges_sorted == e).all(axis=1))[0][0]
            boundary_oriented.append(edges[idx])
        boundary_oriented = np.array(boundary_oriented, dtype=np.int32)

        # Add a base centre vertex and connect boundary edges to form a cap
        center = np.array([[0.0, 0.0, 0.0]], dtype=np.float32)
        verts_new = np.vstack([verts_top, center])
        center_idx = len(verts_new) - 1
        base_faces = np.hstack([boundary_oriented[:, [1, 0]], np.full((len(boundary_oriented), 1), center_idx)])
        faces_new = np.vstack([faces_top, base_faces])

        return trimesh.Trimesh(vertices=verts_new, faces=faces_new, process=True)

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

            growth_amount[idx] = growth * spacing * 0.1
            vertices[idx] += normal * growth_amount[idx]

    def add_polyp(self, new_polyp: np.ndarray) -> None:
        """Add a new polyp (vertex) to the mesh if spacing permits."""
        if np.any(np.linalg.norm(self.mesh.vertices[:-1] - new_polyp, axis=1) < self.polyp_spacing):
            return

        verts = np.vstack([self.mesh.vertices, new_polyp]).astype(np.float32)
        new_idx = len(verts) - 1

        surface_count = len(self.mesh.vertices) - 1
        distances = np.linalg.norm(verts[:surface_count] - new_polyp, axis=1)
        nearest = np.argsort(distances)[:3]
        tris = [
            [new_idx, nearest[0], nearest[1]],
            [new_idx, nearest[1], nearest[2]],
            [new_idx, nearest[2], nearest[0]],
        ]

        # Ensure new triangles have outward-facing normals
        for tri in tris:
            v0, v1, v2 = verts[tri]
            if np.dot(np.cross(v1 - v0, v2 - v0), v0) < 0:
                tri[1], tri[2] = tri[2], tri[1]

        faces = np.vstack([self.mesh.faces, np.array(tris, dtype=np.int32)])
        self.mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
        self.mesh.fix_normals()
        self.update_wp_arrays()

    def growth_step(self) -> None:
        """Update state by growing the polyps and updating the mesh."""
        surface_count = len(self.verts_wp) - 1
        growth_amount = wp.zeros(len(self.verts_wp), dtype=wp.float32)
        wp.launch(
            self.growth_kernel,
            dim=surface_count,
            inputs=[
                self.verts_wp,
                self.normals_wp,
                growth_amount,
                self.polyp_spacing,
                surface_count,
                self.resource_concentration,
                float(self.grid_shape[2]),
            ],
        )
        wp.synchronize()

        # Update the mesh from the Warp vertex array
        self.mesh.vertices = self.verts_wp.numpy()
        self.mesh.vertex_normals = None  # Force recompute

        # Ensure spacing between polyps
        edges = self.mesh.edges_unique
        lengths = self.mesh.edges_unique_length
        candidate: np.ndarray | None = None
        max_gap = self.polyp_spacing
        base_index = len(self.mesh.vertices) - 1
        for edge, length in zip(edges, lengths, strict=False):
            if base_index in edge:
                continue
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
