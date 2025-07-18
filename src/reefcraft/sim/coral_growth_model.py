# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Simple simulation engine used for driving updates."""

import numpy as np
import warp as wp
from numpy.typing import NDArray

from reefcraft.sim.sim_context import SimContext
from reefcraft.utils.logger import logger


class CoralGrowthModel:
    """A base class for all coral morphological models."""

    def __init__(self, context: SimContext) -> None:
        """Initialize the engine with a new :class:`Timer`."""
        self.context = context
        self.reset()

    def reset(self) -> None:
        """Reset the model to its initial conditions including resoring the coral seed mesh."""
        self.default_polyp_mesh()

    def step(self, time: float) -> None:
        """Advance the growth of the coral by the time provided."""
        pass

    def default_polyp_mesh(self, size: float = 1.0, height: float = 0.3, res: int = 16) -> None:
        """Returns: vertices: (res*res, 3) float32 array indices:  ((res-1)*(res-1)*2, 3) uint32 array."""
        logger.debug("POLYP GEN")
        # 1) build a res×res grid in the x–y plane
        xs = np.linspace(-size / 2, size / 2, res, dtype=np.float32)
        ys = np.linspace(-size / 2, size / 2, res, dtype=np.float32)
        xv, yv = np.meshgrid(xs, ys, indexing="xy")

        # 2) Gaussian bump for the mound normalized radius squared, falls off sharply
        rr = (xv / (size / 2)) ** 2 + (yv / (size / 2)) ** 2
        zv = height * np.exp(-5 * rr).astype(np.float32)

        # 3) Stack into vertex list
        vertices = np.stack([xv, zv, yv], axis=-1).reshape(-1, 3)

        # 4) Build quad‐to‐tri indices
        indices = []
        for i in range(res - 1):
            for j in range(res - 1):
                i0 = i * res + j
                i1 = i0 + 1
                i2 = i0 + res
                i3 = i2 + 1
                # two triangles per quad
                indices.append([i0, i2, i1])
                indices.append([i1, i2, i3])

        indices = np.array(indices, dtype=np.uint32)

        vertices_wp = wp.array(vertices, dtype=wp.vec3, device="cuda:0")
        indices_wp = wp.array(indices, dtype=wp.uint32, device="cuda:0")
        logger.debug("Num Verts {}, {}", vertices.size, vertices_wp.size)

        self.context.coral.set_mesh(vertices_wp, indices_wp)
