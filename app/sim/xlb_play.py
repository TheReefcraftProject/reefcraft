import xlb
import warp as wp
import numpy as np
import time
import matplotlib.pyplot as plt
from xlb.compute_backend import ComputeBackend
from xlb.precision_policy import PrecisionPolicy
from xlb.grid import grid_factory
from xlb.operator.stepper import IncompressibleNavierStokesStepper
from xlb.operator.boundary_condition import RegularizedBC, ExtrapolationOutflowBC, FullwayBounceBackBC
import xlb.velocity_set
import jax.numpy as jnp
from xlb.operator.macroscopic import Macroscopic

# -------------------------- Simulation Setup --------------------------

# Grid parameters
grid_size_x, grid_size_y, grid_size_z = 128, 128, 128
grid_shape = (grid_size_x, grid_size_y, grid_size_z)

# Simulation Configuration
compute_backend = ComputeBackend.WARP
precision_policy = PrecisionPolicy.FP32FP32

velocity_set = xlb.velocity_set.D3Q27(precision_policy=precision_policy, backend=compute_backend)
wind_speed = 0.02
num_steps = 1000
print_interval = 100
post_process_interval = 100

# Physical Parameters
Re = 50000.0
clength = grid_size_x - 1
visc = wind_speed * clength / Re
omega = 1.0 / (3.0 * visc + 0.5)

# Initialize XLB
xlb.init(
    velocity_set=velocity_set,
    default_backend=compute_backend,
    default_precision_policy=precision_policy,
)

# Create Grid
grid = grid_factory(grid_shape, compute_backend=compute_backend)

# Bounding box indices
box = grid.bounding_box_indices()
box_no_edge = grid.bounding_box_indices(remove_edges=True)
inlet = box_no_edge["left"]
outlet = box_no_edge["right"]
walls = [box["bottom"][i] + box["top"][i] + box["front"][i] + box["back"][i] for i in range(velocity_set.d)]
walls = np.unique(np.array(walls), axis=-1).tolist()

# Boundary conditions
bc_left = RegularizedBC("velocity", prescribed_value=(wind_speed, 0.0, 0.0), indices=inlet)
bc_walls = FullwayBounceBackBC(indices=walls)
bc_do_nothing = ExtrapolationOutflowBC(indices=outlet)

boundary_conditions = [bc_walls, bc_left, bc_do_nothing]

# Setup Stepper
stepper = IncompressibleNavierStokesStepper(
    omega=omega,
    grid=grid,
    boundary_conditions=boundary_conditions,
    collision_type="KBC",
)

# Prepare Fields
f_0, f_1, bc_mask, missing_mask = stepper.prepare_fields()

# Setup Macroscopic operator
macro = Macroscopic(
    compute_backend=ComputeBackend.WARP,
    precision_policy=precision_policy,
    velocity_set=velocity_set,
)

# -------------------------- Helper Function --------------------------

def visualize_flow(u, step, grid_shape):
    """
    Visualize the flow by plotting the velocity magnitude in the x-y plane.
    """
    # Take the magnitude of the velocity vector at each point in the grid
    u_magnitude = jnp.sqrt(u[0]**2 + u[1]**2 + u[2]**2)

    # Plot the flow as a 2D slice at the middle of the z-axis
    mid_z = grid_shape[2] // 2
    plt.imshow(u_magnitude[:, :, mid_z], cmap='viridis', origin='lower')
    plt.colorbar(label="Velocity Magnitude")
    plt.title(f"Velocity Magnitude at Step {step}")
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.show()


# -------------------------- Simulation Loop --------------------------

start_time = time.time()
for step in range(num_steps):
    # Call stepper with the correct arguments
    f_0, f_1 = stepper(f_0, f_1, bc_mask, missing_mask, omega, step)

    # Swap the buffers
    f_0, f_1 = f_1, f_0

    # Print progress at intervals
    if step % print_interval == 0:
        elapsed_time = time.time() - start_time
        print(f"Iteration: {step}/{num_steps} | Time elapsed: {elapsed_time:.2f}s")
        start_time = time.time()

    # Post-process at intervals and final step
    if step % post_process_interval == 0 or step == num_steps - 1:
        # Compute macroscopic quantities like velocity and density
        rho, u = macro(f_0)

        # Visualize the flow by plotting a 2D slice of velocity magnitude
        visualize_flow(u, step, grid_shape)

print("Simulation completed successfully.")
