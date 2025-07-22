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
    def __init__(self, num_particles: int = 1000, grid_shape: tuple = (64, 64, 64)) -> None:
        """Initialize particles randomly within LBM grid."""
        self.num_particles = num_particles
        self.grid_shape = grid_shape

        grid_centered = np.array(grid_shape)/2.0

        self.positions = np.random.uniform(
            low = [-grid_centered[0], 0, -grid_centered[2]],
            high = [grid_centered[0], grid_shape[1], grid_centered[2]],
            size = (num_particles, 3)
        ).astype(np.float32)

        self.positions_buf = gfx.Buffer(self.positions)
        self.geometry = gfx.Geometry(positions = self.positions_buf)

        self.points = gfx.Points(
            self.geometry,
            gfx.PointsMaterial(color = "#00ffff", size = 2)
        )

        logger.info(f"Initialized {num_particles} water particles.")

    def reset(self) -> None:
        """Reseed particles randomly in the domain."""
        self.positions = np.random.uniform(
            low = [0, 0, 0],
            high = self.grid_shape,
            size = (self.num_particles, 3)
        ).astype(np.float32)

        self.positions_buf.set_data(self.positions)

        logger.info("Water particles reset.")

    def get_actor(self) -> gfx.Points:
        """Return the gfx actor to add to the scene."""
        return self.points
    
    def advect(self, velocity_field: np.ndarray, dt: float = 0.1) -> None:
        """Move particles using the velocity field.

        Args:
            velocity_field: (64, 64, 64, 3) numpy array of velocity vectors.
            dt: timestep for advection.
        """
        positions = self.positions.copy()

        #convert world pos to LBM grid idx
        ix = np.clip(np.round(positions[:, 0] + self.grid_shape[0] / 2).astype(int), 0, self.grid_shape[0]-1)
        iy = np.clip(np.round(positions[:, 1]).astype(int), 0, self.grid_shape[1]-1)
        iz = np.clip(np.round(positions[:, 2] + self.grid_shape[2] / 2).astype(int), 0, self.grid_shape[2]-1)

        #handle possible nan vals
        vel_field = np.nan_to_num(velocity_field, nan=0.0)

        # Use vel_field instead of velocity_field for sampling
        velocities = vel_field[ix, iy, iz]

        # Update positions
        self.positions += velocities * dt

        self.positions[:, 0] = (self.positions[:, 0] + self.grid_shape[0]/2) % self.grid_shape[0] - self.grid_shape[0]/2
        self.positions[:, 1] = np.clip(self.positions[:, 1], 0, self.grid_shape[1])  # Y stays clamped for now
        self.positions[:, 2] = (self.positions[:, 2] + self.grid_shape[2]/2) % self.grid_shape[2] - self.grid_shape[2]/2

        self.positions_buf.set_data(self.positions)

