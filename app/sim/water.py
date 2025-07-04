# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# 
import taichi as ti
import numpy as np

# Initialize Taichi environment
ti.init(arch=ti.gpu)

# Grid size
n = 128
# 3D field for velocity
velocity = ti.Vector.field(3, dtype=ti.f32, shape=(n, n, n))

# Calculate the magnitude of the velocity at each voxel
velocity_magnitude = ti.field(dtype=ti.f32, shape=(n, n, n))

@ti.kernel
def advect():
    # Loop over the 3D grid (velocity field)
    for i, j, k in velocity:
        # Simplified advection (just a placeholder for now)
        velocity[i, j, k] = velocity[i, j, k]  # This is a placeholder for now

@ti.kernel
def apply_force(dt: float):
    # Loop over the 3D grid (velocity field)
    for i, j, k in velocity:
        # Apply gravity force (or other forces)
        velocity[i, j, k] += ti.Vector([0.0, -9.8, 0.0]) * dt  # Gravity force

@ti.kernel
def apply_inflow(inflow_speed: float):
    # Loop over the 3D grid (velocity field) and apply inflow to the left side
    for i, j, k in velocity:
        if i == 0:  # Set inflow at the left side of the tank
            velocity[i, j, k] = ti.Vector([inflow_speed, 0.0, 0.0])

@ti.kernel
def apply_outflow():
    # Loop over the 3D grid (velocity field) and apply outflow to the right side
    for i, j, k in velocity:
        if i == n - 1:  # Set outflow at the right side of the tank
            velocity[i, j, k] = ti.Vector([0.0, 0.0, 0.0])

@ti.kernel
def compute_velocity_magnitude():
    # Compute the magnitude of velocity at each voxel
    for i, j, k in velocity:
        velocity_magnitude[i, j, k] = velocity[i, j, k].norm()

# Create a window and scene for visualization using ti.ui.Scene
window = ti.ui.Window("Fluid Simulation", (640, 640))
scene = window.get_scene()

# Time step and simulation parameters
dt = 0.1  # Time step
inflow_speed = 1.0  # Speed of inflow

# Grid rendering using small cubes to represent each voxel
# These will be visualized in the scene based on velocity magnitude
voxel_size = 0.05  # Size of the small cubes representing each grid point

while window.running:
    # Update simulation
    apply_force(dt)
    advect()
    apply_inflow(inflow_speed)
    apply_outflow()

    # Visualize fluid's velocity field (using the magnitude of velocity)
    compute_velocity_magnitude()

    # Convert velocity magnitude to a 2D numpy array
    img = velocity_magnitude.to_numpy()

    # Loop through the grid and add small cubes based on velocity magnitude
    for i in range(n):
        for j in range(n):
            for k in range(n):
                # Only add a cube if the velocity magnitude is greater than a threshold
                if velocity_magnitude[i, j, k] > 0.1:  # You can adjust this threshold
                    position = ti.Vector([i * voxel_size, j * voxel_size, k * voxel_size])
                    #scene.add_box(position=position, size=ti.Vector([voxel_size, voxel_size, voxel_size]), color=(1, 0, 0))  # Red color

    # Display the scene in the window
    window.show()



