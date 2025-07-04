# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------
import taichi as ti
import numpy as np

# Initialize Taichi
ti.init(arch=ti.gpu)

class LatticeBoltzmann3D:
    def __init__(self, grid_size, tau):
        self.n = grid_size  # Grid size (n x n x n)
        self.tau = tau  # Relaxation time
        # D3Q19 model velocity directions (19 directions in 3D)
        self.velocities = [
            (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1),  # 6 face directions
            (1, 1, 0), (-1, 1, 0), (1, -1, 0), (-1, -1, 0), (1, 0, 1), (-1, 0, 1),  # 6 edge directions
            (1, 0, -1), (-1, 0, -1), (0, 1, 1), (0, -1, 1), (0, 1, -1), (0, -1, -1)  # 6 diagonal directions
        ]
        
        # Fields for velocity and distribution functions
        self.f = ti.field(dtype=ti.f32, shape=(self.n, self.n, self.n, len(self.velocities)))  # Distribution function
        self.feq = ti.field(dtype=ti.f32, shape=(self.n, self.n, self.n, len(self.velocities)))  # Equilibrium distribution
        self.rho = ti.field(dtype=ti.f32, shape=(self.n, self.n, self.n))  # Density field
        self.u = ti.field(dtype=ti.f32, shape=(self.n, self.n, self.n, 3))  # Velocity field (3D)

    def equilibrium(self, rho, u):
        """ Compute the equilibrium distribution function f_eq based on the density and velocity fields. """
        for i, j, k in self.rho:
            cu = ti.Vector([0.0, 0.0, 0.0])
            for v in self.velocities:
                cu += u[i, j, k].dot(ti.Vector(v))
            feq = self.compute_feq(rho[i, j, k], cu)
            self.feq[i, j, k] = feq  # Store equilibrium function in feq field
    
    @ti.kernel
    def compute_feq(self, rho: float, cu: ti.Vector) -> ti.Vector:
        """ Compute the equilibrium distribution function f_eq for the D3Q19 lattice model. """
        w = [1/3, 1/3, 1/3]  # For D3Q19 model, weights are adjusted here
        # The equilibrium distribution function formula:
        # Use the appropriate weights and compute the equilibrium
        feq = ti.Vector([0.0] * len(self.velocities))
        # Simplified example: you should adapt it for your real model
        return feq

    @ti.kernel
    def collide(self):
        """ Perform the BGK collision step: Relaxation of distribution functions to equilibrium. """
        for i, j, k in self.rho:
            for l in range(len(self.velocities)):
                self.f[i, j, k, l] = self.f[i, j, k, l] - (self.f[i, j, k, l] - self.feq[i, j, k, l]) / self.tau

    @ti.kernel
    def stream(self):
        """ Perform the streaming step: Move the distribution functions to neighboring nodes. """
        for i, j, k in self.rho:
            for l, (vx, vy, vz) in enumerate(self.velocities):
                new_i, new_j, new_k = (i + vx) % self.n, (j + vy) % self.n, (k + vz) % self.n
                self.f[new_i, new_j, new_k, l] = self.f[i, j, k, l]

    @ti.kernel
    def compute_macroscopic(self):
        """ Compute macroscopic quantities such as density (rho) and velocity (u) from the distribution functions. """
        for i, j, k in self.rho:
            rho_val = 0.0
            velocity = ti.Vector([0.0, 0.0, 0.0])
            for l, (vx, vy, vz) in enumerate(self.velocities):
                rho_val += self.f[i, j, k, l]
                velocity += self.f[i, j, k, l] * ti.Vector([vx, vy, vz])
            self.rho[i, j, k] = rho_val
            self.u[i, j, k] = velocity / rho_val  # Normalize by density to get velocity

    def update(self):
        """ Run one iteration of the LBM (collision, streaming, and macroscopic computation). """
        self.collide()
        self.stream()
        self.compute_macroscopic()

# Usage
grid_size = 64  # Example grid size for 3D simulation
tau = 1.0  # Relaxation time for viscosity

lbm = LatticeBoltzmann3D(grid_size, tau)

# Main simulation loop
for _ in range(1000):  # Run for 1000 iterations
    lbm.update()

    # Optionally, you can access the macroscopic variables like:
    # lbm.rho  # Density
    # lbm.u    # Velocity
