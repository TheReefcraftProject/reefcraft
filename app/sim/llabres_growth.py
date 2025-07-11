# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

import numpy as np
import taichi as ti

from .mesh_seed import gen_llabres_seed


@ti.data_oriented
class LlabresSurface:
    def __init__(self, verts_np=None, faces_np=None, edges_np=None):
        if verts_np is None or faces_np is None or edges_np is None:
            verts_np, faces_np, edges_np = gen_llabres_seed()

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

        # fix verts on the ground
        self.fixed = ti.field(dtype=ti.i32, shape=self.num_verts)
        for i in range(self.num_verts):
            if verts_np[i][2] <= 0.0:
                self.fixed[i] = 1
            else:
                self.fixed[i] = 0

    @ti.kernel
    def grow(self, threshold: float, amount: float):  # llabres growth method --> grow based on surf norms
        for i in self.verts:
            if self.fixed[i]:
                continue

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
    def update_render_verts(self, aspect_ratio: float):  # projects 3D verts to 2D screen space
        angle = ti.math.radians(-60.0)  # rotate to visualize growth from angle, will revisit once user cam is implemented
        cos_theta = ti.cos(angle)
        sin_theta = ti.sin(angle)

        for i in self.verts:
            v = self.verts[i]

            # Rotate around X-axis to tilt mesh
            x = v[0]
            y = v[1] * cos_theta - v[2] * sin_theta
            # z = v[1] * sin_theta + v[2] * cos_theta

            x /= aspect_ratio  # adjust for aspect ratio, changing screen size doesnt stretch mesh representation

            # Center and scale to fit in canvas
            scale = 0.4
            offset = 0.5
            screen_x = x * scale + offset
            screen_y = y * scale + offset

            self.render_verts[i] = ti.Vector([screen_x, screen_y])

            # if i == 0:  # Only show one for sanity
            #     print(f"[DEBUG] screen_x: {screen_x}, screen_y: {screen_y}")

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

        # print(f"[DEBUG] render_verts shape: {verts.shape}, edges shape: {edges.shape}")

    def step(self, grow_thresh: float, amount: float, split_thresh: float):
        """Edge-based subdivision approach."""
        self.compute_norms()
        self.grow(grow_thresh, amount)

        # Skip subdivision if mesh is too complex
        if self.num_verts > 200:
            print("Mesh too large, skipping subdivision")
            return

        # Find edges that need to be split
        verts = self.verts.to_numpy()
        edges = self.edges.to_numpy()
        faces = self.faces.to_numpy()

        edges_to_split = self.find_edges_to_split(verts, edges, split_thresh)

        if len(edges_to_split) == 0:
            return

        # Limit to one edge per frame for stability
        edges_to_split = edges_to_split[:1]

        print(f"Splitting {len(edges_to_split)} edges")
        print(f"Current mesh: {len(verts)} verts, {len(faces)} faces")

        # Perform edge-based subdivision
        new_verts, new_faces, new_edges = self.subdivide_edges(edges_to_split, verts, faces, edges)

        if new_faces.shape[0] == 0:
            print("Subdivision failed")
            return

        print(f"After subdivision: {len(new_verts)} verts, {len(new_faces)} faces")

        # Update mesh
        self.rebuild_mesh(new_verts, new_faces, new_edges)

    def find_edges_to_split(self, verts, edges, split_thresh):
        """Find edges that should be split based on vertex displacement."""
        edges_to_split = []

        for i, edge in enumerate(edges):
            v1, v2 = edge
            edge_length = np.linalg.norm(verts[v1] - verts[v2])
            # Split edge if longer than threshold
            if edge_length > split_thresh:
                edges_to_split.append(i)

        return edges_to_split

    def subdivide_edges(self, edges_to_split, verts, faces, edges):
        """Subdivide by splitting edges and maintaining triangular mesh."""
        new_verts = verts.copy()
        new_faces = []
        edge_midpoints = {}

        # Create midpoints for edges to split
        for edge_idx in edges_to_split:
            v1, v2 = edges[edge_idx]
            if edge_idx not in edge_midpoints:
                midpoint = 0.5 * (verts[v1] + verts[v2])
                new_verts = np.vstack([new_verts, midpoint])
                edge_midpoints[edge_idx] = len(new_verts) - 1

        # Process each face
        for face in faces:
            face_edges = []
            valid = True
            for i in range(3):
                v1, v2 = face[i], face[(i + 1) % 3]
                edge_key = self.find_edge_index(edges, v1, v2)

                if edge_key == -1:
                    print(f"Skipping face {face} due to missing edge")
                    valid = False
                    break
                face_edges.append(edge_key)

            if not valid:
                continue

            # Check if any edge of this face is being split
            split_edges_in_face = [e for e in face_edges if e in edges_to_split]

            if len(split_edges_in_face) == 0:
                # No splits in this face, keep original
                new_faces.append(face)
            elif len(split_edges_in_face) == 1:
                # One edge split - create 2 triangles
                new_faces.extend(self.split_face_one_edge(face, split_edges_in_face[0], edges, edge_midpoints))
            else:
                # Multiple edges split - more complex subdivision
                new_faces.extend(self.split_face_multiple_edges(face, split_edges_in_face, edges, edge_midpoints))

        # Rebuild edge list
        new_edges = self.rebuild_edges(new_faces)

        max_index = len(new_verts) - 1
        for edge in new_edges:
            if edge[0] > max_index or edge[1] > max_index:
                print(f"Invalid edge: {edge}, max index: {max_index}")

        return new_verts, np.array(new_faces, dtype=np.int32), new_edges

    def find_edge_index(self, edges, v1, v2):
        """Find the index of an edge in the edges array."""
        for i, edge in enumerate(edges):
            if (edge[0] == v1 and edge[1] == v2) or (edge[0] == v2 and edge[1] == v1):
                return i
        print(f"Edge not found between {v1} and {v2}")
        return -1

    def split_face_one_edge(self, face, split_edge_idx, edges, edge_midpoints):
        """Split a triangle when one edge is subdivided."""
        v1, v2 = edges[split_edge_idx]
        midpoint = edge_midpoints[split_edge_idx]

        # Find the third vertex of the triangle
        third_vertex = None
        for v in face:
            if v != v1 and v != v2:
                third_vertex = v
                break
        if third_vertex is None:  # DEBUG
            print(f"Could not find third vertex in face: {face} vs edge: {edges[split_edge_idx]}")
        # Create two new triangles
        return [[v1, midpoint, third_vertex], [midpoint, v2, third_vertex]]

    def split_face_multiple_edges(self, face, split_edges, edges, edge_midpoints):
        """Handle faces with multiple split edges (more complex case)."""
        # For now, just create a simple subdivision
        # This could be improved with more sophisticated mesh topology
        return [face]  # Keep original face for now

    def rebuild_edges(self, faces):
        """Rebuild edge list from face list."""
        edge_set = set()
        for face in faces:
            for i in range(3):
                edge = tuple(sorted([face[i], face[(i + 1) % 3]]))
                edge_set.add(edge)
        return np.array(list(edge_set), dtype=np.int32)

    def rebuild_mesh(self, new_verts, new_faces, new_edges):
        """Rebuild the mesh with new geometry."""
        self.num_verts = new_verts.shape[0]
        self.num_faces = new_faces.shape[0]

        # Recreate all fields
        self.verts = ti.Vector.field(3, dtype=ti.f32, shape=self.num_verts)
        self.norms = ti.Vector.field(3, dtype=ti.f32, shape=self.num_verts)
        self.faces = ti.Vector.field(3, dtype=ti.i32, shape=self.num_faces)
        self.edges = ti.Vector.field(2, dtype=ti.i32, shape=new_edges.shape[0])
        self.render_verts = ti.Vector.field(2, dtype=ti.f32, shape=self.num_verts)
        self.fixed = ti.field(dtype=ti.i32, shape=self.num_verts)

        # Load new data
        self.verts.from_numpy(new_verts)
        self.faces.from_numpy(new_faces)
        self.edges.from_numpy(new_edges)

        # fix grounded points
        for i in range(self.num_verts):
            if new_verts[i][2] <= 0.0:
                self.fixed[i] = 1
            else:
                self.fixed[i] = 0

        self.compute_norms()

        # flat_faces = new_faces.flatten()
        # if np.any(flat_faces >= new_verts.shape[0]):
        #     print("One or more faces reference an invalid vertex index!")
