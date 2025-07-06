from pathlib import Path

import numpy as np
import taichi as ti

# Initialize Taichi on CPU for deterministic behavior
# Calling ti.init multiple times is safe
if not getattr(ti, "_initialized", False):
    from contextlib import suppress

    with suppress(Exception):
        ti.init(arch=ti.cpu)

import sys

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

import importlib


def reload_volume():  # noqa: ANN201
    from reefcraft import sim

    return importlib.reload(sim.volume).Volume


def test_fill_test_pattern_values() -> None:
    Volume = reload_volume()
    vol = Volume(active_region=2)
    assert vol.data.shape == (2, 2, 2)
    assert vol.coords.shape == (8,)
    assert vol.colors.shape == (8,)

    assert np.allclose(vol.data[0, 0, 0], [1.0, 1.0, 1.0])
    idx = 1 * vol.active * vol.active + 0 * vol.active + 1
    expected_coord = np.array([1, 0, 1]) / vol.resolution
    assert np.allclose(vol.coords[idx], expected_coord)
    expected_color = np.array([1, 0, 1]) / vol.active
    assert np.allclose(vol.colors[idx], expected_color)
