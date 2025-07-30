import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

import numpy as np

from reefcraft.sim.compute_lbm import ComputeLBM

"""Test ComputeLBM class."""


def test_setup_boundary_conditions() -> None:
    """Test setup_boundary_conditions function from ComputeLBM."""
    lbm = ComputeLBM(0.02, 3000.0, (32, 32, 32))
    bounds = lbm.boundary_conditions
    assert bounds == lbm.stepper.boundary_conditions


def test_coral_boundary_conditions() -> None:
    """Ensure dynamic boundaries are functioning."""
    pass


def test_get_fields_numpy() -> None:
    """Test get_fields_numpy function from ComputeLBM."""
    lbm = ComputeLBM(0.02, 3000.0, (32, 32, 32))
    for i in range(2000):
        lbm.step(i)

    fields = lbm.get_field_numpy()
    assert isinstance(fields["velocity"], ndarray), f"Expected ndarray, got {type(fields['velocity'])}"


def test_field_numeric_stability() -> None:
    """Test numeric stability of fields (e.g. velocity)."""
    lbm = ComputeLBM(0.02, 3000.0, (32, 32, 32))
    lbm_highRe = ComputeLBM(0.02, 5000.0, (32, 32, 32))
    lbm_highV = ComputeLBM(2.0, 3000.0, (32, 32, 32))


def test_update_mesh() -> None:
    """Test update_mesh function from ComputeLBM."""
    pass


def test_warp_grid() -> None:
    """Test ComputeLBM's warp grid."""
    pass