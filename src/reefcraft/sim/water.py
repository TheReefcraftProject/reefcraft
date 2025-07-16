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
from reefcraft.sim.reef_space import ReefSpace
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


# ---- Example of ReefSpace stepping through simulation ---- #
#---------------------------------------------------------------#

space = ReefSpace()
for i in range(5):
    space.step()
    v_field = space.get_fields_numpy().get("velocity")
    visualize_velocity_field(v_field)