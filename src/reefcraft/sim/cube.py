# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Simulation engine with fixed time step, real-time stats, and background execution."""

import numpy as np
import warp as wp

from reefcraft.sim.state import SimState


class Cube:
    """Simple cube coral mesh for testing."""

    def __init__(self, side_len: int = 10) -> None:
        """Initialize Cube Coral."""
        self.side_len = side_len

        # Create vertices for the cube
        half_len = self.side_len / 2
        self.vertices = np.array(
            [
                [-half_len, -half_len, 0],  # 0: front bottom left
                [half_len, -half_len, 0],  # 1: front bottom right
                [half_len, half_len, 0],  # 2: back bottom right
                [-half_len, half_len, 0],  # 3: back bottom left
                [-half_len, -half_len, self.side_len],  # 4: front top left
                [half_len, -half_len, self.side_len],  # 5: front top right
                [half_len, half_len, self.side_len],  # 6: back top right
                [-half_len, half_len, self.side_len],  # 7: back top left
            ],
            dtype=np.float32,
        )

        # Create indices for the cube faces (2 triangles per face)
        self.indices = np.array(
            [
                # Front face
                [0, 1, 2],
                [0, 2, 3],
                # Right face
                [1, 5, 6],
                [1, 6, 2],
                # Back face
                [5, 4, 7],
                [5, 7, 6],
                # Bottom face
                [0, 1, 5],
                [0, 5, 4],
                # Left face
                [4, 0, 3],
                [4, 3, 7],
                # Top face
                [3, 2, 6],
                [3, 6, 7],
            ],
            dtype=np.int32,
        )

        # Convert to Warp arrays
        self.vertices = wp.array(self.vertices, dtype=wp.vec3f)
        self.indices = wp.array(self.indices, dtype=wp.vec3i)

        self.mesh = (self.vertices, self.indices)

    def add_to_state(self, sim_state: SimState) -> None:
        """Add coral to sim state."""
        self.coral_state = sim_state.add_coral()
        self.coral_state.set_mesh(self.vertices, self.indices)
