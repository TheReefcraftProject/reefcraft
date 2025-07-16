import numpy as np
import warp as wp


class LlabresSurface:
    def __init__(self, device="cuda") -> None:
        self.device = device
        self.verts, self.faces = self.gen_llabres_seed()
        self.norms = wp.zeros(self.verts.shape[0], dtype=wp.vec3f, device=self.device)
        self.fixed = wp.zeros(self.verts.shape[0], dtype=wp.int32, device=self.device)

        # Initialize fixed verts
        verts_np = self.verts.numpy()
        fixed_mask = (verts_np[:, 2] <= 0.0).astype(np.int32)
        self.fixed = wp.array(fixed_mask, dtype=wp.int32, device=self.device)

    def gen_llabres_seed(self, radius=1.0, height=0.1) -> tuple[wp.array, wp.array]:
        verts = []
        faces = []

        # Center vertex
        verts.append([0.0, 0.0, height])

        # 6 hex ring verts
        for i in range(6):
            angle = i * np.pi / 3.0
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            z = 0.0
            verts.append([x, y, z])

        # Faces (triangles from center to ring)
        for i in range(6):
            faces.append([0, 1 + i, 1 + ((i + 1) % 6)])

        # Convert to warp arrays
        verts_wp = wp.array(np.array(verts, dtype=np.float32), dtype=wp.vec3f, device=self.device)
        faces_wp = wp.array(np.array(faces, dtype=np.int32), dtype=wp.vec3i, device=self.device)

        return verts_wp, faces_wp

    def step(self, thresh=0.3, amount=0.001):
        self.compute_normals()

        wp.launch(grow, dim=self.verts.shape[0], inputs=[self.verts, self.norms, self.fixed, thresh, amount], device=self.device)

        return self.subdiv()

    def compute_normals(self):
        # Zero the normals first
        self.norms.fill_(0.0)

        # Accumulate face contributions
        wp.launch(accumulate_normals, dim=self.faces.shape[0], inputs=[self.verts, self.faces, self.norms], device=self.device)

        # Normalize per vertex
        wp.launch(normalize_normals, dim=self.norms.shape[0], inputs=[self.norms], device=self.device)

    def get_dlpack(self) -> dict:
        """Export the mesh as DLPack for zero-copy to external systems."""
        return {"verts": self.verts.to_dlpack(), "faces": self.faces.to_dlpack()}

    def get_numpy(self) -> dict:
        """Optional: get CPU copies for debugging or visualization."""
        return {
            "verts": np.array(self.verts.numpy(), copy=True),
            "faces": np.array(self.faces.numpy(), copy=True),
            "norms": np.array(self.norms.numpy(), copy=True),
        }

    def subdiv(self, edge_thresh=0.8):
        verts_np = self.verts.numpy()
        faces_np = self.faces.numpy()

        new_verts = verts_np.tolist()
        new_faces = []
        edge_midpoints = {}

        M12 = []  # 1 edge splits
        M13 = []  # 2 edge splits
        M14 = []  # 3 edge splits

        subdivd = False  # track if subdiv happens so we can rebuild buffers

        for f in faces_np:
            i0, i1, i2 = f
            v0, v1, v2 = verts_np[i0], verts_np[i1], verts_np[i2]

            e0 = np.linalg.norm(v1 - v0)
            e1 = np.linalg.norm(v2 - v1)
            e2 = np.linalg.norm(v0 - v2)

            split0 = e0 > edge_thresh
            split1 = e1 > edge_thresh
            split2 = e2 > edge_thresh

            n_splits = split0 + split1 + split2

            if n_splits < 0 or n_splits > 3:
                raise RuntimeError(f"Invalid subdivision: triangle has {n_splits} splits")

            if n_splits == 0:
                new_faces.append([i0, i1, i2])
            else:
                subdivd = True
                if n_splits == 1:
                    # For subdiv_I, order matters: first two entries are the split edge
                    if split0:
                        M12.append([i0, i1, i2])
                    elif split1:
                        M12.append([i1, i2, i0])
                    else:  # split2
                        M12.append([i2, i0, i1])
                elif n_splits == 2:
                    # For subdiv_II, the unsplit edge determines ordering
                    if not split0:
                        M13.append([i0, i1, i2])
                    elif not split1:
                        M13.append([i1, i2, i0])
                    else:
                        M13.append([i2, i0, i1])
                elif n_splits == 3:
                    M14.append([i0, i1, i2])

        if M12:
            F12 = self.subdiv_I(new_verts, M12, edge_midpoints)
            new_faces.extend(F12.tolist())

        if M13:
            F13 = self.subdiv_II(new_verts, M13, edge_midpoints)
            new_faces.extend(F13.tolist())

        if M14:
            F14 = self.subdiv_III(new_verts, M14, edge_midpoints)
            new_faces.extend(F14.tolist())

        # Update Warp arrays
        self.verts = wp.array(np.array(new_verts, dtype=np.float32), dtype=wp.vec3f, device=self.device)
        self.faces = wp.array(np.array(new_faces, dtype=np.int32), dtype=wp.vec3i, device=self.device)

        # Recompute fixed and norms
        verts_np = np.array(new_verts, dtype=np.float32)
        fixed_mask = (verts_np[:, 2] <= 0.0).astype(np.int32)
        self.fixed = wp.array(fixed_mask, dtype=wp.int32, device=self.device)
        self.norms = wp.zeros(len(new_verts), dtype=wp.vec3f, device=self.device)

        return subdivd

    def subdiv_I(self, V, M12, edge_midpoints):
        print("subdiv_I")
        i1_list = []

        for i0, i1, i2 in M12:
            key = tuple(sorted((i0, i1)))
            if key in edge_midpoints:
                mid_idx = edge_midpoints[key]
            else:
                midpoint = 0.5 * (np.array(V[i0]) + np.array(V[i1]))
                mid_idx = len(V)
                edge_midpoints[key] = mid_idx
                V.append(midpoint.tolist())

            i1_list.append(mid_idx)

        i1 = np.array(i1_list, dtype=np.int32)
        M12_np = np.array(M12, dtype=np.int32)
        O1, O2, O3 = M12_np[:, 0], M12_np[:, 1], M12_np[:, 2]

        F12 = np.vstack([np.stack([O3, O1, i1], axis=1), np.stack([i1, O2, O3], axis=1)])

        return F12

    def subdiv_II(self, V, M13, edge_midpoints):
        print("subdiv_II")
        i1_list = []
        i2_list = []

        for i0, i1, i2 in M13:
            # Midpoint of (i0, i1)
            key1 = tuple(sorted((i0, i1)))
            if key1 in edge_midpoints:
                m1_idx = edge_midpoints[key1]
            else:
                m1 = 0.5 * (np.array(V[i0]) + np.array(V[i1]))
                m1_idx = len(V)
                edge_midpoints[key1] = m1_idx
                V.append(m1.tolist())

            # Midpoint of (i1, i2)
            key2 = tuple(sorted((i1, i2)))
            if key2 in edge_midpoints:
                m2_idx = edge_midpoints[key2]
            else:
                m2 = 0.5 * (np.array(V[i1]) + np.array(V[i2]))
                m2_idx = len(V)
                edge_midpoints[key2] = m2_idx
                V.append(m2.tolist())

            i1_list.append(m1_idx)
            i2_list.append(m2_idx)

        i1 = np.array(i1_list, dtype=np.int32)
        i2 = np.array(i2_list, dtype=np.int32)
        M13_np = np.array(M13, dtype=np.int32)
        O1, O2, O3 = M13_np[:, 0], M13_np[:, 1], M13_np[:, 2]

        F13 = np.vstack([np.stack([O1, i1, O3], axis=1), np.stack([i1, i2, O3], axis=1), np.stack([i1, O2, i2], axis=1)])

        return F13

    def subdiv_III(self, V, F, edge_midpoints):
        print("subdiv_III")
        i1_list = []
        i2_list = []
        i3_list = []

        for idx, (i0, i1, i2) in enumerate(F):
            # Midpoints
            k1 = tuple(sorted((i1, i2)))
            k2 = tuple(sorted((i2, i0)))
            k3 = tuple(sorted((i0, i1)))

            def get_or_create(key, v_start, v_end):
                if key in edge_midpoints:
                    return edge_midpoints[key]
                else:
                    m = 0.5 * (np.array(V[v_start]) + np.array(V[v_end]))
                    idx = len(V)
                    edge_midpoints[key] = idx
                    V.append(m.tolist())
                    return idx

            m1 = get_or_create(k1, i1, i2)
            m2 = get_or_create(k2, i2, i0)
            m3 = get_or_create(k3, i0, i1)

            i1_list.append(m3)
            i2_list.append(m1)
            i3_list.append(m2)

        i1 = np.array(i1_list, dtype=np.int32)
        i2 = np.array(i2_list, dtype=np.int32)
        i3 = np.array(i3_list, dtype=np.int32)

        F14 = np.vstack(
            [np.stack([F[:, 0], i3, i2], axis=1), np.stack([F[:, 1], i1, i3], axis=1), np.stack([F[:, 2], i2, i1], axis=1), np.stack([i1, i2, i3], axis=1)]
        )

        return F14


