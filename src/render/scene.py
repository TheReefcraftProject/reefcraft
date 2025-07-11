"""Simple animated scene definitions."""

from __future__ import annotations

import math
import time

import numpy as np
import pygfx as gfx


class TriangleScene:
    """Simple triangle scene with animated color."""

    def __init__(self) -> None:
        """Construct the triangle geometry and material."""
        self.scene = gfx.Scene()
        positions = np.array([
            [-0.5, -0.5, 0.0],
            [0.5, -0.5, 0.0],
            [0.0, 0.5, 0.0],
        ], dtype=np.float32)
        indices = np.array([0, 1, 2], dtype=np.uint32)
        geometry = gfx.Geometry(indices=indices, positions=positions)
        self.material = gfx.MeshBasicMaterial(color=(1.0, 0.0, 0.0, 1.0))
        self.mesh = gfx.Mesh(geometry, self.material)
        self.scene.add(self.mesh)
        self.start = time.perf_counter()

    def update(self) -> None:
        """Update animation state."""
        t = time.perf_counter() - self.start
        r = (math.sin(t) + 1) * 0.5
        g = (math.cos(t) + 1) * 0.5
        b = (math.sin(0.5 * t) + 1) * 0.5
        self.material.color = (r, g, b, 1.0)
