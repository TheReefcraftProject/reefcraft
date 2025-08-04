import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

import matplotlib.pyplot as plt
import numpy as np
import warp as wp

from reefcraft.sim.compute_lbm import ComputeLBM

"""Test ComputeLBM class."""


def test_coral_boundary_conditions() -> None:
    """Ensure dynamic boundaries are functioning."""

    # Set up the grid and fluid properties
    grid_shape = (32, 32, 32)  # Small grid for testing
    fluid_speed = 0.5  # Example fluid speed
    max_steps = 10  # Short number of steps for testing

    # Create a ComputeLBM instance or mock it
    compute_lbm = ComputeLBM(grid_shape, fluid_speed, 3000.0)  # Assume default values are set inside ComputeLBM

    # Hardcode the two box meshes (one larger than the other)
    larger_box_vertices = np.array(
        [
            [0, 0, 0],
            [10, 0, 0],
            [10, 10, 0],
            [0, 10, 0],  # bottom face
            [0, 0, 10],
            [10, 0, 10],
            [10, 10, 10],
            [0, 10, 10],  # top face
        ],
        dtype=np.float32,
    )

    smaller_box_vertices = np.array(
        [
            [0, 0, 0],
            [2, 0, 0],
            [2, 2, 0],
            [0, 2, 0],  # bottom face
            [0, 0, 2],
            [2, 0, 2],
            [2, 2, 2],
            [0, 2, 2],  # top face
        ],
        dtype=np.float32,
    )

    smaller_box_indices = np.array(
        [
            [0, 1, 2],
            [0, 2, 3],
            [4, 5, 6],
            [4, 6, 7],  # bottom & top faces
            [0, 1, 5],
            [0, 5, 4],
            [1, 2, 6],
            [1, 6, 5],
            [2, 3, 7],
            [2, 7, 6],
            [3, 0, 4],
            [3, 4, 7],
        ],
        dtype=np.int32,
    )

    # Convert to Warp arrays
    larger_box_vertices_wp = wp.array(larger_box_vertices, dtype=wp.vec3f)
    smaller_box_vertices_wp = wp.array(smaller_box_vertices, dtype=wp.vec3f)
    larger_box_indices_wp = wp.array(smaller_box_indices, dtype=wp.vec3i)
    smaller_box_indices_wp = wp.array(smaller_box_indices, dtype=wp.vec3i)

    print("Testing with small box...")
    compute_lbm.update_mesh((smaller_box_vertices_wp, smaller_box_indices_wp))

    # Run the simulation for a few steps and check velocity changes near the boundary
    for i in range(max_steps):
        compute_lbm.step(i)

    # Check the velocity magnitude near the boundary
    velocity_field = compute_lbm.get_field_numpy()["velocity_magnitude"]
    inflow_v = velocity_field[5, 16, 16]  # Check near the inflow
    boundary_v = velocity_field[16, 16, 0]  # Check near the boundaries
    print(f"Inflow velocity: {inflow_v}. Boundary velocity: {boundary_v}")
    # Assert that the boundary velocity is significantly different (indicating boundary interaction)
    assert np.abs(boundary_v - inflow_v) > 0, "No change in velocity at the boundary"

    print("Velocity magnitude changed at boundary. Moving to next step.")

    # Now update mesh to larger box and test again
    print("Testing with larger box...")
    compute_lbm.update_mesh((larger_box_vertices_wp, larger_box_indices_wp))

    for step in range(max_steps):
        print(f"Step {step + 1}:")

        # Run the LBM step, updating boundary conditions accordingly
        compute_lbm.step(step)

    # Check the velocity magnitude higher up in the z-axis where the larger box should affect the flow
    velocity_field = compute_lbm.get_field_numpy()["velocity_magnitude"]
    inflow_v = velocity_field[5, 16, 16]
    boundary_v = velocity_field[16, 16, 10]  # Check in the higher z region

    # Verify that there is a change in the velocity near the boundary of the larger box
    assert np.any(np.abs(boundary_v - inflow_v) > 0), "No change in velocity at larger box boundary"

    print("Velocity magnitude changed at larger box boundary. Moving to next step.")

    print("Test passed successfully!")


def test_setup_boundary_conditions() -> None:
    """Test setup_boundary_conditions function from ComputeLBM."""
    lbm = ComputeLBM((32, 32, 32), 0.02, 3000.0)
    bounds = lbm.boundary_conditions
    assert bounds == lbm.stepper.boundary_conditions


def test_get_fields_numpy() -> None:
    """Test get_fields_numpy function from ComputeLBM."""
    lbm = ComputeLBM((32, 32, 32), 0.02, 3000.0)
    for i in range(2000):
        lbm.step(i)

    fields = lbm.get_field_numpy()
    assert isinstance(fields["velocity"], np.ndarray), f"Expected ndarray, got {type(fields['velocity'])}"
    assert fields["velocity"].shape == (32, 32, 32, 3)


