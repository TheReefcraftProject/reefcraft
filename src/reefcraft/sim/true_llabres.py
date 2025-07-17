import numpy as np
import warp as wp

# -----------------------------------------------------------------------------
# Simple true Llabrés-style pipeline to generate final coral mesh
# -----------------------------------------------------------------------------


def gen_llabres_mesh():
    # Initialize Warp
    wp.init()

    # Parameters
    num_iters = 80
    thresh = 0.57
    amount = 0.1
    dmax = 1.0
    edge_midpoints = {}

    # Generate initial hex seed
    def gen_llabres_seed(radius=1.0, height=0.1):
        verts = [[0.0, 0.0, height]]
        for i in range(6):
            angle = i * np.pi / 3.0
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            verts.append([x, y, 0.0])

        faces = []
        for i in range(6):
            faces.append([0, 1 + i, 1 + ((i + 1) % 6)])

        return np.array(verts, dtype=np.float32), np.array(faces, dtype=np.int32)

    verts_np, faces_np = gen_llabres_seed()

    device = "cuda"
    verts = wp.array(verts_np, dtype=wp.vec3f, device=device)
    faces = wp.array(faces_np, dtype=wp.vec3i, device=device)
    fixed = wp.array((verts_np[:, 2] <= 0.0).astype(np.int32), dtype=wp.int32, device=device)
    norms = wp.zeros(verts.shape[0], dtype=wp.vec3f, device=device)

    for it in range(num_iters):
        norms.fill_(0.0)
        wp.launch(accumulate_normals, dim=faces.shape[0], inputs=[verts, faces, norms], device=device)
        wp.launch(normalize_normals, dim=norms.shape[0], inputs=[norms], device=device)

        norms_np = norms.numpy()
        verts_np = verts.numpy()
        for i in range(len(verts_np)):
            if np.isclose(verts_np[i][2], 0.0, atol=1e-6):
                norms_np[i][2] = 0.0
                norm = np.linalg.norm(norms_np[i])
                if norm > 1e-8:
                    norms_np[i] /= norm
        norms = wp.array(norms_np, dtype=wp.vec3f, device=device)

        wp.launch(grow, dim=verts.shape[0], inputs=[verts, norms, fixed, thresh, amount], device=device)

        verts_np = verts.numpy()
        faces_np = faces.numpy()

        verts_np, faces_np = subdiv_total(verts_np, faces_np, edge_midpoints, dmax)

        verts = wp.array(verts_np, dtype=wp.vec3f, device=device)
        faces = wp.array(faces_np, dtype=wp.vec3i, device=device)
        fixed = wp.array((verts_np[:, 2] <= 0.0).astype(np.int32), dtype=wp.int32, device=device)
        norms = wp.zeros(verts.shape[0], dtype=wp.vec3f, device=device)

    print("[DONE] Growth complete, verts and faces ready")
    return verts_np, faces_np


def subdiv_total(V, F, edge_midpoints, dmax=1.0):
    if edge_midpoints is None:
        edge_midpoints = {}

    V = np.array(V, dtype=np.float32)
    F = np.array(F, dtype=np.int32)

    new_verts = V.tolist()
    new_faces = []

    M12, M13, M14, F11 = [], [], [], []

    for f in F:
        i0, i1, i2 = f
        v0, v1, v2 = V[i0], V[i1], V[i2]

        e0 = np.linalg.norm(v1 - v0)
        e1 = np.linalg.norm(v2 - v1)
        e2 = np.linalg.norm(v0 - v2)

        edges = [e0, e1, e2]
        nsub = sum(e > dmax for e in edges)

        if nsub == 3:
            M14.append([i0, i1, i2])
        elif nsub == 2:
            if e0 <= dmax:
                M13.append([i0, i1, i2])
            elif e1 <= dmax:
                M13.append([i1, i2, i0])
            else:
                M13.append([i2, i0, i1])
        elif nsub == 1:
            if e0 > dmax:
                M12.append([i0, i1, i2])
            elif e1 > dmax:
                M12.append([i1, i2, i0])
            else:
                M12.append([i2, i0, i1])
        else:
            F11.append([i0, i1, i2])

    if M14:
        F14 = subdiv_III(new_verts, np.array(M14, dtype=np.int32), edge_midpoints)
        new_faces.extend(F14.tolist())

    if M13:
        F13 = subdiv_II(new_verts, np.array(M13, dtype=np.int32), edge_midpoints)
        new_faces.extend(F13.tolist())

    if M12:
        F12 = subdiv_I(new_verts, np.array(M12, dtype=np.int32), edge_midpoints)
        new_faces.extend(F12.tolist())

    if F11:
        new_faces.extend(F11)

    VV = np.array(new_verts, dtype=np.float32)
    FF = np.array(new_faces, dtype=np.int32)

    return VV, FF


def subdiv_I(V, M12, edge_midpoints):
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


def subdiv_II(V, M13, edge_midpoints):
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


def subdiv_III(V, F, edge_midpoints):
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
def grow(verts: wp.array(dtype=wp.vec3f), norms: wp.array(dtype=wp.vec3f), fixed: wp.array(dtype=wp.int32), thresh: float, amount: float):
    i = wp.tid()
    if fixed[i]:
        return
    n = norms[i]
    sigma = n[2] / wp.sqrt(n[0] * n[0] + n[1] * n[1] + 1e-6)
    if sigma >= thresh:
        verts[i] += n * amount


@wp.kernel
def accumulate_normals(verts: wp.array(dtype=wp.vec3f), faces: wp.array(dtype=wp.vec3i), norms: wp.array(dtype=wp.vec3f)):
    t = wp.tid()
    i0, i1, i2 = faces[t][0], faces[t][1], faces[t][2]
    v0, v1, v2 = verts[i0], verts[i1], verts[i2]
    e1 = v1 - v0
    e2 = v2 - v0
    cross = wp.cross(e1, e2)
    if wp.length(cross) > 1e-8:
        n = wp.normalize(cross)
        wp.atomic_add(norms, i0, n)
        wp.atomic_add(norms, i1, n)
        wp.atomic_add(norms, i2, n)


@wp.kernel
def normalize_normals(norms: wp.array(dtype=wp.vec3f)):
    i = wp.tid()
    norms[i] = wp.normalize(norms[i])
