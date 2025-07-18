# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Simple simulation engine used for driving updates."""

from typing import Literal

import numpy as np
import warp as wp

from reefcraft.sim.state import SimState
from reefcraft.utils.logger import logger


class GrowthModel:
    """A base class for all coral morphological models."""

    def __init__(self, context: SimState) -> None:
        """Initialize the engine with a new :class:`Timer`."""
        self.context = context
        self.reset()

    @property
    def name(self) -> Literal["Base Growth Model"]:
        """Override this with the correct name for your derived model."""
        return "Base Growth Model"

    def reset(self) -> None:
        """Reset the model to its initial conditions including resoring the coral seed mesh."""
        self.default_polyp_mesh()

    def update(self, time: float) -> None:
        """Advance the growth of the coral by the time provided."""

        @wp.kernel
        def wave_in_place(
            verts: wp.array(dtype=wp.vec3),  # your single vec3 array
            t: float,  # time in seconds
            amp: float,  # amplitude of the wave
            freq: float,  # frequency in Hz
        ):
            i = wp.tid()
            p = verts[i]
            p.z = wp.sin(t * 2.0 * 3.141592653589793 * freq) * amp
            verts[i] = p

        vertices = self.context.coral.vertices
        wp.launch(
            wave_in_place,
            dim=vertices.shape[0],
            inputs=[vertices, time, 0.1, 0.5],
            device="cuda:0",
        )

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

        vertices_wp = wp.array(vertices, dtype=wp.vec3, device="cuda:0")
        indices_wp = wp.array(indices, dtype=wp.uint32, device="cuda:0")

        self.context.coral.set_mesh(vertices_wp, indices_wp)