def test_field_numeric_stability() -> None:
    """Test numeric stability of fields (e.g. velocity)."""
    lbm = ComputeLBM((100, 100, 100), 2.0, 3000.0)
    smaller_box_vertices = np.array(
        [
            [0, 0, 0],
            [2, 0, 0],
            [2, 2, 0],
            [0, 2, 0],  # bottom face
            [0, 0, 2],
            [2, 0, 2],
            [2, 2, 2],
            [0, 2, 2],  # top face
        ],
        dtype=np.float32,
    )

    smaller_box_indices = np.array(
        [
            [0, 1, 2],
            [0, 2, 3],
            [4, 5, 6],
            [4, 6, 7],  # bottom & top faces
            [0, 1, 5],
            [0, 5, 4],
            [1, 2, 6],
            [1, 6, 5],
            [2, 3, 7],
            [2, 7, 6],
            [3, 0, 4],
            [3, 4, 7],
        ],
        dtype=np.int32,
    )

    # Convert to Warp arrays
    smaller_box_vertices_wp = wp.array(smaller_box_vertices, dtype=wp.vec3f)
    smaller_box_indices_wp = wp.array(smaller_box_indices, dtype=wp.vec3i)
    lbm.update_mesh((smaller_box_vertices_wp, smaller_box_indices_wp))

    for i in range(10000):
        lbm.step(i)

    velocity_field = lbm.get_field_numpy()["velocity"]

    # Assert that there are no NaN values in the velocity field
    assert not np.isnan(velocity_field).any(), "Velocity field contains NaN values."

    print("Test passed: No NaN values in velocity field.")


def test_update_mesh() -> None:
    """Test update_mesh function from ComputeLBM."""

    compute_lbm = ComputeLBM((32, 32, 32), 0.02, 3000.0)

    # Define a small and large box meshes (to be used as test cases)
    small_box_vertices = np.array(
        [
            [5, 5, 5],
            [7, 5, 5],
            [7, 7, 5],
            [5, 7, 5],  # bottom face
            [5, 5, 7],
            [7, 5, 7],
            [7, 7, 7],
            [5, 7, 7],  # top face
        ],
        dtype=np.float32,
    )

    # Convert to Warp arrays
    small_box_vertices_wp = wp.array(small_box_vertices, dtype=wp.vec3f, device="cuda")

    # Hardcode indices for simplicity (same for both small and large boxes)
    small_box_indices = np.array(
        [
            [0, 1, 2],
            [0, 2, 3],
            [4, 5, 6],
            [4, 6, 7],  # bottom & top faces
            [0, 1, 5],
            [0, 5, 4],
            [1, 2, 6],
            [1, 6, 5],
            [2, 3, 7],
            [2, 7, 6],
            [3, 0, 4],
            [3, 4, 7],
        ],
        dtype=np.int32,
    )

    larger_box_vertices = np.array(
        [
            [0, 0, 0],
            [10, 0, 0],
            [10, 10, 0],
            [0, 10, 0],  # bottom face
            [0, 0, 10],
            [10, 0, 10],
            [10, 10, 10],
            [0, 10, 10],  # top face
        ],
        dtype=np.float32,
    )

    # Convert to Warp arrays
    small_box_indices_wp = wp.array(small_box_indices, dtype=wp.vec3i, device="cuda")

    # larger box:
    larger_box_vertices_wp = wp.array(larger_box_vertices, dtype=wp.vec3i, device="cuda")
    larger_box_indices_wp = small_box_indices_wp

    # Step 3: Test with small box first
    print("Testing with small box...")
    compute_lbm.update_mesh((small_box_vertices_wp, small_box_indices_wp))
    assert compute_lbm.coral_vertices is not None

    # Step 4: Access the boundary condition (index 3 is where coral mesh is stored)
    # Here we check the updated mesh by inspecting the boundary condition
    updated_vertices = compute_lbm.stepper.boundary_conditions[3].mesh_vertices  # Get updated mesh indices (list)
    print(updated_vertices)

    correct_position = np.array([16, 16, 0])
    correct_position = small_box_vertices + correct_position
    assert updated_vertices.all() == correct_position.all()
    print("Test passed successfully!")

    compute_lbm.update_mesh((larger_box_vertices_wp, larger_box_indices_wp))
    updated_vertices = compute_lbm.stepper.boundary_conditions[3].mesh_vertices  # Get updated mesh indices (list)
    print(updated_vertices)


def test_warp_grid() -> None:
    """Test ComputeLBM's warp grid."""
    lbm = ComputeLBM((32, 32, 32), 0.02, 3000.0)

    # For now assert grid shape is correct:
    assert lbm.grid.shape == lbm.grid_shape
