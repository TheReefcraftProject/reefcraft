# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Simple PORAG-inspired growth model (relocated to sim.models)."""

from __future__ import annotations

import numpy as np
import warp as wp
from scipy.spatial import ConvexHull

from reefcraft.sim.models.growth_model import GrowthModel
from reefcraft.sim.state import CoralState, SimState


class SimplePoragGrowthModel(GrowthModel):
    """Coral growth simulation with polyps evenly spaced on a hemisphere surface."""

    def __init__(
        self,
        sim_state: SimState,
        coral_state: CoralState,
        grid_shape: tuple = (200, 200, 200),
        polyp_spacing: float = 0.1,
        max_time_steps: int = 1000,
        resource_concentration: float = 1.0,
    ) -> None:
        """Initializes the PORAG-inspired growth model."""
        super().__init__(sim_state=sim_state, coral_state=coral_state)
        self._name = "PORAG"
        self.inputs = {"water.velocity": "Velocity Field"}
        self.outputs = {"coral.mesh": "Coral Mesh (verts, faces)"}
        self._store = None
        self.grid_shape = grid_shape
        self.polyp_spacing = polyp_spacing
        self.max_time_steps = max_time_steps
        self.resource_concentration = resource_concentration
        self.device = "cuda"

        self.radius = self.calculate_radius()
        self.mesh = self.initialize_polyps()
        self.normals = wp.zeros((len(self.mesh["vertices"]),), dtype=wp.vec3f, device="cuda")
        self.launch_mesh_kernel()
        self.coral_state.set_mesh(self.mesh["vertices"], self.mesh["indices"])

    def calculate_radius(self) -> float:
        num_polyps = 81
        surface_area_per_polyp = self.polyp_spacing**2
        total_area = num_polyps * surface_area_per_polyp
        radius = np.sqrt(total_area / (2 * np.pi))
        return radius

    def initialize_polyps(self) -> dict:
        num_polyps = 81
        vertices = np.zeros((num_polyps, 3), dtype=np.float32)
        indices = np.arange(num_polyps, dtype=np.int32)
        golden_angle = np.pi * (3.0 - np.sqrt(5.0))
        for i in range(num_polyps):
            phi = np.arccos(1 - (i + 0.5) / num_polyps)
            theta = golden_angle * i
            x = self.radius * np.sin(phi) * np.cos(theta)
            y = self.radius * np.sin(phi) * np.sin(theta)
            z = self.radius * np.cos(phi)
            vertices[i] = [x, y, z]
        hull = ConvexHull(vertices)
        indices = hull.simplices.astype(np.int32)
        vertices_wp = wp.array(vertices, dtype=wp.vec3f, device="cuda")
        indices_wp = wp.array(indices, dtype=wp.vec3i, device="cuda")
        return {"vertices": vertices_wp, "indices": indices_wp}

    def attach_store(self, store) -> None:
        self._store = store

    def update(self, dt: float) -> None:  # noqa: ARG002
        if self._store is not None and self._store.has("water.velocity"):
            _vel = self._store.get("water.velocity")
        self.growth_step()
        self.growth_step()
        self.coral_state.set_mesh(self.mesh.get("vertices"), self.mesh.get("indices"))
        if self._store is not None:
            coral_id = getattr(self.coral_state, "coral_id", 0)
            self._store.put(f"coral.{coral_id}.mesh", (self.mesh.get("vertices"), self.mesh.get("indices")))

    def update_mesh(self, mesh_data: dict) -> None:
        self.mesh = mesh_data

    @wp.kernel
    def calculate_normals_kernel(vertices: wp.array(dtype=wp.vec3f), normals: wp.array(dtype=wp.vec3f), n: int) -> None:
        idx = wp.tid()
        if idx < n:
            vertex = vertices[idx]
            normal = vertex / wp.length(vertex)
            normals[idx] = normal

    def launch_mesh_kernel(self) -> None:
        num_polyps = len(self.mesh["vertices"])
        if self.normals is None:
            self.normals = wp.zeros(num_polyps, dtype=wp.vec3f, device="cuda")
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

    def add_polyp(self, new_polyp: tuple) -> None:
        vertices_np = self.mesh["vertices"].numpy()
        for vertex in vertices_np:
            if np.linalg.norm(vertex - np.array(new_polyp, dtype=np.float32)) < self.polyp_spacing:
                return
        new_vertices = np.concatenate([vertices_np, np.array([new_polyp], dtype=np.float32)], axis=0)
        new_idx = len(new_vertices) - 1
        indices_np = self.mesh["indices"].numpy()
        distances = np.linalg.norm(vertices_np - np.array(new_polyp, dtype=np.float32), axis=1)
        nearest = np.argsort(distances)[:3]
        new_tris = np.array([[new_idx, nearest[0], nearest[1]],[new_idx, nearest[1], nearest[2]],[new_idx, nearest[2], nearest[0]]], dtype=np.int32)
        self.mesh["vertices"] = wp.array(new_vertices, dtype=wp.vec3f, device=self.device)
        self.mesh["indices"] = wp.array(np.concatenate([indices_np, new_tris]), dtype=wp.vec3i, device=self.device)
        self.normals = wp.zeros(len(new_vertices), dtype=wp.vec3f, device=self.device)
        self.launch_mesh_kernel()

    def growth_step(self) -> None:
        vertices = self.mesh["vertices"]
        normals = self.normals
        growth_amount = wp.zeros(len(vertices), dtype=wp.float32, device="cuda")
        wp.launch(self.growth_kernel, dim=len(vertices), inputs=[vertices, normals, growth_amount, self.polyp_spacing, len(vertices), self.resource_concentration, float(self.grid_shape[2])])
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

    def step(self, dt: float) -> None:  # noqa: ARG002
        self.update(dt)


