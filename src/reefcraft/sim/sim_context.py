# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Simple simulation engine used for driving updates."""

import numpy as np
import warp as wp

from reefcraft.utils.logger import logger


class CoralContext:
    """A base class for all coral morphological models."""

    def __init__(self) -> None:
        """Initialize the coral data state within the sim."""
        self.verts = wp.zeros(3, dtype=wp.vec3f)  # , device=self.device)
        self.faces = wp.zeros(3, dtype=wp.int32)  # , device=self.device)

    def get_render_mesh(self) -> dict:
        """Retrieve the mesh data for the coral we are growing."""
        return {
            "verts": np.array(self.verts.numpy(), copy=True),
            "faces": np.array(self.faces.numpy(), copy=True),
        }

    def set_mesh(self, vertices: wp.array, indices: wp.array) -> None:
        """Set the mesh data directly."""
        logger.debug("SET_MESH on CORAL: {}, {}", vertices, indices)
        self.verts = vertices
        self.indices = indices


class SimContext:
    """The data context for the simulation including all simulation state."""

    def __init__(self) -> None:
        """Initialize the simulation."""
        self.coral = CoralContext()
