# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

import warp as wp
import numpy as np

"""
ReefSpace is the space acted on by ComputeLBM and coral growth models.

"""

class ReefSpace:
    def __init__(self, grid_size):
        self.grid_size = grid_size

    @wp.kernel
    def _init_kernel(self):
        # Create an empty 3D grid with the specified size
        self.grid = wp.empty(shape=self.grid_size, dtype=wp.vec3, device="cuda")

