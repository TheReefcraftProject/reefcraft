"""Simple animated scene definitions."""

from __future__ import annotations

import math
import time

import numpy as np
import pygfx as gfx
import pylinalg as la  # pip install pylinalg


class Scene:
    """Animated triangle scene for rendering demos."""

    def __init__(self) -> None:
        """Initialize the triangle mesh and lighting."""
        self.scene = gfx.Scene()
        self.scene.add(gfx.AmbientLight())
        self.scene.add(gfx.DirectionalLight())

        # camera = gfx.PerspectiveCamera(70, 16 / 9)
        # camera.local.z = 400

        positions = np.array(
            [
                [0.0, 100.0, 0.0],
                [-100.0, -100.0, 0.0],
                [100.0, -100.0, 0.0],
            ],
            dtype=np.float32,
        )
        indices = np.array([0, 1, 2], dtype=np.uint32)

        geometry = gfx.Geometry(positions=positions, indices=indices)
        self.material = gfx.MeshPhongMaterial(color="#336699")
        self.mesh = gfx.Mesh(geometry, self.material)
        self.scene.add(self.mesh)

        self.start = time.perf_counter()

    def update(self) -> None:
        """Advance animation state for the mesh."""
        t = time.perf_counter() - self.start

        # animate color as before
        r = (math.sin(t) + 1) * 0.5
        g = (math.cos(t) + 1) * 0.5
        b = (math.sin(0.5 * t) + 1) * 0.5
        self.material.color = (r, g, b, 1.0)

        # create a rotation quaternion from euler angles (in radians)
        # here we spin around X and Y at different speeds:
        q = la.quat_from_euler((t * 0.8, t * 0.5, 0.0), order="XYZ")

        # apply it
        self.mesh.local.rotation = q
