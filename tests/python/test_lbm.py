import importlib.util
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

import matplotlib.pyplot as plt
import numpy as np
import warp as wp

# Import ComputeLBM directly to avoid running package-level side effects
spec = importlib.util.spec_from_file_location("compute_lbm", Path(__file__).resolve().parents[2] / "src" / "reefcraft" / "sim" / "compute_lbm.py")
compute_lbm_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compute_lbm_module)
ComputeLBM = compute_lbm_module.ComputeLBM

"""Test ComputeLBM class."""

# Reusable cube meshes for tests
SMALL_CUBE_VERTICES = np.array(
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

LARGE_CUBE_VERTICES = np.array(
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

CUBE_INDICES = np.array(
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


def test_coral_boundary_conditions() -> None:
    """Ensure dynamic boundaries are functioning."""

    # Set up the grid and fluid properties
    grid_shape = (32, 32, 32)  # Small grid for testing
    fluid_speed = 0.5  # Example fluid speed
    max_steps = 100  # Short number of steps for testing

    # Create a ComputeLBM instance and initialize with the small cube mesh
    compute_lbm = ComputeLBM(grid_shape, fluid_speed, 3000.0)
    small_vertices_wp = wp.array(SMALL_CUBE_VERTICES, dtype=wp.vec3f)
    large_vertices_wp = wp.array(LARGE_CUBE_VERTICES, dtype=wp.vec3f)
    indices_wp = wp.array(CUBE_INDICES, dtype=wp.vec3i)
    compute_lbm.set_mesh((small_vertices_wp, indices_wp))

    print("Testing with small box...")

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
    compute_lbm.update_mesh((large_vertices_wp, indices_wp))

    for step in range(max_steps):
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


def test_coral_boundary_conditions_with_wall() -> None:
    """Ensure dynamic boundaries are functioning with a wall in the middle."""

    # Set up the grid and fluid properties
    grid_shape = (32, 32, 32)  # Small grid for testing
    fluid_speed = 0.5  # Example fluid speed
    max_steps = 100  # Short number of steps for testing

    # Create a ComputeLBM instance and initialize with the small cube mesh
    compute_lbm = ComputeLBM(grid_shape, fluid_speed, 3000.0)
    small_vertices_wp = wp.array(SMALL_CUBE_VERTICES, dtype=wp.vec3f)
    indices_wp = wp.array(CUBE_INDICES, dtype=wp.vec3i)
    compute_lbm.set_mesh((small_vertices_wp, indices_wp))

    # Define the wall in the middle of the grid along the plane of zy at x = grid_size[0] / 2
    wall_x = grid_shape[0] // 2  # Wall at x = 16 for a grid of size 32
    wall_vertices = np.array(
        [
            [wall_x, 0, 0],
            [wall_x, 0, grid_shape[2] - 1],
            [wall_x, grid_shape[1] - 1, 0],
            [wall_x, grid_shape[1] - 1, grid_shape[2] - 1],
        ],
        dtype=np.float32,
    )

    # Define the indices for the wall spanning the zy-plane
    wall_indices = np.array(
        [
            [0, 1, 2],
            [1, 3, 2],
            [2, 3, 1],  # Wall faces connecting vertices
        ],
        dtype=np.int32,
    )

    # Convert to Warp arrays
    wall_vertices_wp = wp.array(wall_vertices, dtype=wp.vec3f)
    wall_indices_wp = wp.array(wall_indices, dtype=wp.vec3i)

    # Test with the wall in the middle of the grid
    print("Testing with wall at x = grid_size[0] // 2...")

    compute_lbm.update_mesh((wall_vertices_wp, wall_indices_wp))
    print(compute_lbm.stepper.boundary_conditions[0].indices)

    # Run the simulation for a few steps and check velocity changes near the boundary (the wall)
    for i in range(max_steps):
        compute_lbm.step(i)

    # Check the velocity magnitude near the boundary (the wall)
    velocity_field = compute_lbm.get_field_numpy()["velocity_magnitude"]
    inflow_v = velocity_field[5, 16, 16]  # Check near the inflow
    boundary_v = velocity_field[18, 16, 16]  # Check near the wall at x = wall_x
    print(f"Inflow velocity: {inflow_v}. Boundary velocity at wall: {boundary_v}")
    # Assert that the boundary velocity is significantly different (indicating boundary interaction)
    assert np.abs(boundary_v - inflow_v) > 0, "No change in velocity at the boundary"

    print("Velocity magnitude changed at the wall boundary. Moving to next step.")

    print("Test passed successfully!")


def test_setup_boundary_conditions() -> None:
    """Test setup_boundary_conditions function from ComputeLBM."""
    lbm = ComputeLBM((32, 32, 32), 0.02, 3000.0)
    small_vertices_wp = wp.array(SMALL_CUBE_VERTICES, dtype=wp.vec3f)
    indices_wp = wp.array(CUBE_INDICES, dtype=wp.vec3i)
    lbm.set_mesh((small_vertices_wp, indices_wp))
    bounds = lbm.boundary_conditions
    assert bounds == lbm.stepper.boundary_conditions


def test_get_fields_numpy() -> None:
    """Test get_fields_numpy function from ComputeLBM."""
    lbm = ComputeLBM((32, 32, 32), 0.02, 3000.0)
    small_vertices_wp = wp.array(SMALL_CUBE_VERTICES, dtype=wp.vec3f)
    indices_wp = wp.array(CUBE_INDICES, dtype=wp.vec3i)
    lbm.set_mesh((small_vertices_wp, indices_wp))
    for i in range(2000):
        lbm.step(i)

    fields = lbm.get_field_numpy()
    assert isinstance(fields["velocity"], np.ndarray), f"Expected ndarray, got {type(fields['velocity'])}"
    assert fields["velocity"].shape == (32, 32, 32, 3)


def test_field_numeric_stability() -> None:
    """Test numeric stability of fields (e.g. velocity)."""
    lbm = ComputeLBM((100, 100, 100), 2.0, 4000.0)
    small_vertices_wp = wp.array(SMALL_CUBE_VERTICES, dtype=wp.vec3f)
    indices_wp = wp.array(CUBE_INDICES, dtype=wp.vec3i)
    lbm.set_mesh((small_vertices_wp, indices_wp))

    for i in range(100000):
        lbm.step(i)

    velocity_field = lbm.get_field_numpy()["velocity"]

    # Assert that there are no NaN values in the velocity field
    assert not np.isnan(velocity_field).any(), "Velocity field contains NaN values."

    print("Test passed: No NaN values in velocity field.")


def test_update_mesh() -> None:
    """Test update_mesh function from ComputeLBM."""
    compute_lbm = ComputeLBM((32, 32, 32), 0.02, 3000.0)

    # Convert reusable cube meshes to Warp arrays
    small_vertices_wp = wp.array(SMALL_CUBE_VERTICES, dtype=wp.vec3f)
    large_vertices_wp = wp.array(LARGE_CUBE_VERTICES, dtype=wp.vec3f)
    indices_wp = wp.array(CUBE_INDICES, dtype=wp.vec3i)

    # Step 3: Test with small box first
    compute_lbm.set_mesh((small_vertices_wp, indices_wp))
    assert compute_lbm.coral_vertices is not None

    # Step 4: Verify the initial mesh was set correctly
    updated_vertices = compute_lbm.coral_vertices
    print(updated_vertices)

    correct_position = SMALL_CUBE_VERTICES + np.array([16, 16, 0])
    assert np.all(updated_vertices == correct_position)
    print("Test passed successfully!")

    compute_lbm.update_mesh((large_vertices_wp, indices_wp))
    updated_vertices = compute_lbm.coral_vertices
    print(updated_vertices)


def test_warp_grid() -> None:
    """Test ComputeLBM's warp grid."""
    lbm = ComputeLBM((32, 32, 32), 0.02, 3000.0)
    small_vertices_wp = wp.array(SMALL_CUBE_VERTICES, dtype=wp.vec3f)
    indices_wp = wp.array(CUBE_INDICES, dtype=wp.vec3i)
    lbm.set_mesh((small_vertices_wp, indices_wp))

    # For now assert grid shape is correct:
    assert lbm.grid.shape == lbm.grid_shape
