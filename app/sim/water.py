# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------
"""
Here we use the ComputeLBM class to run the water simulation.

IDEA/GOAL: Have this return specified fields (e.g. Density, Velocity) 
in specified formats (numpy, jnp, warp) at specified points in loop to be used in reefcraft.
"""
# Import LBM 
from compute_lbm import ComputeLBM

# Simulation parameters
grid_shape = (128, 128, 128)  # Grid size
num_steps = 1000              # Total number of simulation steps
fluid_speed = 0.02           # Fluid speed (m/s)
stl_filename = "app/resources/stl/coral.stl"  # Path to the coral mesh (for boundary conditions)
post_process_interval = 100  # Interval for post-processing (e.g., saving VTK or images)

# Create an instance of LatticeBoltzmannMethod
lbm_sim = ComputeLBM(
    grid_shape=grid_shape,
    num_steps=num_steps,
    fluid_speed=fluid_speed,
    stl_filename=stl_filename,
    post_process_interval=post_process_interval
)

# Run Simulation - No visual
#lbm_sim.run()

# Run the simulation with save vtk
lbm_sim.run_vtk()


