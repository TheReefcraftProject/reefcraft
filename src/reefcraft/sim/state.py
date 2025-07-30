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
        """Retrieve the mesh data with left-handed (Y-up) coords for rendering."""
        # TODO: Add a check for None for the arrays
        verts_np = np.array(self.vertices.numpy(), copy=True)
        verts_np[:, [1, 2]] = verts_np[:, [2, 1]]  # Swap Y/Z for left-handed view
        return {
            "vertices": verts_np,
            "indices": np.array(self.indices.numpy(), copy=True),
        }

    """possible options for LBM accessing?"""

    def get_physics_mesh(self) -> dict:
        """Return the original right-handed (Z-up) mesh for physics/coupling."""
        return {
            "vertices": np.array(self.vertices.numpy(), copy=True),
            "indices": np.array(self.indices.numpy(), copy=True),
        }

    def get_physics_wp(self) -> tuple[wp.array, wp.array]:
        """Return the warp arrays directly (no copies)."""
        return self.vertices, self.indices


class SimState:
    """The data context for the simulation including all simulation state."""

    def __init__(self) -> None:
        """Initialize the simulation."""
        self.corals = []
        self.velocity_field: np.ndarray

    def add_coral(self) -> CoralState:
        """Add another coral state into the system and return it."""
        new_coral = CoralState()
        self.corals.append(new_coral)
        return new_coral
