import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

import matplotlib.pyplot as plt
import numpy as np
import warp as wp

from reefcraft.sim.simple_porag import SimpleP

"""Test SimpleP class."""


def test_update_mesh() -> None:
    """Test the update_mesh function from SimpleP to ensure the mesh is updated correctly."""

    simple_p = SimpleP()

    # Define new mesh vertices and indices (as an example)
    new_vertices = np.array([[1.0, 1.0, 0.0], [2.0, 2.0, 0.0], [3.0, 3.0, 0.0]], dtype=np.float32)
    new_indices = np.array([[0, 1, 2]], dtype=np.int32)  # Simple triangle face

    # Update the mesh
    simple_p.update_mesh({"vertices": wp.array(new_vertices, dtype=wp.vec3f), "indices": wp.array(new_indices, dtype=wp.vec3i)})

    # Check if mesh is updated (check the first vertex)
    updated_vertices = simple_p.mesh["vertices"].numpy()
    assert np.array_equal(updated_vertices[0], new_vertices[0]), f"Mesh update failed, first vertex: {updated_vertices[0]}"

    # Check if indices are updated
    updated_indices = simple_p.mesh["indices"].numpy()
    assert np.array_equal(updated_indices[0], new_indices[0]), f"Mesh indices update failed, first index: {updated_indices[0]}"

    print("Mesh update test passed.")


def test_growth_step() -> None:
    """Test that polyps are updated correctly in each growth step."""

    simple_p = SimpleP()

    # Get initial position of a polyp (let's pick the first polyp)
    initial_position = simple_p.mesh["vertices"].numpy()[0]

    # Perform a growth step
    simple_p.growth_step()

    # Get the new position of the same polyp
    new_position = simple_p.mesh["vertices"].numpy()[0]

    # Assert that the position has changed
    assert not np.array_equal(initial_position, new_position), "Polyp position did not change after growth step."

    print("Growth step test passed.")


def test_add_polyp() -> None:
    """Test that the add_polyp function adds a new polyp when space is available."""

    simple_p = SimpleP()

    # Current number of polyps
    initial_num_polyps = len(simple_p.mesh["vertices"])

    # Add a new polyp at a position where there is space
    new_polyp_position = (0.5, 0.5, 0.5)
    simple_p.add_polyp(new_polyp_position)

    # Check if the number of polyps has increased
    new_num_polyps = len(simple_p.mesh["vertices"])
    assert new_num_polyps == initial_num_polyps + 1, f"Expected {initial_num_polyps + 1} polyps, found {new_num_polyps}"

    print("Add polyp test passed.")