@wp.kernel
def grow(verts: wp.array(dtype=wp.vec3f), norms: wp.array(dtype=wp.vec3f), fixed: wp.array(dtype=wp.int32), thresh: float, amount: float) -> None:
    i = wp.tid()
    if fixed[i]:
        return

    n = norms[i]
    sigma = n[2] / wp.sqrt(n[0] * n[0] + n[1] * n[1] + 1e-6)

    if sigma > thresh:
        verts[i] += n * amount


@wp.kernel
def accumulate_normals(verts: wp.array(dtype=wp.vec3f), faces: wp.array(dtype=wp.vec3i), norms: wp.array(dtype=wp.vec3f)):
    t = wp.tid()

    i0, i1, i2 = faces[t][0], faces[t][1], faces[t][2]

    v0 = verts[i0]
    v1 = verts[i1]
    v2 = verts[i2]

    e1 = v1 - v0
    e2 = v2 - v0

    n = wp.normalize(wp.cross(e1, e2))

    wp.atomic_add(norms, i0, n)
    wp.atomic_add(norms, i1, n)
    wp.atomic_add(norms, i2, n)


@wp.kernel
def normalize_normals(norms: wp.array(dtype=wp.vec3f)):
    i = wp.tid()
    norms[i] = wp.normalize(norms[i])
