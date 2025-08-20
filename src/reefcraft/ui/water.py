# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Particle system for visualizing water flow."""

import numpy as np
import pygfx as gfx
import warp as wp

from reefcraft.utils.logger import logger


class WaterParticles:
    """Class to manage water particles for visualization."""

    def __init__(self, num_particles: int = 100, grid_shape: tuple = (32, 32, 32)) -> None:
        """Initialize particles randomly within LBM grid."""
        self.num_particles = num_particles
        self.grid_shape = np.array(grid_shape, dtype=np.float32)

        # Random initial positions in world space
        grid_centered = self.grid_shape / 2.0
        init_pos = np.random.uniform(
            low=[-grid_centered[0], 0, -grid_centered[2]],
            high=[grid_centered[0], grid_shape[1], grid_centered[2]],
            size=(num_particles, 3),
        ).astype(np.float32)

        # Store GPU copy
        self.positions_wp = wp.array(init_pos, dtype=wp.vec3)
        self.positions_buf = gfx.Buffer(init_pos)
        self.geometry = gfx.Geometry(positions=self.positions_buf)

        self.points = gfx.Points(self.geometry, gfx.PointsMaterial(color="#00ffbf", size=4))

        logger.info(f"[Warp] Initialized {num_particles} GPU particles.")

    def reset(self) -> None:
        """Reseed particles randomly in the domain (both Warp + gfx buffer)."""
        grid_centered = self.grid_shape / 2.0
        reset_pos = np.random.uniform(
            low=[-grid_centered[0], 0, -grid_centered[2]],
            high=[grid_centered[0], self.grid_shape[1], grid_centered[2]],
            size=(self.num_particles, 3),
        ).astype(np.float32)

        # Update both Warp and gfx
        self.positions_wp = wp.array(reset_pos, dtype=wp.vec3, device="cuda")
        self.positions_buf.set_data(reset_pos)

        logger.info("[Warp] Water particles reset.")

    def get_actor(self) -> gfx.Points:
        """Return the gfx actor to add to the scene."""
        return self.points

    def advect(self, velocity_field: np.ndarray, dt: float = 0.1) -> None:
        """Launch a warp kernel to advect particles using the velocity field."""
        # Flatten velocity field for easy indexing (assume shape [Nx, Ny, Nz, 3])
        flat_velocity = velocity_field.reshape(-1, 3).astype(np.float32)
        velocity_wp = wp.array(flat_velocity, dtype=wp.vec3)

        wp.launch(
            kernel=advect_kernel,
            dim=self.num_particles,
            inputs=[
                self.positions_wp,
                velocity_wp,
                wp.vec3(*self.grid_shape),
                dt,
            ],
        )

        # Sync back to CPU only for gfx update
        updated = self.positions_wp.numpy()
        self.positions_buf.set_data(updated)


@wp.kernel
def advect_kernel(
    positions: wp.array(dtype=wp.vec3),
    velocity_field: wp.array(dtype=wp.vec3),
    grid_shape: wp.vec3,
    dt: float,
) -> None:
    """Move particles using the velocity field."""
    tid = wp.tid()

    pos = positions[tid]

    half_x = grid_shape[0] * 0.5
    half_z = grid_shape[2] * 0.5

    gx = wp.clamp(wp.int(wp.round(pos[0] + half_x)), 1, int(grid_shape[0]) - 2)
    gy = wp.clamp(wp.int(wp.round(pos[1])), 1, int(grid_shape[1]) - 2)
    gz = wp.clamp(wp.int(wp.round(pos[2] + half_z)), 1, int(grid_shape[2]) - 2)

    index = (gx * int(grid_shape[1]) + gy) * int(grid_shape[2]) + gz
    vel = velocity_field[index]

    pos += vel * dt

    if pos[0] < -half_x:
        pos[0] = half_x - 1.0
    elif pos[0] > half_x:
        pos[0] = -half_x + 1.0

    if pos[1] < 0.0:
        pos[1] = 1.0
    elif pos[1] > grid_shape[1]:
        pos[1] = grid_shape[1] - 2.0

    if pos[2] < -half_z:
        pos[2] = half_z - 1.0
    elif pos[2] > half_z:
        pos[2] = -half_z + 1.0

    positions[tid] = pos
