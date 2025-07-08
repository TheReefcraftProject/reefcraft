# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

import numpy as np
import taichi as ti


@ti.data_oriented
class LlabresSurface:
    def __init__(self, verts_np: np.ndarray, faces_np: np.ndarray, edges_np: np.ndarray):
        self.num_verts = verts_np.shape[0]
        self.num_faces = faces_np.shape[0]

        self.verts = ti.Vector.field(3, dtype=ti.f32, shape=self.num_verts)
        self.norms = ti.Vector.field(3, dtype=ti.f32, shape=self.num_verts)
        self.faces = ti.Vector.field(3, dtype=ti.i32, shape=self.num_faces)
        self.edges = ti.Vector.field(2, dtype=ti.i32, shape=edges_np.shape[0])
        self.render_verts = ti.Vector.field(2, dtype=ti.f32, shape=self.num_verts)

        self.verts.from_numpy(verts_np)
        self.faces.from_numpy(faces_np)
        self.edges.from_numpy(edges_np)
        self.compute_norms()

    @ti.kernel
    def grow(self, threshold: float, amount: float):
        for i in self.verts:
            n = self.norms[i]
            nx, ny, nz = n[0], n[1], n[2]
            sigma = nz / ti.sqrt(nx**2 + ny**2 + 1e-6)

            if sigma > threshold:
                self.verts[i] += amount * n.normalized()

    @ti.kernel
    def compute_norms(self):
        for i in self.norms:
            self.norms[i] = ti.Vector([0.0, 0.0, 0.0])

        for f in self.faces:
            i0, i1, i2 = self.faces[f][0], self.faces[f][1], self.faces[f][2]
            v0, v1, v2 = self.verts[i0], self.verts[i1], self.verts[i2]

            e1 = v1 - v0
            e2 = v2 - v0
            norm = ti.math.cross(e1, e2).normalized()

            ti.atomic_add(self.norms[i0], norm)
            ti.atomic_add(self.norms[i1], norm)
            ti.atomic_add(self.norms[i2], norm)

        for i in self.norms:
            self.norms[i] = self.norms[i].normalized()

    # @ti.kernel
    # def update_render_verts(self):
    #     for i in self.verts:
    #         v = self.verts[i]
    #         # Project x, y from [-1, 1] → [0, 1]
    #         norm_x = (v[0] + 1.0) * 0.5
    #         norm_y = (v[1] + 1.0) * 0.5
    #         self.render_verts[i] = ti.Vector([norm_x, norm_y])

    @ti.kernel
    def update_render_verts(self, aspect_ratio: float):
        # Rotate mesh to view from side (X-axis rotation)
        angle = ti.math.radians(-60.0)  # Tilt downward 45 degrees
        cos_theta = ti.cos(angle)
        sin_theta = ti.sin(angle)

        for i in self.verts:
            v = self.verts[i]

            # Rotate around X-axis to tilt mesh
            x = v[0]
            y = v[1] * cos_theta - v[2] * sin_theta
            # z = v[1] * sin_theta + v[2] * cos_theta

            x /= aspect_ratio  # correct for aspect ratio

            # Center and scale to fit in canvas
            scale = 0.4
            offset = 0.5
            screen_x = x * scale + offset
            screen_y = y * scale + offset

            self.render_verts[i] = ti.Vector([screen_x, screen_y])

    def draw_edges(self, canvas, color=(1.0, 1.0, 1.0), thickness=1.0):
        verts = self.render_verts.to_numpy()
        edges = self.edges.to_numpy()

        lines = []
        for i in range(edges.shape[0]):
            i0, i1 = edges[i]
            lines.append(verts[i0])
            lines.append(verts[i1])

        lines_np = np.array(lines, dtype=np.float32)
        line_field = ti.Vector.field(2, dtype=ti.f32, shape=lines_np.shape[0])
        line_field.from_numpy(lines_np)
        canvas.lines(vertices=line_field, width=thickness, color=color)
