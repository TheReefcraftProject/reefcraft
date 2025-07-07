# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------
import taichi as ti
import numpy as np
import matplotlib as plt

# Initialize Taichi
ti.init(arch=ti.gpu)

@ti.data_oriented
class LBM:
    def __init__(self, grid_size, tau):
        self.n = grid_size  # Grid size (n x n x n)
        self.tau = tau  # Relaxation time
        self.velocities = ti.Vector.field(3, dtype=ti.f32, shape=19)  # 19 velocity directions (D3Q19)
        
        # Fields for velocity and distribution functions
        self.f = ti.field(dtype=ti.f32, shape=(self.n, self.n, self.n, 19))  # Distribution function (D3Q19 has 19 velocities)
        self.feq = ti.field(dtype=ti.f32, shape=(self.n, self.n, self.n, 19))  # Equilibrium distribution
        self.rho = ti.field(dtype=ti.f32, shape=(self.n, self.n, self.n))  # Density field
        self.u = ti.field(dtype=ti.f32, shape=(self.n, self.n, self.n, 3))  # Velocity field (3D)

    @ti.func
    def initialize_velocities(self):
        # Initialize the velocity directions in self.velocities (D3Q19 lattice directions)
        directions = [
            (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1),
            (1, 1, 0), (-1, 1, 0), (1, -1, 0), (-1, -1, 0), (1, 0, 1), (-1, 0, 1),
            (1, 0, -1), (-1, 0, -1), (0, 1, 1), (0, -1, 1), (0, 1, -1), (0, -1, -1)
        ]
        for i, direction in enumerate(directions):
            self.velocities[i] = ti.Vector(direction)  # Set velocity direction in the field

    @ti.kernel
    def compute_feq(self):
        """ Compute the equilibrium distribution function f_eq for the D3Q19 lattice model. """
        for i, j, k in self.rho:
            cu = self.u[i, j, k]
            rho = self.rho[i, j, k]
            feq = ti.Vector([0.0] * 19)  # Vector to hold equilibrium distribution for 19 velocities

            # Loop through each direction (19 directions in D3Q19)
            for l in range(19):  # There are 19 directions in D3Q19
                vx, vy, vz = self.velocities[l]  # Accessing the velocity vector directly from the Taichi Vector field
                cu_dot = cu.dot(ti.Vector([vx, vy, vz]))  # Dot product of cu and lattice direction
                # Calculate the equilibrium distribution function
                feq[l] = (1 / 3) * rho * (1 + 3 * cu_dot + 9 * cu_dot**2 / 2 - cu.norm()**2 / 2)

            self.feq[i, j, k] = feq  # Store the equilibrium distribution in the field

    @ti.kernel
    def collide(self):
        """ Perform the BGK collision step: Relaxation of distribution functions to equilibrium. """
        for i, j, k in self.rho:
            for l in range(19):  # 19 directions for D3Q19
                self.f[i, j, k, l] = self.f[i, j, k, l] - (self.f[i, j, k, l] - self.feq[i, j, k, l]) / self.tau

    @ti.kernel
    def stream(self):
        """ Perform the streaming step: Move the distribution functions to neighboring nodes. """
        for i, j, k in self.rho:
            for l in range(19):  # 19 directions for D3Q19
                vx, vy, vz = self.velocities[l]
                
                # Ensure that indices are integers
                new_i = int(i + vx) % self.n  # Cast to integer
                new_j = int(j + vy) % self.n  # Cast to integer
                new_k = int(k + vz) % self.n  # Cast to integer
                
                # Move the distribution function to the new indices
                self.f[new_i, new_j, new_k, l] = self.f[i, j, k, l]

    @ti.kernel
    def compute_macroscopic(self):
        """ Compute macroscopic quantities such as density (rho) and velocity (u) from the distribution functions. """
        for i, j, k in self.rho:
            rho_val = 0.0
            velocity = ti.Vector([0.0, 0.0, 0.0])
            for l in range(19):  # 19 directions for D3Q19
                vx, vy, vz = self.velocities[l]
                rho_val += self.f[i, j, k, l]
                velocity += self.f[i, j, k, l] * ti.Vector([vx, vy, vz])
            
            self.rho[i, j, k] = rho_val
            
            # Correctly assign the velocity components to the 4D field `self.u`
            self.u[i, j, k, 0] = velocity[0] / rho_val  # x-component of velocity
            self.u[i, j, k, 1] = velocity[1] / rho_val  # y-component of velocity
            self.u[i, j, k, 2] = velocity[2] / rho_val  # z-component of velocity

    def update(self):
        """ Run one iteration of the LBM (collision, streaming, and macroscopic computation). """
        self.collide()
        self.stream()
        self.compute_macroscopic()


# Usage
#grid_size = 64  # Example grid size for 3D simulation
#tau = 1.0  # Relaxation time for viscosity

#lbm = LBM(grid_size, tau)

# Main simulation loop
#for _ in range(1000):  # Run for 1000 iterations
#    lbm.update()

    # Optionally, you can access the macroscopic variables like:
    # lbm.rho  # Density
    # lbm.u    # Velocity
