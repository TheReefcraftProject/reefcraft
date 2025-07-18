# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Simple simulation engine used for driving updates."""

import numpy as np
import warp as wp

from reefcraft.utils.logger import logger


class CoralState:
    """A base class for all coral morphological models."""

    def __init__(self) -> None:
        """Initialize the coral data state within the sim."""
        self.vertices = None
        self.indices = None

    def set_mesh(self, vertices: wp.array, indices: wp.array) -> None:
        """Set the mesh data directly."""
        self.vertices = vertices
        self.indices = indices

    def get_render_mesh(self) -> dict:
        """Retrieve the mesh data for the coral we are growing."""
        # TODO: Add a check for None for the arrays
        return {
            "vertices": np.array(self.vertices.numpy(), copy=True),
            "indices": np.array(self.indices.numpy(), copy=True),
        }


class SimState:
    """The data context for the simulation including all simulation state."""

    def __init__(self) -> None:
        """Initialize the simulation."""
        self.coral = CoralState()
