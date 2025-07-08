import numpy as np


def gen_llabres_seed(radius=1.0, height=0.1):
    verts = []
    faces = []
    edge_set = set()

    # Center point (raised)
    verts.append([0.0, 0.0, height])  # index 0

    # 6 surrounding points in a hex ring
    for i in range(6):
        angle = i * np.pi / 3.0  # 60 degrees per step
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        z = 0.0  # grounded
        verts.append([x, y, z])

    # Create 6 triangles from center to ring
    for i in range(6):
        i0 = 0  # center
        i1 = 1 + i
        i2 = 1 + ((i + 1) % 6)
        faces.append([i0, i1, i2])

        edge_set.update(
            {
                tuple(sorted((i0, i1))),
                tuple(sorted((i1, i2))),
                tuple(sorted((i2, i0))),
            }
        )

    edges = np.array(list(edge_set), dtype=np.int32)
    return np.array(verts, dtype=np.float32), np.array(faces, dtype=np.int32), edges


# first attempt, very dense mesh
def gen_hemisphere(radius=1.0, n_lat=10, n_lon=20):
    verts = []
    faces = []
    edge_set = set()

    for i in range(n_lat + 1):
        theta = np.pi / 2 * (i / n_lat)

        for j in range(n_lon):
            phi = 2 * np.pi * (j / n_lon)
            x = radius * np.sin(theta) * np.cos(phi)
            y = radius * np.sin(theta) * np.sin(phi)
            z = radius * np.cos(theta)

            verts.append([x, y, z])

    for i in range(n_lat):
        for j in range(n_lon):
            next_j = (j + 1) % n_lon
            v0 = i * n_lon + j
            v1 = i * n_lon + next_j
            v2 = (i + 1) * n_lon + j
            v3 = (i + 1) * n_lon + next_j

            faces.append([v0, v2, v1])
            faces.append([v1, v2, v3])

            edge_set.update(
                {
                    tuple(sorted((v0, v2))),
                    tuple(sorted((v2, v1))),
                    tuple(sorted((v1, v0))),
                    tuple(sorted((v1, v2))),
                    tuple(sorted((v2, v3))),
                    tuple(sorted((v3, v1))),
                }
            )
    edges = np.array(list(edge_set), dtype=np.int32)
    return np.array(verts, dtype=np.float32), np.array(faces, dtype=np.int32), edges
