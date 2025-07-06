# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Voxel grid representing a cubic meter of water."""

from __future__ import annotations

import taichi as ti


class Volume:
    """A sparse voxel volume at millimeter resolution."""

    def __init__(self, active_region: int = 32) -> None:
        """Create the voxel grid.

        Args:
            active_region: Size of the region to initialize with test data.
                The logical volume is ``1000^3`` voxels, but only an
                ``active_region`` cube is allocated for this preview to avoid
                excessive memory use.
        """
        self.resolution = 1000
        self.active = active_region
        self.data = ti.Vector.field(3, dtype=ti.f32, shape=(self.active, self.active, self.active))
        self.coords = ti.Vector.field(3, dtype=ti.f32, shape=self.active ** 3)
        self.colors = ti.Vector.field(3, dtype=ti.f32, shape=self.active ** 3)
        self._fill_test_pattern()

    @ti.kernel
    def _fill_test_pattern(self) -> None:
        for i, j, k in ti.ndrange(self.active, self.active, self.active):
            idx = i * self.active * self.active + j * self.active + k
            self.data[i, j, k] = ti.Vector([1.0, 1.0, 1.0])
            self.coords[idx] = ti.Vector([i, j, k]) / self.resolution
            self.colors[idx] = ti.Vector([i, j, k]) / self.active

    def render(self, scene: ti.ui.Scene) -> None:
        """Draw the voxel test pattern to ``scene``."""
        scene.particles(self.coords, radius=0.002, per_vertex_color=self.colors)
