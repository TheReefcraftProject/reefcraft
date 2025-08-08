# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Simple simulation engine used for driving updates."""

from typing import Literal

import numpy as np
import warp as wp

from reefcraft.sim.state import CoralState, SimState
from reefcraft.utils.logger import logger


class GrowthModel:
    """A base class for all coral morphological models."""

    def __init__(self, sim_state: SimState, coral_state: CoralState) -> None:
        """Initialize the engine with a new :class:`Timer`."""
        self.sim_state: SimState = sim_state
        self.coral_state: CoralState = coral_state
        self.reset()

    @property
    def name(self) -> Literal["Base Growth Model"]:
        """Override this with the correct name for your derived model."""
        return "Base Growth Model"

    def reset(self) -> None:
        """Reset the model to its initial conditions including resoring the coral seed mesh."""
        self.default_polyp_mesh()

    def update(self, dt: float) -> None:
        """Advance the growth of the coral by the time provided."""
        pass

    def default_polyp_mesh(self, size: float = 1.0, height: float = 0.3, res: int = 32) -> None:
        """vertices: (res*res, 3) float32 array indices:  ((res-1)*(res-1)*2, 3) uint32 array."""
        xs = np.linspace(-size / 2, size / 2, res, dtype=np.float32)
        ys = np.linspace(-size / 2, size / 2, res, dtype=np.float32)
        xv, yv = np.meshgrid(xs, ys, indexing="xy")

        # Gaussian bump for the mound normalized radius squared, falls off sharply
        rr = (xv / (size / 2)) ** 2 + (yv / (size / 2)) ** 2
        zv = height * np.exp(-5 * rr).astype(np.float32)

        # Stack into vertex list
        vertices = np.stack([xv, zv, yv], axis=-1).reshape(-1, 3)

        # Build quad‐to‐tri indices
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

        vertices_wp = wp.array(vertices, dtype=wp.vec3)
        indices_wp = wp.array(indices, dtype=wp.uint32)

        self.coral_state.set_mesh(vertices_wp, indices_wp)
