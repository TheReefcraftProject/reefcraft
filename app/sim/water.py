# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------
"""
Here we use the ComputeLBM class to run the water simulation.

IDEA/GOAL: Have this return specified fields (e.g. Density, Velocity) 
in specified formats (numpy, jnp, warp array) at specified points in loop to be used in reefcraft.
"""
# Import LBM 
from compute_lbm import ComputeLBM
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.quiver as quiver
from mpl_toolkits.mplot3d import Axes3D

# --- Function for matplt visual --- #
def visualize_velocity_field(velocity_field):
    """
    Visualize the 3D velocity field using sparse plotting.
    """
    # Extract components
    u = velocity_field[:, :, :, 0]
    v = velocity_field[:, :, :, 1]
    w = velocity_field[:, :, :, 2]

    # Create mesh grid
    x = np.linspace(0, 31, 32)
    y = np.linspace(0, 31, 32)
    z = np.linspace(0, 31, 32)
    X, Y, Z = np.meshgrid(x, y, z)

    # Normalize velocity vectors
    magnitude = np.sqrt(u**2 + v**2 + w**2)
    u /= magnitude
    v /= magnitude
    w /= magnitude

    # Sparse the grid by selecting every other point
    slice_step = 4
    X_sparse = X[::slice_step, ::slice_step, ::slice_step]
    Y_sparse = Y[::slice_step, ::slice_step, ::slice_step]
    Z_sparse = Z[::slice_step, ::slice_step, ::slice_step]
    u_sparse = u[::slice_step, ::slice_step, ::slice_step]
    v_sparse = v[::slice_step, ::slice_step, ::slice_step]
    w_sparse = w[::slice_step, ::slice_step, ::slice_step]

    # Create a figure and axis for 3D plot
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')  # Ensure this is a 3D plot

    # Plot sparse velocity vectors using quiver
    ax.quiver(X_sparse, Y_sparse, Z_sparse, u_sparse, v_sparse, w_sparse, length=1, normalize=True, linewidth=2)

    # Set axis labels
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    #ax.set_zlabel('Z')

    # Set the title
    ax.set_title('3D Sparse Velocity Field Vectors')

    plt.show()


# ---- Set up Parameters and Create Instance of ComputeLBM ---- #
#---------------------------------------------------------------#

# Simulation parameters
grid_shape = (32, 32, 32)  # Grid size
num_steps = 100              # Total number of simulation steps
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

# ---- Examples of running ---- # 

# Run Simulation - No post processing
lbm_sim.run()

# Run the simulation with save vtk
#lbm_sim.run_vtk()

# Example of runing one iteration at a time and returning the numpy velocity field and plotting it
num_iterations = 5

for i in range(num_iterations):
    # Simulate velocity field (replace this with the actual velocity field from your simulation)
    velocity_field = lbm_sim.run_step(i).get("velocity")  # Random 3D velocity field for example

    print(f"Visualizing iteration {i + 1}...")
    visualize_velocity_field(velocity_field)