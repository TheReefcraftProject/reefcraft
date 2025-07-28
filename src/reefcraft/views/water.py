# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Particle system for visualizing water flow."""

import numpy as np
import pygfx as gfx

from reefcraft.utils.logger import logger


class WaterParticles:
    """Class to manage water particles for visualization."""

    def __init__(self, num_particles: int = 2000, grid_shape: tuple = (30, 30, 30)) -> None:
        """Initialize particles randomly within LBM grid."""
        self.num_particles = num_particles
        self.grid_shape = grid_shape

        grid_centered = np.array(grid_shape) / 2.0

        self.positions = np.random.uniform(
            low=[-grid_centered[0], 0, -grid_centered[2]], high=[grid_centered[0], grid_shape[1], grid_centered[2]], size=(num_particles, 3)
        ).astype(np.float32)

        self.positions_buf = gfx.Buffer(self.positions)
        self.geometry = gfx.Geometry(positions=self.positions_buf)

        self.points = gfx.Points(self.geometry, gfx.PointsMaterial(color="#00ffbf", size=2))

        logger.info(f"Initialized {num_particles} water particles.")

    def reset(self) -> None:
        """Reseed particles randomly in the domain."""
        self.positions = np.random.uniform(low=[0, 0, 0], high=self.grid_shape, size=(self.num_particles, 3)).astype(np.float32)

        self.positions_buf.set_data(self.positions)

        logger.info("Water particles reset.")

    def get_actor(self) -> gfx.Points:
        """Return the gfx actor to add to the scene."""
        return self.points

    def advect(self, velocity_field: np.ndarray, dt: float = 0.1) -> None:
        """Move particles using the velocity field with corrected indexing.

        Args:
            velocity_field: (32, 32, 32, 3) numpy array of velocity vectors.
            dt: timestep for advection.
        """
        xw, yw, zw = self.grid_shape
        x_half, z_half = xw / 2, zw / 2
        y_max = yw

        # Clip to interior of LBM field to avoid boundary dead zones
        ix = np.clip(np.round(self.positions[:, 0] + x_half).astype(int), 1, xw - 2)
        iy = np.clip(np.round(self.positions[:, 1]).astype(int), 1, yw - 2)
        iz = np.clip(np.round(self.positions[:, 2] + z_half).astype(int), 1, zw - 2)

        velocities = velocity_field[ix, iy, iz]

        # Move particles
        self.positions += velocities * dt

        # Get mask for out-of-bounds axes
        out_x_low = self.positions[:, 0] < -x_half
        out_x_high = self.positions[:, 0] > x_half
        out_y_low = self.positions[:, 1] < 0
        out_y_high = self.positions[:, 1] > y_max
        out_z_low = self.positions[:, 2] < -z_half
        out_z_high = self.positions[:, 2] > z_half

        # X wrap: reappear at opposite side
        self.positions[out_x_low, 0] = x_half - 1.0
        self.positions[out_x_high, 0] = -x_half + 1.0

        # Y bounce: reflect off top/bottom
        self.positions[out_y_low | out_y_high, 1] = np.clip(self.positions[out_y_low | out_y_high, 1], 1, y_max - 2)

        # Z wrap: reappear at opposite side
        self.positions[out_z_low, 2] = z_half - 1.0
        self.positions[out_z_high, 2] = -z_half + 1.0

        self.positions_buf.set_data(self.positions)
